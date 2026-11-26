# /// script
# requires-python = ">=3.12"
# dependencies = ["build123d==0.13.0", "trimesh==5.2.1", "lxml>=5,<7", "shapely>=2,<3"]
# ///
"""Generate the R01 rescue carrier. Check fit in the original assembly coordinates."""

import argparse
import json
from pathlib import Path

import numpy as np
import trimesh
from build123d import (
    Align,
    Compound,
    Cone,
    Polygon,
    Pos,
    RectangleRounded,
    export_stl,
    extrude,
    import_step,
)
from geometria import (
    HERE,
    STEP,
    block,
    bore,
    common,
    rear_shell,
    rear_shell_r01,
    strap_mount,
)
from motores import BACK, FRONT, MOTORS, carrier, flush_slots, side_block
from shapely.geometry import Point
from shapely.geometry import box as rectangle


def save_mesh(shape, path):
    export_stl(shape, path, tolerance=0.025, angular_tolerance=0.085)
    mesh = trimesh.load_mesh(path)
    assert mesh.is_volume and mesh.is_watertight and len(mesh.split()) == 1
    return mesh


def clipped(part, mask):
    result = part.intersect(mask)
    return Compound(children=result.solids()) if result and result.solids() else None


def check_empty(part, other, label):
    overlap = common(part, other)
    assert overlap < 0.0025, (label, round(overlap, 3))
    return round(overlap, 5)


def tie_at_post(x, side):
    # A 2.5 mm strap encircles the neck of the EXISTING post and the
    # small vertical bar on the OUTSIDE of the new carrier, below the shoulder.
    outer_lug = sorted((x + side * 8.2, x + side * 11.5))
    wrap = (
        Point(x, 279.5)
        .buffer(4.5, quad_segs=32)
        .union(rectangle(outer_lug[0], 277.2, outer_lug[1], 281.8))
        .convex_hull.buffer(0.2, quad_segs=8)
    )

    def prism(p):
        return Pos(0, 0, 86.2) * extrude(
            Polygon(*list(p.exterior.coords)[:-1], align=None),
            amount=2.5,
            dir=(0, 0, 1),
        )

    band = prism(wrap.buffer(1.0, quad_segs=8)).cut(prism(wrap))
    latch = side_block(x, side, 12.1, 15.9, 277.5, 281.5, 85.45, 89.45)
    return band.fuse(latch).clean()


