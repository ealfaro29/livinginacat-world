"""Live operator preview and hardware image adjustments."""

import asyncio

from starlette.responses import JSONResponse, Response

from physiclaw.core.bridge.handler import json_or_none
from physiclaw.core.hardware.image_controls import CameraOptionError
from physiclaw.core.vision.preprocess import resize_to_max_edge
from physiclaw.core.vision.util import encode_jpeg

PRIVATE = {"Cache-Control": "private, no-store"}


def failure(exc):
    if isinstance(exc, CameraOptionError):
        return JSONResponse(
            {"error": exc.code}, status_code=exc.status, headers=PRIVATE
        )
    return JSONResponse({"error": "camera_busy"}, status_code=409, headers=PRIVATE)


def connected(rig):
    cam = rig.cam
    if cam is None:
        raise CameraOptionError("camera_offline")
    return cam


def preview(rig):
    with rig.locked():
        frame = connected(rig).preview_frame()
    if frame is None:
        raise CameraOptionError("frame_unavailable")
    return encode_jpeg(resize_to_max_edge(frame, 900), quality=76)


def register(mcp, rig, tasks):
    def options(change=None):
        with rig.locked():
            return connected(rig).operator_settings(change)

    @mcp.custom_route("/entity/api/camera/options", methods=["GET", "POST"])
    async def camera_options(request):
        try:
            if request.method == "GET":
                state = await asyncio.to_thread(options)
            else:
                body = await json_or_none(request)
                if body is None or set(body) != {
                    "device",
                    "control",
                    "value",
                    "previous",
                }:
                    raise CameraOptionError("invalid_control", 400)
                if tasks.lock.locked():
                    raise CameraOptionError("task_active")
                async with tasks.lock:
                    if tasks.snapshot()["current"]:
                        raise CameraOptionError("task_active")
                    state = await asyncio.to_thread(options, body)
            return JSONResponse(state, headers=PRIVATE)
        except (CameraOptionError, RuntimeError, OSError) as exc:
            return failure(exc)

    @mcp.custom_route("/entity/api/camera/preview", methods=["GET"])
    async def camera_preview(request):
        try:
            jpeg = await asyncio.to_thread(preview, rig)
            return Response(jpeg, media_type="image/jpeg", headers=PRIVATE)
        except (CameraOptionError, RuntimeError, OSError) as exc:
            return failure(exc)
