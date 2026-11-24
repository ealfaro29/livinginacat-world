"""Camera frame calibration — physical setup check + software rotation.

One overhead frame drives both halves of the step: a physical
camera-setup diagnostic (phone shape, coverage, edge straightness via
``check_phone_in_frame``) and the software frame-rotation code. The
page shows a blue UP and a red RIGHT marker; their relative positions
in the raw frame tell us which cv2 rotation uprights the camera view,
so every later frame grab (camera mapping, validation, runtime vision)
can rotate first and treat the image as canonical portrait.
"""

import logging
import time

import cv2
import numpy as np

from physiclaw.common.logger.evidence import record_event
from physiclaw.core.bridge import CalibrationState
from physiclaw.core.hardware.camera import Camera
from physiclaw.core.vision.blobs import find_largest_hsv_blob
from physiclaw.core.vision.util import check_phone_in_frame

log = logging.getLogger(__name__)


def _pick_rotation_from_markers(
    frame: np.ndarray, screen_outline: list[list[int]] | None = None
) -> tuple[int, str]:
    """Locate blue UP and red RIGHT markers, derive the cv2 rotation code.

    Returns (rotation_code, human_label). Rotation is -1 (none) or one of
    cv2.ROTATE_{90_CLOCKWISE, 180, 90_COUNTERCLOCKWISE}. Raises if either
    marker is missing.
    """

    if screen_outline is not None:
        outline = np.asarray(screen_outline, dtype=np.int32)
        mask = np.zeros(frame.shape[:2], dtype=np.uint8)
        cv2.fillConvexPoly(mask, outline, 255)
        frame = cv2.bitwise_and(frame, frame, mask=mask)

    def _blob(lower, upper=None) -> tuple[float, float] | None:
        return find_largest_hsv_blob(
            frame,
            lower,
            upper,
            min_area=500,
            morph_op=cv2.MORPH_CLOSE,
            morph_kernel=(7, 7),
            # The displayed arrows occupy rectangles up to 2.5:1. A long
            # reddish rail can cross the estimated outline and dwarf RIGHT.
            max_aspect=4,
        )

    # A cool white screen can look blue; its saturation is much lower than UP.
    blue_low, blue_high = [100, 125, 55], [134, 255, 255]
    up = _blob(blue_low, blue_high)
    record_event(
        "camera.up_marker",
        detected=up,
        hsv_lower=blue_low,
        hsv_upper=blue_high,
    )
    if up is None:
        raise RuntimeError("UP (blue) marker not found")
    # The camera can render the red marker pink on a bright display.
    red = [([0, 38, 60], [11, 255, 255]), ([144, 38, 60], [180, 255, 255])]
    right = _blob(red)
    record_event("camera.right_marker", detected=right, hsv_ranges=red)
    if right is None:
        raise RuntimeError("RIGHT (red) marker not found")
    up_x, up_y = up
    right_x, right_y = right

    log.info(
        f"  Blue UP at ({up_x:.0f}, {up_y:.0f}), red RIGHT at ({right_x:.0f}, {right_y:.0f})"
    )

    if up_y < right_y and abs(up_x - right_x) < abs(up_y - right_y):
        code, label = -1, "0° — no rotation needed"
    elif up_x < right_x and abs(up_y - right_y) < abs(up_x - right_x):
        code, label = cv2.ROTATE_90_CLOCKWISE, "90° clockwise"
    elif up_y > right_y and abs(up_x - right_x) < abs(up_y - right_y):
        code, label = cv2.ROTATE_180, "180°"
    else:
        code, label = cv2.ROTATE_90_COUNTERCLOCKWISE, "90° counter-clockwise"

    if screen_outline is not None:
        # UP is near the top centre of the display, RIGHT near the middle
        # of its right edge. A blue reflection near the middle can reverse
        # both axes while still fitting every point of the symmetric grid.
        x, y, width, height = cv2.boundingRect(np.asarray(screen_outline, np.int32))
        points = (np.array([up, right]) - [x, y]) / [width, height]
        u, v = points.T
        u, v = {
            -1: (u, v),
            cv2.ROTATE_90_CLOCKWISE: (1 - v, u),
            cv2.ROTATE_180: (1 - u, 1 - v),
            cv2.ROTATE_90_COUNTERCLOCKWISE: (v, 1 - u),
        }[code]
        if not (
            0.20 < u[0] < 0.80 and v[0] < 0.38 and u[1] > 0.55 and 0.24 < v[1] < 0.76
        ):
            raise RuntimeError(
                "Orientation markers are outside their expected screen positions"
            )
    return code, label


def calibrate_camera_frame(cam: Camera, cal: CalibrationState) -> dict:
    """Camera frame calibration — physical setup check + rotation code.

    One overhead frame drives both:
      - physical camera-setup diagnostic (shape, coverage, edge straightness),
      - software rotation code picked from the UP/RIGHT markers.

    Returns ``{"rotation", "rotation_name", "setup_ok", "issues",
              "coverage", "aspect_ratio", "image_size", "phone_region"}``.
    """
    log.info(
        "═══ Camera frame calibration ═══",
        extra={
            "event": "calibration.started",
            "console": True,
            "console_message": "Calibration: checking camera alignment",
        },
    )
    cal.set_phase("markers")
    time.sleep(1.0)

    frame = cam.raw_frame()
    if frame is None:
        raise RuntimeError("Camera read failed — is the camera connected?")

    checks = check_phone_in_frame(frame)
    record_event("camera.frame_checks", checks=checks)
    rotation, rot_label = _pick_rotation_from_markers(
        frame, checks.get("screen_outline")
    )
    # The CLI/browser setup surfaces the returned issues as warnings. Keep
    # advisory checks in server diagnostics instead of duplicating them as
    # production warnings; actual capture/marker failures still raise.
    log.info(
        f"  ✓ Camera frame: rotation={rot_label}, setup_ok={checks['ok']}",
        extra={
            "event": "calibration.checked",
            "console": checks["ok"],
            "console_message": "Camera alignment ready",
        },
    )
    return {
        "rotation": rotation,
        "rotation_name": rot_label,
        "setup_ok": checks["ok"],
        "issues": checks["issues"],
        "coverage": checks["coverage"],
        "aspect_ratio": checks["aspect_ratio"],
        "image_size": checks["image_size"],
        "phone_region": checks["phone_region"],
    }
