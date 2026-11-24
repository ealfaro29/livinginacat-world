"""Operator-only queue editing. Requests change the same durable rows the MKS reads."""

from starlette.responses import JSONResponse

from physiclaw.core.bridge.handler import json_or_none
from physiclaw.entity.tasks import QueueError


def register(mcp, tasks, rig):
    @mcp.custom_route("/entity/api/tasks", methods=["GET", "POST"])
    async def task_queue(request):
        headers = {"Cache-Control": "private, no-store"}
        added = None
        try:
            if request.method == "POST":
                body = await json_or_none(request)
                if not isinstance(body, dict):
                    raise QueueError("invalid_task")
                action = body.get("action")
                if action == "add" and set(body) <= {
                    "action",
                    "instructions",
                    "request_id",
                    "run_at",
                }:
                    added = tasks.submit(
                        body.get("instructions"),
                        body.get("request_id"),
                        body.get("run_at"),
                    )
                elif action == "move" and set(body) == {
                    "action",
                    "id",
                    "neighbor",
                    "direction",
                }:
                    tasks.move(body["id"], body["neighbor"], body["direction"])
                elif action == "remove" and set(body) == {"action", "id"}:
                    tasks.remove_waiting(body["id"])
                else:
                    raise QueueError("invalid_task")
            view = tasks.snapshot(operator=True)
            view["ready"] = bool(
                rig.ready and rig.hardware_ready and rig.calibration.precision_verified
            )
            if added is not None:
                view["added"] = added
            return JSONResponse(view, headers=headers)
        except QueueError as exc:
            return JSONResponse(
                {"error": exc.code}, status_code=exc.status, headers=headers
            )
