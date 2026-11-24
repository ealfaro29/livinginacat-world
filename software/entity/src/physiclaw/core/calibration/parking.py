"""Off-screen parks in the calibrated XY frame (mm)."""

import math

import numpy as np

from physiclaw.core.calibration.transforms import PARK_PCT
from physiclaw.core.geometry import apply_affine, invert_affine
from physiclaw.core.geometry.travel import Marks, contains, validate_outline
from physiclaw.core.hardware.arm import X_TRAVEL, Y_TRAVEL

_left, _top = PARK_PCT
CORNERS = {
    "top-left": PARK_PCT,
    "top-right": (1 - _left, _top),
    "bottom-left": (_left, 1 - _top),
    "bottom-right": (1 - _left, 1 - _top),
}
# The mesh is 7.9 mm across. Allow another millimetre beyond its radius.
MIN_CLEARANCE_MM = 5.0


def validate_travel_span(points) -> None:
    if np.any(np.ptp(np.asarray(points, dtype=float), axis=0) > (X_TRAVEL, Y_TRAVEL)):
        raise ValueError("travel_span")


def glass_and_reference(affine):
    glass = [apply_affine(affine, x, y) for x in (0, 1) for y in (0, 1)]
    return [*glass, apply_affine(affine, *PARK_PCT)]


def validate_taught_travel(affine, taught: Marks) -> None:
    validate_outline(taught)
    validate_travel_span(list(taught.values()))
    if not all(contains(taught, p) for p in glass_and_reference(affine)):
        raise ValueError("enclose_glass")
    inverse = invert_affine(affine)
    norms = np.linalg.norm(inverse[:, :2], axis=1)
    for point in taught.values():
        x, y = apply_affine(inverse, *point)
        if max(max(-x, x - 1) / norms[0], max(-y, y - 1) / norms[1]) < MIN_CLEARANCE_MM:
            raise ValueError("clear_glass")


def parking_positions(
    affine, confirmed=(), taught: Marks | None = None
) -> dict[str, tuple[float, float]]:
    """Choose real stops when taught. The bridge spans X, so it must clear glass in Y."""
    reference = apply_affine(affine, *PARK_PCT)
    glass_y = [apply_affine(affine, x, y)[1] for x in (0, 1) for y in (0, 1)]
    front, back = min(glass_y), max(glass_y)

    def clears_bridge_row(point):
        return (
            point[1] <= front - MIN_CLEARANCE_MM or point[1] >= back + MIN_CLEARANCE_MM
        )

    if taught:
        validate_taught_travel(affine, taught)
        clear = {
            name: point for name, point in taught.items() if clears_bridge_row(point)
        }
        if clear:
            return clear
    # A mirrored phone corner is not a measured rail stop. In particular,
    # clipping a front corner to the last row of glass leaves the bridge in view.
    positions = {"top-left": reference}
    for name in confirmed:
        point = apply_affine(affine, *CORNERS[name])
        if clears_bridge_row(point):
            positions[name] = point
    try:
        validate_travel_span([*glass_and_reference(affine), *positions.values()])
    except ValueError as exc:
        raise ValueError("Checked parking corners exceed the gantry travel") from exc
    return positions


def nearest_park(positions, current):
    """Compare physical distances, retaining a deterministic winner on ties."""
    return min(positions.values(), key=lambda xy: math.dist(current, xy))