def main(work):
    work.mkdir(parents=True, exist_ok=True)
    asm = import_step(STEP)
    parts = {s.label: s for g in asm.children for s in g.children}
    case = rear_shell_r01(parts["Carcasa_detras"])
    repair = carrier()
    assert repair.is_valid and len(repair.solids()) == 1
    name = json.loads((HERE / "rescate.json").read_text())["objects"][0]["name"]
    mesh = save_mesh(repair, work / (name + "-cad.stl"))
    m = mesh.copy()
    m.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, [1, 0, 0]))
    lo, hi = m.bounds
    m.apply_translation([-(lo[0] + hi[0]) / 2, -(lo[1] + hi[1]) / 2, -lo[2]])
    m.export(work / (name + ".stl"))
    plates = []
    for x, z, side in MOTORS:
        # Restore just the loose 5 mm plate with its original rounded edges
        # and the five slots actually present in the 3MF, not a rectangle.
        clip = block(x - 23, x + 23, FRONT, BACK, z, z + 5)
        old_plate = (
            (Pos(x, 275, z) * extrude(RectangleRounded(46, 46, 3), amount=5))
            .intersect(clip)
            .solids()[0]
        )
        # The raw STEP plate still has circular holes; intersect it with the
        # released R01 to isolate the manufactured slotted plate.
        plate = old_plate.intersect(case).solids()[0]
        plates.append(plate)
        save_mesh(plate, work / ("loose_" + ("A" if side < 0 else "B") + ".stl"))
    high_plate = flush_slots(plates[1])
    upper_name = json.loads((HERE / "rescate.json").read_text())["objects"][1]["name"]
    high_mesh = save_mesh(high_plate, work / (upper_name + "-cad.stl"))
    low, high = high_mesh.bounds
    high_mesh.apply_translation(
        [-(low[0] + high[0]) / 2, -(low[1] + high[1]) / 2, -low[2]]
    )
    high_mesh.export(work / (upper_name + ".stl"))
    stripped = case.cut(*plates).clean()
    export_stl(
        stripped,
        work / "shell_without_plates.stl",
        tolerance=0.08,
        angular_tolerance=0.14,
    )
    new = rear_shell(parts["Carcasa_detras"])
    result = {
        "carrier_volume_cm3": round(repair.volume / 1000, 2),
        "plate_bottom_z_mm": [z for _, z, _ in MOTORS],
        "retention": "Two M3 x 8 cross-bolts with square nuts close the rear entrances. Two 2.5 mm cable ties secure the carrier to the existing rear idler posts below their shoulders.",
        "collisions_mm3": {},
        "plate_capture_mm2": {},
        "roots_mm2": {},
    }
    c = result["collisions_mm3"]
    c["r01_shell_installed"] = check_empty(repair, stripped, "original rear shell")
    # The complete swept volume of the existing posts and shell over their
    # height is also checked as the carrier is lowered, in addition to seat fit.
    for label, xx in (("L", -62.25), ("R", 52.25)):
        c["idler_shoulder_sweep_" + label] = check_empty(
            repair, bore(xx, 279.5, 3, 13.6, 98.8), "shoulder insertion"
        )
        c["m5_nut_entry_" + label] = check_empty(
            repair,
            block(xx - 4.22, xx + 4.22, 274.55, 296, 93.5, 97.9),
            "idler nut insertion",
        )
    for dz in (2, 7, 15, 35, 56, 80, 99):
        c["lower_carrier_" + str(dz)] = check_empty(
            repair.translate((0, 0, dz)), stripped, "lowering carrier " + str(dz)
        )
    for (x, z, side), plate, tag in zip(MOTORS, plates, ("A", "B")):
        c["plate_" + tag] = check_empty(plate, repair, "plate " + tag)
        # A rectangular swept envelope is stricter than sweeping the rounded
        # plate: both the full width and the original 5 mm height must pass.
        c["plate_rear_insertion_" + tag] = check_empty(
            repair, block(x - 23, x + 23, FRONT, 320, z, z + 5), "slide " + tag
        )
        motor = block(x - 21.15, x + 21.15, 275 - 23.15, 275 + 23.15, z - 38, z)
        for kind, sh in (("carrier", repair), ("reinforced_shell", new)):
            c[kind + "_motor_travel_" + tag] = check_empty(
                sh, motor, "motor adjustment " + kind + tag
            )
            for dx in (-15.5, 15.5):
                for dy in (-15.5, 15.5):
                    for off in (-2, 0, 2):
                        check_empty(
                            sh,
                            bore(x + dx, 275 + dy + off, z - 1, 3.12, 7),
                            "M3 shank " + tag,
                        )
                        check_empty(
                            sh,
                            bore(x + dx, 275 + dy + off, z + 5, 6, 5),
                            "M3 head " + tag,
                        )
        pin = -62.25 if side == -1 else 52.25
        tie = tie_at_post(pin, side)
        save_mesh(tie, work / ("tie_" + tag + ".stl"))
        c["strap_to_carrier_" + tag] = check_empty(tie, repair, "tie route " + tag)
        c["strap_to_shell_" + tag] = check_empty(
            tie, stripped, "tie on existing post " + tag
        )
        assert (
            common(tie.translate((0, 0, 4.0)), bore(pin, 279.5, 90.4, 13.6, 11.4)) > 1
        ), "strap retention"
        fastener = bore(x + side * 29.25, 298.25, z + 2.0, 3, 8, (-side, 0, 0))
        head = bore(x + side * 29.25, 298.25, z + 2.0, 5.7, 1.65, (side, 0, 0))
        visual_bolt = fastener.fuse(head)
        save_mesh(visual_bolt, work / ("bolt_" + tag + ".stl"))
        check_empty(visual_bolt, repair, "M3 stop clearance " + tag)
        check_empty(fastener, plate, "locked plate " + tag)
        nut_sweep = side_block(x, side, 24.52, 26.92, 295.55, 300.95, z - 0.70, z + 12)
        check_empty(nut_sweep, repair, "insert square nut " + tag)
        assert common(fastener, plate.translate((0, 2, 0))) > 1, "Rear stop " + tag
        if side == 1:
            for xx in (x - 15.5, x + 15.5):
                for offset in (-2, 0, 2):
                    # Catalogue bounds for the 90-degree #7213 head. Even
                    # the smaller head engages less than 4 mm of motor thread.
                    for diam, h in ((6.72, 96.17), (5.54, 95.56)):
                        cone_height = (diam - 3) / 2
                        bottom = h - cone_height
                        shank = bore(
                            xx, 259.5 + offset, h - 8, 3, 8 - cone_height + 0.01
                        )
                        head = Pos(xx, 259.5 + offset, bottom) * Cone(
                            1.50,
                            diam / 2,
                            cone_height,
                            align=(Align.CENTER, Align.CENTER, Align.MIN),
                        )
                        screw = shank.fuse(head)
                        check_empty(screw, high_plate, "flat head in repair B")
                        check_empty(screw, new, "flat head in integrated B")
                        assert 3.0 <= z - (h - 8) <= 4.0
        support = []
        for side2 in (-1, 1):
            # Measure the actual intersecting bearing area against the original plate.
            patch = side_block(x, side2, 21.65, 23.01, FRONT, BACK, z - 0.04, z + 0.04)
            support.append(
                round(
                    common(repair, clipped(plate.translate((0, 0, -0.025)), patch))
                    / 0.025,
                    2,
                )
            )
        assert min(support) > 22, (tag, support)
        result["plate_capture_mm2"][tag] = support
        root = []
        for sh in (case, new):
            # At each edge measure material continuing across the underside seam.
            areas = []
            for side2 in (-1, 1):
                windows = [
                    side_block(x, side2, 18.5, 28, FRONT, BACK, z - 0.20, z - 0.10),
                    side_block(x, side2, 18.5, 28, FRONT, BACK, z + 0.10, z + 0.20),
                ]
                lower = clipped(sh, windows[0])
                upper = clipped(sh, windows[1])
                if lower and upper:
                    pin = -62.25 if side == -1 else 52.25
                    upper = upper.cut(bore(pin, 279.5, z - 0.3, 14.6, 1))
                    if sh is case and upper:
                        upper = clipped(upper, plate)
                areas.append(
                    round(common(lower.translate((0, 0, 0.30)), upper) / 0.10, 2)
                    if lower and upper
                    else 0.0
                )
            root.append(areas)
        result["roots_mm2"][tag] = {"R01": root[0], "R02": root[1]}
        assert min(root[1]) > 120 and min(root[0]) < 0.1, root
    c["converter_floor"] = check_empty(
        repair, strap_mount(35, 49).translate((-31, 255, 3.4)), "DFRobot base"
    )
    inlet = block(33, 63, 275, 299, 11, 41)
    c["inlet_service_corridor"] = check_empty(repair, inlet, "power inlet")
    c["reinforcement_added_in_inlet_corridor"] = check_empty(
        new.cut(case), inlet, "new material near power inlet"
    )
    for sh in (repair, new):
        check_empty(sh, parts["Entrada_CC_trasera"], "Kycon socket")
    (work / "repair-cad.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2), flush=True)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("work", type=Path)
    main(p.parse_args().work)
