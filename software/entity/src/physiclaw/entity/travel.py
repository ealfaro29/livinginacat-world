"""Operator-only measurement of the four corners, using the rig's one serial connection."""

import asyncio
import dataclasses
import hashlib
import math
import uuid

from starlette.responses import JSONResponse

from physiclaw.core.calibration.parking import (
    glass_and_reference,
    parking_positions,
    validate_taught_travel,
    validate_travel_span,
)
from physiclaw.core.geometry.travel import EDGES, contains, read_point

DIRECTIONS = {"left": (-1, 0), "right": (1, 0), "front": (0, -1), "back": (0, 1)}


def operate(rig, body, session):
    """Each request reads the real idle work position inside the shared hardware lock."""
    with rig.locked(wait_seconds=1):
        cal = rig.calibration
        arm = rig.arm
        if (
            arm is None
            or not rig.origin_pinned
            or not (cal.precision_verified or cal.travel_limits)
            or cal.pct_to_grbl is None
        ):
            raise ValueError("not_calibrated")
        arm.wait_idle(timeout=2)
        pos = arm.position(require_work_frame=True)
        # A stale tab must not jog after a reconnect, a new arm fit, or another user's move.
        frame = hashlib.sha256(
            f"{session}:{id(arm)}:".encode() + cal.pct_to_grbl.tobytes()
        ).hexdigest()[:24]
        if body is not None:
            if (
                not isinstance(body, dict)
                or body.get("frame") != frame
                or math.dist(pos, read_point(body.get("from"))) > 0.05
            ):
                raise ValueError("position_changed")
            action = body.get("action")
            if action == "park":
                if not cal.travel_limits or not contains(cal.travel_limits, pos):
                    raise ValueError("no_measured_park")
                options = parking_positions(cal.pct_to_grbl, taught=cal.travel_limits)
                corner = body.get("corner")
                if corner is not None and (
                    not isinstance(corner, str) or corner not in options
                ):
                    raise ValueError("no_measured_park")
                arm.lift_stylus()
                expected = rig.park(corner=corner)
                pos = arm.position(require_work_frame=True)
                if expected is None or math.dist(expected, pos) > 0.1:
                    raise ValueError("position_changed")
            elif not cal.precision_verified:
                raise ValueError("not_calibrated")
            elif action == "jog":
                direction, size = body.get("direction"), body.get("mm")
                if (
                    not isinstance(direction, str)
                    or direction not in DIRECTIONS
                    or type(size) is not int
                    or size not in (1, 5)
                ):
                    raise ValueError("invalid_step")
                dx, dy = DIRECTIONS[direction]
                target = (pos[0] + dx * size, pos[1] + dy * size)
                validate_travel_span(
                    [
                        *glass_and_reference(cal.pct_to_grbl),
                        *cal.travel_marks.values(),
                        pos,
                        target,
                    ]
                )
                rig._mark_away()
                arm.teach_to(*target)
                pos = arm.position(require_work_frame=True)
                if math.dist(target, pos) > 0.1:
                    raise ValueError("position_changed")
            elif action == "mark":
                corner = body.get("corner")
                if not isinstance(corner, str) or corner not in EDGES:
                    raise ValueError("invalid_marks")
                marks = {**cal.travel_marks, corner: pos}
                validate_travel_span(
                    [*glass_and_reference(cal.pct_to_grbl), *marks.values()]
                )
                dataclasses.replace(cal, travel_marks=marks).save()
                cal.travel_marks = marks
            elif action == "apply":
                if body.get("marks") != {
                    k: list(v) for k, v in cal.travel_marks.items()
                }:
                    raise ValueError("marks_changed")
                validate_taught_travel(cal.pct_to_grbl, cal.travel_marks)
                limits = dict(cal.travel_marks)
                if parking_positions(cal.pct_to_grbl, taught=limits) != limits:
                    raise ValueError("clear_glass")
                applied = dataclasses.replace(cal, travel_limits=limits)
                applied.remember_travel()
                applied.save()
                cal.travel_limits = limits
                arm.travel_limits = limits
            else:
                raise ValueError("invalid_action")
        return {
            "frame": frame,
            "position": pos,
            "can_teach": cal.precision_verified,
            "marks": cal.travel_marks,
            "limits": cal.travel_limits,
        }


def register(mcp, rig, tasks):
    session = uuid.uuid4().hex

    @mcp.custom_route("/entity/api/travel", methods=["GET", "POST"])
    async def travel(request):
        try:
            body = None
            if request.method == "POST":
                body = await request.json()
                if not isinstance(body, dict):
                    raise ValueError("invalid_action")
            if body is not None:
                if tasks.lock.locked():
                    raise ValueError("task_active")
                async with tasks.lock:
                    if tasks.snapshot()["current"] is not None:
                        raise ValueError("task_active")
                    result = await asyncio.to_thread(operate, rig, body, session)
            else:
                result = await asyncio.to_thread(operate, rig, None, session)
        except (ValueError, RuntimeError, OSError) as exc:
            key = str(exc)
            known = {
                "task_active",
                "invalid_action",
                "invalid_point",
                "invalid_marks",
                "invalid_step",
                "need_four",
                "corner_order",
                "enclose_glass",
                "clear_glass",
                "travel_span",
                "position_changed",
                "marks_changed",
                "not_calibrated",
                "no_measured_park",
            }
            return JSONResponse(
                {"error": key if key in known else "unavailable"},
                status_code=409,
                headers={"Cache-Control": "no-store"},
            )
        return JSONResponse(result, headers={"Cache-Control": "no-store"})
