"""Operator-only MCP lifecycle and read-only touchscreen routes."""

import asyncio
from pathlib import Path
from typing import Literal

from starlette.responses import FileResponse, JSONResponse

from physiclaw.entity import camera, task_routes, travel
from physiclaw.entity.pulse_hardware import run_on_rig
from physiclaw.entity.tasks import Tasks

ASSETS = Path(__file__).resolve().parents[1] / "static" / "entity"


def register(mcp, tasks: Tasks, rig, display=None):
    travel.register(mcp, rig, tasks)
    camera.register(mcp, rig, tasks)
    task_routes.register(mcp, tasks, rig)

    @mcp.custom_route("/entity/travel", methods=["GET"])
    async def travel_page(request):
        return FileResponse(
            ASSETS / "travel.html", headers={"Cache-Control": "no-store"}
        )

    async def published(result):
        if display is not None:
            await asyncio.to_thread(display.sync)
        return result

    def state():
        hardware = rig.status()
        return tasks.snapshot() | {
            "hardware": {
                key: bool(hardware.get(key))
                for key in ("arm", "camera", "bridge", "ready")
            },
        }

    @mcp.tool()
    async def entity_enqueue(title: str, request_id: str) -> dict:
        """Queue one explicit operator request without moving. Reuse request_id to retry."""
        return await published(tasks.enqueue(title, request_id))

    @mcp.tool()
    async def entity_start(task_id: int) -> dict:
        """Mark the first queued request current before sending its MCP actions."""
        return await published(await tasks.start(task_id))

    @mcp.tool()
    async def entity_finish(
        task_id: int, outcome: Literal["done", "failed", "cancelled"]
    ) -> dict:
        """Close the operator's task after checking its result. Leaves the next task waiting."""
        return await published(await tasks.finish(task_id, outcome))

    @mcp.tool()
    @tasks.track
    async def entity_play_pulse(task_id: int, round_id: str, port: int = 8050) -> dict:
        """Play an operator-started Pulse round using the camera and real touchscreen acknowledgements."""
        if not tasks.is_running_request(task_id, "pulse-" + round_id):
            return {"reason": "lost"}
        return await asyncio.to_thread(run_on_rig, rig, round_id, port)

    @mcp.tool()
    async def entity_status() -> dict:
        """Read the current task, live action, waiting tasks and rig connection state."""
        return state()

    @mcp.custom_route("/entity/state", methods=["GET"])
    async def panel_state(request):
        return JSONResponse(state(), headers={"Cache-Control": "no-store"})

    @mcp.custom_route("/entity/display/state", methods=["GET"])
    async def display_state(request):
        return JSONResponse(
            display.report if display else {"connected": False},
            headers={"Cache-Control": "no-store"},
        )

    @mcp.custom_route("/entity/", methods=["GET"])
    async def panel(request):
        return FileResponse(
            ASSETS / "index.html", headers={"Cache-Control": "no-cache"}
        )

    @mcp.custom_route("/entity/sentient.svg", methods=["GET"])
    async def symbol(request):
        return FileResponse(ASSETS / "sentient.svg", media_type="image/svg+xml")

    @mcp.custom_route("/entity/space-grotesk.ttf", methods=["GET"])
    async def font(request):
        return FileResponse(ASSETS / "space-grotesk.ttf", media_type="font/ttf")
