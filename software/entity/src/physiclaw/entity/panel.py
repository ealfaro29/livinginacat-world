"""Publish Entity state through the MKS's existing, serialized GRBL connection."""

import logging
import re
import threading
import time

log = logging.getLogger(__name__)
REPORT = re.compile(r"\[ENTITY:1,(\d+),(\d+),(\d+),(\d+),(\d+),(\d+)\]")
TOUCH = re.compile(r"\[ENTITY:TOUCH,(\d+),(\d+),(\d+),(\d+),(-?\d+),(-?\d+),(\d+)\]")
VIEWS = ("boot", "idle", "working", "queue", "offline", "setup")


def encoded(text):
    raw = (text or "").encode()
    if len(raw) > 96:
        raw = raw[:93].decode("utf-8", errors="ignore").encode() + "…".encode()
    # The GRBL input layer consumes realtime characters even inside text strings.
    return raw.hex().upper()


def page_content(state, ready, page):
    queue = state["queue"]
    page = min(page, max(0, (len(queue) - 1) // 3))
    current = state["current"] or {}
    rows = tuple(row["title"] for row in queue[3 * page : 3 * page + 3])
    return (
        bool(ready),
        current.get("id", 0),
        current.get("title", ""),
        state["action"],
        len(queue),
        page,
        rows,
    )


def frame_commands(seq, content):
    ready, task_id, title, action, count, page, rows = content
    yield f"$EP=B,{seq},{int(ready)},{task_id},{count},{page}"
    yield f"$EP=T,{encoded(title)}"
    yield f"$EP=A,{encoded(action)}"
    for index, row in enumerate(rows):
        yield f"$EP={index},{encoded(row)}"
    yield f"$EP=E,{seq}"


class MKSPublisher:
    def __init__(self, tasks, rig):
        self.tasks = tasks
        self.rig = rig
        self._stop = threading.Event()
        self._lock = threading.Lock()
        self._thread = None
        self._transport = None
        self._content = None
        self._seq = 0
        self._retry_after = 0.0
        self.report = {"connected": False}

    def start(self):
        if self._thread is None:
            self._thread = threading.Thread(
                target=self._run, name="mks-panel", daemon=True
            )
            self._thread.start()

    def stop(self):
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=2)

    def _run(self):
        while not self._stop.is_set():
            self.sync()
            self._stop.wait(0.8)

    def sync(self):
        if self._stop.is_set() or time.monotonic() < self._retry_after:
            return
        if not self._lock.acquire(blocking=False):
            return
        try:
            state = self.tasks.snapshot()
            with self.rig.try_locked(timeout=0) as owned:
                if not owned:
                    return
                hardware = self.rig.status()
                if not hardware["arm"]:
                    self.report = {"connected": False}
                    return
                transport = self.rig.require_arm().transport
                reply = []
                transport.send("$EP", diagnostics=reply)
                match = next(
                    (m for line in reply if (m := REPORT.fullmatch(line))), None
                )
                if match is None:
                    raise ValueError("MKS display protocol unavailable")
                page, committed, rendered, view, touches, flushes = map(
                    int, match.groups()
                )
                content = page_content(state, hardware["ready"], page)
                if (
                    self._transport is not transport
                    or self._content != content
                    or committed != self._seq
                ):
                    seq = committed % 2147483647 + 1
                    for command in frame_commands(seq, content):
                        transport.send(command)
                    self._seq, self._content, self._transport = seq, content, transport
                self.report = {
                    "connected": True,
                    "sent": self._seq,
                    "rendered": rendered,
                    "page": page,
                    "view": VIEWS[view] if view < len(VIEWS) else "unknown",
                    "touches": touches,
                    "flushes": flushes,
                }
                touch = next(
                    (m for line in reply if (m := TOUCH.fullmatch(line))), None
                )
                if touch:
                    self.report["touch_sample"] = dict(
                        zip(
                            (
                                "presses",
                                "adc_x",
                                "adc_y",
                                "pressure",
                                "x",
                                "y",
                                "live_pressure",
                            ),
                            map(int, touch.groups()),
                            strict=True,
                        )
                    )

        except Exception as exc:
            # The panel is optional. Avoid blocking a task on a stock or disconnected board.
            if self.report.get("connected") or not self._retry_after:
                log.warning("MKS display unavailable (%s)", type(exc).__name__)
            self.report = {"connected": False}
            self._retry_after = time.monotonic() + 10
            self._content = None
        finally:
            self._lock.release()
