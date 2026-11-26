# /// script
# requires-python = ">=3.12"
# dependencies = ["shapely>=2,<3"]
# ///
"""Check physical model extrusion on four motor roots, excluding all support paths."""

import argparse
import json
import math
import re
from itertools import pairwise
from pathlib import Path

from shapely.geometry import LineString, box
from shapely.ops import unary_union

HEIGHTS = (84.2, 84.4, 84.6, 84.8, 91.2, 91.4, 91.6, 91.8)
FIELDS = re.compile(r" ([XYEIJ])([-+\d.]+)")
MODEL = {
    "Outer wall",
    "Inner wall",
    "Overhang wall",
    "Gap infill",
    "Internal solid infill",
    "Sparse infill",
    "Bridge",
    "Internal Bridge",
    "Bottom surface",
    "Top surface",
}


def segment(g, p, end, args):
    if g == "G1" or "I" not in args or "J" not in args:
        return LineString([p, end])
    cx, cy = p[0] + args["I"], p[1] + args["J"]
    a = math.atan2(p[1] - cy, p[0] - cx)
    b = math.atan2(end[1] - cy, end[0] - cx)
    da = (b - a) % (2 * math.pi) if g == "G3" else -((a - b) % (2 * math.pi))
    r = math.hypot(p[0] - cx, p[1] - cy)
    n = max(1, math.ceil(abs(da) * r / 0.25))
    return LineString(
        [p]
        + [
            (cx + r * math.cos(a + da * i / n), cy + r * math.sin(a + da * i / n))
            for i in range(1, n)
        ]
        + [end]
    )


def audit(path):
    # The 196 x 156.9 mm shell is centred at 128,128 on plate 3.
    xmin, ymin = 128, -95.55
    rectangles = {}
    for tag, x in (("A", -31), ("B", 21)):
        for side in (-1, 1):
            l, r = sorted((x + side * 21.7, x + side * 25.4))
            rectangles[(tag, side)] = box(l + xmin, 264 + ymin, r + xmin, 273 + ymin)
    lines = {h: [] for h in HEIGHTS}
    p = (0.0, 0.0)
    h = 0
    feature = None
    width = 0.42
    for s in path.open():
        if s.startswith("; Z_HEIGHT: "):
            h = round(float(s.split(":")[1]), 4)
            feature = None
            if h > max(HEIGHTS):
                break
        elif s.startswith("; FEATURE: "):
            feature = s[11:].strip()
        elif s.startswith("; LINE_WIDTH: "):
            width = float(s.split(":")[1])
        elif s.startswith(("G0 ", "G1 ", "G2 ", "G3 ")):
            if h not in HEIGHTS:
                continue
            args = {k: float(v) for k, v in FIELDS.findall(s)}
            end = (args.get("X", p[0]), args.get("Y", p[1]))
            if feature in MODEL and args.get("E", 0) > 0 and end != p:
                lines[h].append(
                    segment(s.split()[0], p, end, args).buffer(width / 2, quad_segs=3)
                )
            p = end
    out = {}
    for (tag, side), rect in rectangles.items():
        hs = HEIGHTS[:4] if tag == "A" else HEIGHTS[4:]
        masks = [
            unary_union([l.intersection(rect) for l in lines[h] if l.intersects(rect)])
            for h in hs
        ]
        out[tag + (" left" if side < 0 else " right")] = [
            round(a.intersection(b).area, 2) for a, b in pairwise(masks)
        ]
    return out


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("gcode", type=Path)
    p.add_argument("--original", type=Path)
    opts = p.parse_args()
    results = {
        "root_window_mm": [3.7, 9.0],
        "consecutive_model_layers_mm": HEIGHTS,
        "R02_model_overlap_mm2": audit(opts.gcode),
    }
    assert all(min(v) > 8 for v in results["R02_model_overlap_mm2"].values()), results
    if opts.original:
        results["R01_model_overlap_mm2"] = audit(opts.original)
        assert all(min(v) < 1 for v in results["R01_model_overlap_mm2"].values()), (
            results
        )
    print(json.dumps(results, indent=2))
