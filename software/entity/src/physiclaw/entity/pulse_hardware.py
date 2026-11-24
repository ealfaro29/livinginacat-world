"""Camera-guided Pulse round on the rig that owns the serial port."""

import logging
import math
import re
import time

import cv2
import httpx
import numpy as np

from physiclaw.core.calibration._common import CAL_STRIKE_DURATION

TOTAL = 5
log = logging.getLogger(__name__)
ANGLES = np.arange(24) * (2 * np.pi / 24)
DIRECTIONS = np.column_stack((np.cos(ANGLES), np.sin(ANGLES)))


class RoundEnded(Exception):
    """A reason the bilingual director can present to the operator."""


def target_center(frame: np.ndarray) -> tuple[float, float] | None:
    """Require one round warm disc, a darker gap and a contrasting circular rim."""
    h, w = frame.shape[:2]
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    warm = cv2.bitwise_or(
        cv2.inRange(hsv, (0, 70, 120), (24, 255, 255)),
        cv2.inRange(hsv, (170, 75, 120), (179, 255, 255)),
    )
    contours, _ = cv2.findContours(
        cv2.medianBlur(warm, 3), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )
    candidates = []
    for contour in contours:
        _, _, width, height = cv2.boundingRect(contour)
        if not (0.033 * w <= width <= 0.16 * w and 0.69 < width / height < 1.42):
            continue
        if cv2.contourArea(contour) < 0.54 * width * height:
            continue
        m = cv2.moments(contour)
        center = np.array([m["m10"] / m["m00"], m["m01"] / m["m00"]])
        x, y = center / (w, h)
        if not (0.08 < x < 0.92 and 0.15 < y < 0.85):
            continue
        # The iPhone's neon rim can clip to white on the overhead camera.
        # Measure brightness in the gap and beyond the rim on the same ray.
        offsets = DIRECTIONS[:, None, :] * [width / 2, height / 2]
        radii = np.linspace(1.08, 2.50, 32)
        points = np.rint(center + offsets * radii[None, :, None]).astype(int)
        samples = hsv[points[:, :, 1].clip(0, h - 1), points[:, :, 0].clip(0, w - 1)]
        hue, sat, val = (samples[:, :, i].astype(int) for i in range(3))
        background = np.maximum(val[:, :6].min(axis=1), np.median(val[:, -5:], axis=1))
        ring_color = ((hue >= 16) & (hue <= 90)) | (sat <= 85)
        bright = ring_color & (val >= 145) & (val > background[:, None] + 45)
        if np.count_nonzero(bright[:, 6:-5].any(axis=1)) >= 16:
            candidates.append((float(x), float(y)))
    return candidates[0] if len(candidates) == 1 else None


def screen_target(rig):
    """Resample the calibrated glass directly into physical screen coordinates."""
    frame = rig.require_cam().snapshot()
    if frame is None:
        return None
    transform = (
        rig.require_transforms().pct_to_cam * np.array(frame.shape[1::-1])[:, None]
    )
    dimension = rig.calibration.screen_dimension
    width = 390
    height = round(width * dimension["height"] / dimension["width"])
    transform[:, :2] /= (width, height)
    screen = cv2.warpAffine(
        frame, transform, (width, height), flags=cv2.INTER_LINEAR | cv2.WARP_INVERSE_MAP
    )
    return target_center(screen)


def next_target(rig, previous):
    # Two fresh looks allow the new target to render. Only leave the glass if
    # the carriage obscures it. A missing or ambiguous target never fires.
    for clear_view in (False, True):
        if clear_view:
            rig.park()
        for _ in range(3):
            center = screen_target(rig)
            if center is not None and (
                previous is None or math.dist(center, previous) > 0.055
            ):
                return center
            time.sleep(0.04)
    raise RoundEnded("vision")


def play_physical(rig, read_phone):
    if not rig.ready or not rig.origin_pinned or not rig.calibration.precision_verified:
        raise RoundEnded("offline")
    # Check cancellation before any automatic parking or movement.
    read_phone()
    with rig.engaged(wait_seconds=1):
        arm = rig.require_arm()
        previous = None
        taps = 0
        for index in range(TOTAL):
            started = time.monotonic()
            deadline = time.monotonic() + 2.5
            while True:
                phone = read_phone()
                if phone["phase"] != "playing" or phone["hits"] != index:
                    raise RoundEnded("lost")
                if phone["accepting"]:
                    break
                if time.monotonic() >= deadline:
                    raise RoundEnded("lost")
                time.sleep(0.05)
            center = next_target(rig, previous)
            if rig.assistive_touch.overlaps_at(*center):
                raise RoundEnded("vision")
            x, y = center
            initial_misses = phone["misses"]
            # Cancellation during image acquisition need not move the carriage.
            read_phone()
            rig.move_to_bbox_center([x, y, x, y])
            for attempt in range(2):
                now = read_phone()
                if now["hits"] == index + 1 and attempt:
                    break  # A late acknowledgement already settled the previous strike.
                if (
                    now["phase"] != "playing"
                    or now["hits"] != index
                    or not now["accepting"]
                ):
                    raise RoundEnded("lost")
                if now["misses"] != initial_misses:
                    raise RoundEnded("miss")
                arm.tap(duration=CAL_STRIKE_DURATION)
                taps += 1
                deadline = time.monotonic() + 1.1
                while True:
                    now = read_phone()
                    if now["hits"] == index + 1:
                        break
                    if now["hits"] != index or now["phase"] != "playing":
                        raise RoundEnded("lost")
                    if now["misses"] != initial_misses:
                        raise RoundEnded("miss")
                    if time.monotonic() >= deadline:
                        break
                    time.sleep(0.05)
                if now["hits"] == index + 1:
                    break
            else:
                raise RoundEnded("miss")
            log.info(
                "Pulse target %d registered in %.2fs at %.3f,%.3f after %d strike(s)",
                index + 1,
                time.monotonic() - started,
                x,
                y,
                attempt + 1,
            )
            previous = center
        if read_phone()["phase"] != "won":
            raise RoundEnded("miss")
        return {"reason": "done", "taps": taps}


def run_on_rig(rig, round_id: str, port: int = 8050):
    if not re.fullmatch(r"[a-f0-9]{24}", round_id) or not (1 <= port <= 65535):
        return {"reason": "lost"}
    url = f"http://127.0.0.1:{port}/control/session"
    with httpx.Client(timeout=1.5, trust_env=False) as http:

        def read_phone():
            reply = http.get(url, params={"round": round_id})
            reply.raise_for_status()
            body = reply.json()
            if "reason" in body:
                raise RoundEnded(body["reason"])
            return body

        try:
            return play_physical(rig, read_phone)
        except RoundEnded as exc:
            return {"reason": str(exc)}
        except httpx.HTTPError:
            return {"reason": "lost"}
