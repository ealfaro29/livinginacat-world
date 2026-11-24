"""Durable task order shared by MCP clients, the operator app and the MKS display."""

import asyncio
import re
import sqlite3
import time
from contextlib import closing, contextmanager
from contextvars import ContextVar
from functools import wraps
from pathlib import Path

from mcp.server.mcpserver.exceptions import ToolError


class QueueError(ValueError):
    def __init__(self, code, status=400):
        super().__init__(code)
        self.code = code
        self.status = status


NEXT = """SELECT id FROM tasks WHERE state='queued'
          AND (run_at IS NULL OR run_at <= unixepoch()) ORDER BY sort_rank,id LIMIT 1"""
CARD = "id,title,state"
DETAIL = CARD + ",instructions,run_at,finished_at,result"


class Tasks:
    def __init__(self, path: Path):
        self.path = path
        path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        with closing(self._connect()) as db, db:
            db.execute("BEGIN IMMEDIATE")
            db.execute("""CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY, request_id TEXT NOT NULL UNIQUE, title TEXT NOT NULL,
                state TEXT NOT NULL DEFAULT 'queued' CHECK (
                    state IN ('queued','running','done','failed','cancelled','interrupted')
                ), finished_at INTEGER)""")
            db.execute(
                "CREATE UNIQUE INDEX IF NOT EXISTS one_running ON tasks(state) WHERE state='running'"
            )
            columns = {row["name"] for row in db.execute("PRAGMA table_info(tasks)")}
            for name, kind in (
                ("sort_rank", "INTEGER"),
                ("run_at", "INTEGER"),
                ("instructions", "TEXT"),
                ("result", "TEXT"),
            ):
                if name not in columns:
                    db.execute(f"ALTER TABLE tasks ADD COLUMN {name} {kind}")
            db.execute("UPDATE tasks SET sort_rank=id WHERE sort_rank IS NULL")
            db.execute(
                "CREATE INDEX IF NOT EXISTS task_order ON tasks(state,sort_rank,id)"
            )
        path.chmod(0o600)
        self.lock = asyncio.Lock()
        self.action: str | None = None
        self._web_id = ContextVar("entity_web_task", default=None)

    def _connect(self):
        db = sqlite3.connect(self.path, timeout=5)
        db.row_factory = sqlite3.Row
        return db

    def recover(self):
        """Called after the rig server has obtained its exclusive process lock."""
        with closing(self._connect()) as db, db:
            db.execute(
                "UPDATE tasks SET state='interrupted', finished_at=unixepoch() WHERE state='running'"
            )

    def enqueue(self, title: str, request_id: str) -> dict:
        title = " ".join(title.split())
        if not title or len(title) > 120 or not title.isprintable():
            raise ToolError("Use a task title of 1 to 120 printable characters.")
        if request_id.startswith("web:") or not re.fullmatch(
            r"[A-Za-z0-9._:-]{1,96}", request_id
        ):
            raise ToolError(
                "Use a stable MCP request_id of 1 to 96 printable identifier characters."
            )
        with closing(self._connect()) as db, db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute(
                f"SELECT {CARD} FROM tasks WHERE request_id=?", (request_id,)
            ).fetchone()
            if row is not None:
                if row["title"] != title:
                    raise ToolError("That request_id already belongs to another title.")
                return dict(row)
            task_id = self._insert(db, request_id, title)
            return {"id": task_id, "title": title, "state": "queued"}

    @staticmethod
    def _insert(db, request_id, title, instructions=None, run_at=None):
        task_id = db.execute(
            "INSERT INTO tasks(request_id,title,instructions,run_at) VALUES(?,?,?,?)",
            (request_id, title, instructions, run_at),
        ).lastrowid
        db.execute("UPDATE tasks SET sort_rank=? WHERE id=?", (task_id, task_id))
        return task_id

    def submit(self, instructions, key, run_at=None):
        if (
            not isinstance(instructions, str)
            or not 1 <= len(instructions.strip()) <= 2000
        ):
            raise QueueError("invalid_task")
        if not isinstance(key, str) or not re.fullmatch(r"[A-Za-z0-9_-]{8,80}", key):
            raise QueueError("invalid_key")
        if run_at is not None and (
            type(run_at) is not int or not 0 < run_at <= 253402300799
        ):
            raise QueueError("invalid_time")
        instructions = instructions.strip()
        if any(not c.isprintable() and c not in "\t\r\n" for c in instructions):
            raise QueueError("invalid_task")
        with closing(self._connect()) as db, db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute(
                "SELECT id,instructions,run_at FROM tasks WHERE request_id=?",
                ("web:" + key,),
            ).fetchone()
            if row:
                if row["instructions"] != instructions or row["run_at"] != run_at:
                    raise QueueError("request_conflict", 409)
                return row["id"]
            if run_at is not None and run_at <= int(time.time()):
                raise QueueError("past_time")
            return self._insert(
                db,
                "web:" + key,
                " ".join(instructions.split())[:120],
                instructions,
                run_at,
            )

    def move(self, task_id, neighbor, direction):
        if (
            type(task_id) is not int
            or type(neighbor) is not int
            or task_id == neighbor
            or direction not in ("up", "down")
        ):
            raise QueueError("invalid_move")
        with closing(self._connect()) as db, db:
            db.execute("BEGIN IMMEDIATE")
            rows = db.execute(
                "SELECT id,sort_rank FROM tasks WHERE state='queued' ORDER BY sort_rank,id"
            ).fetchall()
            indexes = {row["id"]: idx for idx, row in enumerate(rows)}
            if task_id not in indexes or neighbor not in indexes:
                raise QueueError("queue_changed", 409)
            a, b = indexes[task_id], indexes[neighbor]
            if abs(a - b) != 1:
                raise QueueError("queue_changed", 409)
            if (direction == "up" and a < b) or (direction == "down" and a > b):
                return
            db.executemany(
                "UPDATE tasks SET sort_rank=? WHERE id=?",
                [(rows[b]["sort_rank"], task_id), (rows[a]["sort_rank"], neighbor)],
            )

    def remove_waiting(self, task_id):
        if type(task_id) is not int:
            raise QueueError("invalid_task")
        with closing(self._connect()) as db, db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute(
                "SELECT state FROM tasks WHERE id=?", (task_id,)
            ).fetchone()
            if row and row["state"] == "cancelled":
                return
            if not row or row["state"] != "queued":
                raise QueueError("queue_changed", 409)
            db.execute(
                "UPDATE tasks SET state='cancelled', finished_at=unixepoch() WHERE id=?",
                (task_id,),
            )

    def claim_due(self):
        eligible = f"""SELECT {DETAIL} FROM tasks WHERE instructions IS NOT NULL
                     AND id=({NEXT}) AND NOT EXISTS(SELECT 1 FROM tasks WHERE state='running')"""
        with closing(self._connect()) as db, db:
            if not db.execute(eligible).fetchone():
                return None
            db.execute("BEGIN IMMEDIATE")
            row = db.execute(eligible).fetchone()
            if not row:
                return None
            db.execute("UPDATE tasks SET state='running' WHERE id=?", (row["id"],))
            return dict(row) | {"state": "running"}

    @contextmanager
    def executing_web(self, task_id):
        token = self._web_id.set(task_id)
        try:
            yield
        finally:
            self._web_id.reset(token)

    async def start(self, task_id: int) -> dict:
        async with self.lock:
            with closing(self._connect()) as db, db:
                db.execute("BEGIN IMMEDIATE")
                row = db.execute(
                    f"SELECT {CARD},instructions FROM tasks WHERE id=?", (task_id,)
                ).fetchone()
                if row and row["instructions"] is not None:
                    raise ToolError("The app executes this request.")
                if row and row["state"] == "running":
                    return {k: row[k] for k in ("id", "title", "state")}
                if not row or row["state"] != "queued":
                    raise ToolError("This task is not waiting.")
                if db.execute("SELECT 1 FROM tasks WHERE state='running'").fetchone():
                    raise ToolError("Finish the current task first.")
                next_row = db.execute(NEXT).fetchone()
                if not next_row or next_row["id"] != task_id:
                    raise ToolError("Start the first task in the queue.")
                db.execute("UPDATE tasks SET state='running' WHERE id=?", (task_id,))
                return {"id": task_id, "title": row["title"], "state": "running"}

    async def finish(self, task_id: int, outcome: str, result=None) -> dict:
        if outcome not in {"done", "failed", "cancelled"} and not (
            outcome == "interrupted" and self._web_id.get() == task_id
        ):
            raise ToolError("Use done, failed or cancelled.")
        async with self.lock:
            with closing(self._connect()) as db, db:
                db.execute("BEGIN IMMEDIATE")
                row = db.execute(
                    f"SELECT {CARD},instructions FROM tasks WHERE id=?", (task_id,)
                ).fetchone()
                if not row:
                    raise ToolError("Unknown task.")
                if row["instructions"] is not None and self._web_id.get() != task_id:
                    raise ToolError("The app owns this request.")
                if row["state"] != outcome:
                    if row["state"] != "running" and not (
                        outcome == "cancelled" and row["state"] == "queued"
                    ):
                        raise ToolError(
                            "Only running tasks can finish. Waiting tasks can be cancelled."
                        )
                    db.execute(
                        "UPDATE tasks SET state=?,result=?,finished_at=unixepoch() WHERE id=?",
                        (outcome, result, task_id),
                    )
                return {"id": task_id, "title": row["title"], "state": outcome}

    def snapshot(self, *, operator=False) -> dict:
        fields = DETAIL if operator else CARD + ",run_at"

        def card(row):
            value = dict(row)
            if not operator and value.get("run_at") is None:
                value.pop("run_at", None)
            return value

        with closing(self._connect()) as db:
            db.execute("BEGIN")
            rows = db.execute(
                f"SELECT {fields} FROM tasks WHERE state IN ('queued','running') ORDER BY sort_rank,id"
            ).fetchall()
            last = db.execute(
                f"SELECT {fields} FROM tasks WHERE finished_at IS NOT NULL ORDER BY finished_at DESC,id DESC LIMIT 1"
            ).fetchone()
        return {
            "current": next(
                (card(row) for row in rows if row["state"] == "running"), None
            ),
            "queue": [card(row) for row in rows if row["state"] == "queued"],
            "last": card(last) if last else None,
            "action": self.action,
        }

    def track(self, fn):
        async def execute(task_id, args, kwargs):
            async with self.lock:
                if self._active_id() != task_id:
                    raise ToolError("The task changed before this action could start.")
                self.action = fn.__name__
                try:
                    return await fn(*args, **kwargs)
                finally:
                    self.action = None

        @wraps(fn)
        async def tracked(*args, **kwargs):
            task_id = self._active_id()
            if task_id is None:
                raise ToolError(
                    "Entity is idle. Start an operator-requested task before using the rig."
                )
            if self.lock.locked():
                raise ToolError("Another action is in progress. Wait for it to finish.")
            work = asyncio.create_task(execute(task_id, args, kwargs))
            try:
                return await asyncio.shield(work)
            except asyncio.CancelledError:
                # The hardware call may be in a worker thread after its client disconnects.
                # Keep the rig lock until it returns, and consume its eventual exception.
                work.add_done_callback(
                    lambda task: None if task.cancelled() else task.exception()
                )
                raise

        return tracked

    def is_running_request(self, task_id: int, request_id: str) -> bool:
        with closing(self._connect()) as db:
            return (
                db.execute(
                    "SELECT 1 FROM tasks WHERE id=? AND request_id=? AND state='running'",
                    (task_id, request_id),
                ).fetchone()
                is not None
            )

    def _active_id(self):
        with closing(self._connect()) as db:
            row = db.execute(
                "SELECT id,instructions FROM tasks WHERE state='running'"
            ).fetchone()
        if row and (row["instructions"] is None or self._web_id.get() == row["id"]):
            return row["id"]
        return None
