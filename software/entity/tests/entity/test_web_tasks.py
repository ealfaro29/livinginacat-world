import asyncio
import sqlite3
import time
from types import SimpleNamespace as NS

import pytest
from mcp.server.mcpserver.exceptions import ToolError

from physiclaw.contract.dto import AssistantMessage, ToolCall
from physiclaw.entity.dispatcher import run_next, run_request
from physiclaw.entity.tasks import QueueError, Tasks


def test_upgrade_order_schedule_and_replay(tmp_path):
    path = tmp_path / "tasks.db"
    with sqlite3.connect(path) as db:
        db.execute(
            "CREATE TABLE tasks(id INTEGER PRIMARY KEY,request_id TEXT UNIQUE,title TEXT,state TEXT DEFAULT 'queued',finished_at INTEGER)"
        )
        db.execute("INSERT INTO tasks VALUES(6,'old','Antes','done',14)")
    q = Tasks(path)
    future = int(time.time()) + 3600
    a = q.submit("Mañana", "req_later", future)
    b = q.submit("Ahora", "req_today")
    c = q.submit("Otra", "req_other")
    assert q.submit("Ahora", "req_today") == b
    with pytest.raises(QueueError):
        q.submit("Otro texto", "req_today")
    q.move(c, b, "up")
    q.move(c, b, "up")
    assert [row["id"] for row in Tasks(path).snapshot()["queue"]] == [a, c, b]
    q.remove_waiting(b)
    assert q.claim_due()["id"] == c
    assert q.claim_due() is None
    with pytest.raises(QueueError):
        q.remove_waiting(c)
    with pytest.raises(ToolError):
        asyncio.run(q.finish(c, "done"))
    q.recover()
    assert q.claim_due() is None
    with sqlite3.connect(path) as db:
        assert db.execute(
            "SELECT id,title,state,finished_at FROM tasks WHERE id=6"
        ).fetchone() == (6, "Antes", "done", 14)
        db.execute("UPDATE tasks SET run_at=1 WHERE id=?", (a,))
    assert q.claim_due()["id"] == a


def test_runner_uses_configured_tool_contract_and_lease(tmp_path):
    q = Tasks(tmp_path / "tasks")
    ident = q.submit("Leé la pantalla", "read_only_1")
    rig = NS(ready=False, hardware_ready=True, calibration=NS(precision_verified=True))
    ran = []

    @q.track
    async def peek():
        ran.append("peek")

    class MCP:
        async def list_tools(self):
            return [
                NS(name=name, description="t", input_schema={})
                for name in ("peek", "entity_enqueue")
            ]

        async def call_tool(self, name, arguments):
            await peek()
            return NS(content=[NS(type="text", text="72")], is_error=False)

    class Provider:
        async def chat(self, history, tools):
            assert {t["name"] for t in tools} == {"peek", "finish_task"}
            fn = (
                ToolCall("one", "peek", {})
                if len(history) == 2
                else ToolCall(
                    "two", "finish_task", {"outcome": "done", "summary": "72"}
                )
            )
            return AssistantMessage("", [fn], "tool_use")

        async def aclose(self):
            ran.append("closed")

    async def work(text, mcp):
        return await run_request(text, mcp, Provider)

    async def check():
        assert not await run_next(q, rig, MCP(), work)
        rig.ready = True
        assert await run_next(q, rig, MCP(), work)
        assert not await run_next(q, rig, MCP(), work)

    asyncio.run(check())
    last = q.snapshot(operator=True)["last"]
    assert (last["id"], last["state"], last["result"]) == (ident, "done", "72")
    assert ran == ["peek", "closed"]


def test_clients_cannot_borrow_web_lease(tmp_path):
    q = Tasks(tmp_path / "tasks")
    tid = q.submit("tarea", "web_lease")
    q.claim_due()

    @q.track
    async def tap():
        return "ok"

    async def check():
        with pytest.raises(ToolError):
            await tap()
        with pytest.raises(ToolError):
            await q.start(tid)
        with q.executing_web(tid):
            assert await tap() == "ok"

    asyncio.run(check())
