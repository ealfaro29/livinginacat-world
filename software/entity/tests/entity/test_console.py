import asyncio

import pytest
from mcp.server.mcpserver.exceptions import ToolError
from starlette.testclient import TestClient

from physiclaw.common import paths
from physiclaw.core.server.app import build_server
from physiclaw.core.server.planes import build_control_app
from physiclaw.entity.tasks import Tasks


@pytest.mark.asyncio
async def test_queue_retries_fifo_and_restart(tmp_path):
    queue = Tasks(tmp_path / "queue.sqlite3")
    a = queue.enqueue("Calcular 89 × 90", "req-a")
    assert queue.enqueue(a["title"], "req-a") == a
    b = queue.enqueue("Abrir el calendario", "req-b")
    with pytest.raises(ToolError):
        await queue.start(b["id"])
    await queue.start(a["id"])
    with pytest.raises(ToolError):
        await queue.start(b["id"])
    resumed = Tasks(queue.path)
    resumed.recover()
    assert resumed.snapshot()["current"] is None
    assert resumed.snapshot()["last"] == a | {"state": "interrupted"}
    assert resumed.snapshot()["queue"] == [b]
    await resumed.start(b["id"])
    await resumed.finish(b["id"], "done")
    assert (await resumed.finish(b["id"], "done"))["state"] == "done"
    assert resumed.snapshot()["queue"] == []


@pytest.mark.asyncio
async def test_an_activity_finishes_before_the_task_closes_even_on_disconnect(tmp_path):
    queue = Tasks(tmp_path / "queue.sqlite3")
    started, release = asyncio.Event(), asyncio.Event()
    calls = []

    @queue.track
    async def tap():
        calls.append("tap")
        started.set()
        await release.wait()
        return "ok"

    with pytest.raises(ToolError, match="idle"):
        await tap()
    job = queue.enqueue("Toque de prueba", "one")
    assert not calls
    await queue.start(job["id"])
    caller = asyncio.create_task(tap())
    await started.wait()
    assert queue.snapshot()["action"] == "tap"
    caller.cancel()
    with pytest.raises(asyncio.CancelledError):
        await caller
    close = asyncio.create_task(queue.finish(job["id"], "cancelled"))
    await asyncio.sleep(0)
    assert not close.done()
    release.set()
    await close
    assert queue.snapshot()["action"] is None
    assert calls == ["tap"]


@pytest.mark.asyncio
async def test_mcp_and_touchscreen_share_state_and_never_publish_on_phone_plane(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(paths, "HOME", tmp_path)
    monkeypatch.setenv("ENTITY_ON_DEMAND", "1")
    bundle = build_server()
    assert bundle.mcp.name == "Entity by Sentient"
    catalog = {entry.name for entry in await bundle.mcp.list_tools()}
    assert {
        "tap",
        "peek",
        "entity_enqueue",
        "entity_start",
        "entity_finish",
        "entity_status",
    } <= catalog
    app = build_control_app(bundle.mcp)
    with TestClient(app, base_url="http://127.0.0.1") as client:
        assert client.get("/entity/").status_code == 200
        assert client.get("/entity/state").json()["hardware"]["arm"] is False
        for asset in ["sentient.svg", "space-grotesk.ttf"]:
            assert client.get("/entity/" + asset).status_code == 200
        await bundle.mcp.call_tool(
            "entity_enqueue", {"title": "Primer trabajo", "request_id": "demo-1"}
        )
        pending = client.get("/entity/state").json()
        assert pending["current"] is None
        task_id = pending["queue"][0]["id"]
        await bundle.mcp.call_tool("entity_start", {"task_id": task_id})
        assert (
            client.get("/entity/state").json()["current"]["title"] == "Primer trabajo"
        )
        await bundle.mcp.call_tool(
            "entity_finish", {"task_id": task_id, "outcome": "done"}
        )
        assert client.get("/entity/state").json()["last"]["state"] == "done"
        assert not client.get("/entity/state").json()["current"]
        assert client.post("/entity/state").status_code == 405
    with TestClient(bundle.phone_app.build()) as phone:
        assert phone.get("/entity/state").status_code == 404
