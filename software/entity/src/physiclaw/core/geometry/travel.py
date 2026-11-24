"""Work-coordinate travel taught by the operator, in millimetres."""

import math

EDGES = ("bottom-left", "bottom-right", "top-right", "top-left")
Point = tuple[float, float]
Marks = dict[str, Point]


def read_point(value: object) -> Point:
    if not isinstance(value, (tuple, list)) or len(value) != 2:
        raise ValueError("invalid_point")
    if any(type(n) not in (int, float) or not math.isfinite(n) for n in value):
        raise ValueError("invalid_point")
    return float(value[0]), float(value[1])


def read_marks(value: object) -> Marks:
    if not isinstance(value, dict) or set(value).difference(EDGES):
        raise ValueError("invalid_marks")
    return {key: read_point(point) for key, point in value.items()}


def contains(marks: Marks, point: Point) -> bool:
    """Convex polygon in front-left, front-right, back-right, back-left order."""
    for i, name in enumerate(EDGES):
        x, y = marks[name]
        x2, y2 = marks[EDGES[(i + 1) % 4]]
        dx, dy = x2 - x, y2 - y
        # A hundredth of a millimetre accommodates GRBL position rounding.
        if dx * (point[1] - y) - dy * (point[0] - x) < -0.01 * math.hypot(dx, dy):
            return False
    return True


def validate_outline(marks: Marks) -> None:
    if set(marks) != set(EDGES):
        raise ValueError("need_four")
    fl, fr, br, bl = (marks[k] for k in EDGES)
    if max(fl[0], bl[0]) >= min(fr[0], br[0]) or max(fl[1], fr[1]) >= min(bl[1], br[1]):
        raise ValueError("corner_order")
    if not all(contains(marks, p) for p in marks.values()):
        raise ValueError("corner_order")
