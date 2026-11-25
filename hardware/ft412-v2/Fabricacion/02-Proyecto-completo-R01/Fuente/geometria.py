# /// script
# requires-python = ">=3.12"
# dependencies = ["build123d==0.13.0", "trimesh==5.2.1", "lxml>=5,<7"]
# ///
"""Produce closed printing meshes in the orientation specified by the release manifest."""

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import trimesh
from build123d import Align, Box, Cylinder, Plane, Pos, export_stl, import_step
from scipy.spatial.transform import Rotation

HERE = Path(__file__).resolve().parents[1]
HARDWARE = HERE.parents[2]
V2 = HARDWARE / "ft412-v2"
STEP = V2 / "Consola-tornilleria/FT412-V2.step"
SOURCE_SHA = "362b71880a2ef7e8eed44361729774c055c95f51518e1a5895e9b0351b1de580"
CX, CY = -5.0, 138.0
SIDES = (-1, 1)


def block(x0, x1, y0, y1, z0, z1):
    return Pos(x0, y0, z0) * Box(x1 - x0, y1 - y0, z1 - z0, align=(Align.MIN,) * 3)


def bore(x, y, z, dia, length, axis=(0, 0, 1)):
    return Plane(origin=(x, y, z), z_dir=axis).location * Cylinder(
        dia / 2, length, align=(Align.CENTER, Align.CENTER, Align.MIN)
    )


def common(a, b):
    result = a.intersect(b)
    return sum(s.volume for s in result.solids()) if result is not None else 0.0


def fixed_axle(part, x, y):
    # A metal M5 nut is fed from the side. The axle bears on the metal inner races.
    boss = bore(x, y, 90.4, 13.6, 11.4)
    return part.fuse(boss).cut(
        bore(x, y, 89.8, 5.4, 12.4),
        block(x - 4.22, x + 4.22, y - 4.95, y + 7, 93.5, 97.9),
    )


def moving_bridge(part):
    for sign in SIDES:
        x, y = CX + sign * 57.25, CY + 9.0
        part = part.cut(block(x - 5.2, x + 5.2, CY + 11.5, CY + 24.1, 116.9, 119.5))
        boss = block(x - 6.2, x + 6.2, y - 6, y + 5, 117, 126.0)
        part = part.fuse(boss).cut(
            bore(x, y, 116.7, 5.4, 10.3),
            block(x - 4.22, x + 4.22, y - 9, y + 4.95, 120.0, 124.4),
        )
        assert common(part, bore(x, y, 116.9, 5.25, 9.9)) < 0.0001
    return part.clean()


def rear_shell(part):
    # Panel mounting from the inside. 12 mm face aperture, two separate M2.5
    # screw clearances on the manufacturer's 19 mm vertical pitch.
    # Recess the exterior locally so only 1.6 mm of panel separates the plug
    # from the socket face. Leave the surrounding 3 mm rear wall intact.
    part = part.cut(block(33, 63, 300.6, 302.1, 11, 41))
    for z in (16.5, 35.5):
        part = part.cut(bore(48, 298.8, z, 2.85, 3.6, (0, 1, 0)))
    for sign in SIDES:
        part = fixed_axle(part, CX + sign * 57.25, 279.5)
        # Move each complete motor on four matching slots, including the pilot.
        x = CX + sign * 26
        top = 89.3 if sign < 0 else 96.3
        for dx, dy, diameter in [(0.0, 0.0, 23.0)] + [
            (u, v, 3.55) for u in (-15.5, 15.5) for v in (-15.5, 15.5)
        ]:
            xx, yy = x + dx, 275 + dy
            length = 2.0
            cuts = [
                bore(xx, yy + off, top - 5.15, diameter, 5.4)
                for off in (-length, length)
            ]
            cuts.append(
                block(
                    xx - diameter / 2,
                    xx + diameter / 2,
                    yy - length,
                    yy + length,
                    top - 5.15,
                    top + 0.25,
                )
            )
            part = part.cut(*cuts)
    return part.clean()


def tool_carriage(part):
    # The bottom support runs below both pulley stacks. Locate the #412 on its
    # shelf and retain its metal body to the spine with two 2.5 mm cable ties.
    # Bias the actuator 3.8 mm left so the near belt terminal clears its coil.
    # Keep all four X-block screws in their original positions.
    tip_x = CX - 3.8
    lower = (
        part.intersect(block(-60, 60, 100, 180, 79, 140.4))
        .solids()[0]
        .translate((-3.8, 0, 0))
    )
    upper = part.intersect(block(-60, 60, 100, 180, 140.35, 147)).solids()[0]
    part = upper.fuse(lower, block(tip_x - 5, CX + 5, CY - 13, CY - 9, 136, 143.5))
    shelf = block(tip_x - 9, tip_x + 9, CY - 10, CY + 9.7, 80.0, 83.0)
    part = part.fuse(shelf).cut(bore(tip_x, CY, 79.9, 8.0, 3.2))
    for sign in SIDES:
        x1, x2 = sorted((tip_x + sign * 7.85, tip_x + sign * 9.0))
        part = part.fuse(block(x1, x2, CY - 8, CY + 8, 82.7, 86.2))
    for z in (90.0, 105.0):
        part = part.cut(
            block(tip_x - 5.2, tip_x + 5.2, CY - 13.2, CY - 12.15, z - 1.5, z + 1.5)
        )
    # Both 6 mm belts fold around the posts outside the idlers' sweep.
    arm = block(CX + 6.45, CX + 10.4, CY - 12.8, CY + 21.55, 96.6, 100.0)
    arm = arm.fuse(block(CX + 0.25, CX + 10.4, CY - 13, CY - 9.1, 96.6, 100.0))
    for xx, yy in ((CX + 7.65, CY - 1.05), (CX, CY + 19.05)):
        arm = arm.fuse(
            block(xx - 2.35, CX + 10.4, yy - 2.5, yy + 2.5, 96.6, 100.0),
            bore(xx, yy, 99.8, 4.7, 17.6),
            bore(xx, yy, 117.25, 6.1, 1.15),
        )
    return part.fuse(arm).clean()


def optical_arch(part):
    # Coplanar rear flanges form a stable first layer when the arch is laid on
    # its back. They stay within the original external envelope.
    for sign in SIDES:
        x0, x1 = sorted((95.1 * sign, 97.95 * sign))
        part = part.fuse(block(x0, x1, 209.9, 216, 58.2, 198.7))
    return part.fuse(block(-96.7, 96.7, 205.6, 216, 190, 197)).clean()


def strap_mount(width, length):
    # Flat adhesive lands below two raised skids. Transverse strap tunnels
    # allow a PCB edge or an existing insulated stand to be retained.
    base = block(-width / 2, width / 2, -length / 2, length / 2, 0, 2)
    for side in SIDES:
        x = side * (width / 2 - 3)
        rail = block(x - 2.0, x + 2.0, -length / 2, length / 2, 1.8, 4.8)
        base = base.fuse(rail)
    for side in SIDES:
        y = side * (length / 2 - 6.5)
        for edge in SIDES:
            x = edge * (width / 2 - 3)
            # Thread the strap across the flat underside in its own recess.
            base = base.cut(block(x - 2.25, x + 2.25, y - 1.8, y + 1.8, -0.1, 5))
        base = base.cut(
            block(-width / 2 + 3.1, width / 2 - 3.1, y - 1.8, y + 1.8, -0.1, 1.0)
        )
    if length >= 30:
        base = base.cut(
            block(
                -width / 2 + 7,
                width / 2 - 7,
                -length / 2 + 10,
                length / 2 - 10,
                -0.1,
                2.1,
            )
        )
    return base.clean()


def load_meshes(work, layout):
    if hashlib.sha256(STEP.read_bytes()).hexdigest() != SOURCE_SHA:
        raise ValueError("Unexpected assembly STEP")
    asm = import_step(STEP)
    parts = {s.label: s for g in asm.children for s in g.children}
    changed = {}
    for name, fn in [
        ("Carcasa_detras", rear_shell),
        ("Puente_transversal_nuevo", moving_bridge),
        ("Carro_portapunta", tool_carriage),
        ("Portico_camara_una_pieza", optical_arch),
    ]:
        changed[name] = fn(parts[name])
    for tag, sign in zip(("I", "D"), SIDES):
        name = "Asiento_Y_" + tag
        changed[name] = fixed_axle(parts[name], CX + sign * 57.25, 11.5).clean()
    specials = {
        name: strap_mount(width, length)
        for name, width, length in [
            ("Geekworm", 58, 47),
            ("DFRobot", 35, 49),
            ("Fusible", 32, 18),
        ]
    }
    assert all(
        s.is_valid and len(s.solids()) == 1
        for s in (*changed.values(), *specials.values())
    )
    # Check the new inlet, all six shaft drillings and the revised gantry.
    rear = changed["Carcasa_detras"]
    assert all(
        common(rear, bore(48, 298.8, z, diam, 3.6, (0, 1, 0))) < 0.0001
        for z, diam in [(26, 11.95), (16.5, 2.75), (35.5, 2.75)]
    )
    assert common(rear, parts["MKS_DLC32_V22"]) < 0.001
    assert common(changed["Portico_camara_una_pieza"], rear) < 0.001
    for sign, tag in zip(SIDES, ("I", "D")):
        x = CX + sign * 57.25
        for shape, y in ((changed["Asiento_Y_" + tag], 11.5), (rear, 279.5)):
            assert common(shape, bore(x, y, 92.0, 5.25, 10.0)) < 0.0001
    # Validate the added folded-belt supports, including their tips at the
    # closest possible X offset to either travelling pulley. The bridge,
    # bearings and toolhead move together in Y.
    tool = changed["Carro_portapunta"]
    assert common(tool, parts["Solenoide_412"].translate((-3.8, 0, 0))) < 0.001
    for off in (-55.05, -53.05, 0, 53.05, 55.05):
        head = tool.translate((off, 0, 0))
        for n in (
            "Puente_transversal_nuevo",
            "MGN9_X",
            "Polea_puente_A_0",
            "Polea_puente_A_1",
            "Polea_puente_B_0",
            "Polea_puente_B_1",
            "Patin_Y_I",
            "Patin_Y_D",
        ):
            target = changed[n] if n in changed else parts[n]
            if n.startswith("Polea_puente_"):
                target = target.translate((0, -9, 0))
            overlap = common(head, target)
            assert overlap < 0.005, (off, n, overlap)
    for row in layout:
        name = row["name"]
        if "stl" in row:
            source = HARDWARE / row["stl"]
            if hashlib.sha256(source.read_bytes()).hexdigest() != row["sha256"]:
                raise ValueError("Unexpected mesh: " + name)
        else:
            label = row["body"]
            if label in changed:
                shape = changed[label]
            elif label in specials:
                shape = specials[label]
            else:
                shape = parts[label]
            assert len(shape.solids()) == 1 and shape.is_valid, label
            source = work / (name + "-cad.stl")
            export_stl(shape, source, tolerance=0.025, angular_tolerance=0.085)
        mesh = trimesh.load_mesh(source)
        assert mesh.is_volume and mesh.is_watertight and mesh.is_winding_consistent, (
            name
        )
        # A closed internal cavity is a negative shell, not a second printed object.
        shells = mesh.split(only_watertight=False)
        assert sum(c.volume > 0 for c in shells) == 1 and all(
            c.is_watertight for c in shells
        ), name
        if any(row["rotation"]):
            transform = np.eye(4)
            transform[:3, :3] = Rotation.from_euler(
                "xyz", row["rotation"], degrees=True
            ).as_matrix()
            mesh.apply_transform(transform)
        lo, hi = mesh.bounds
        mesh.apply_translation([-(lo[0] + hi[0]) / 2, -(lo[1] + hi[1]) / 2, -lo[2]])
        mesh.export(work / (name + ".stl"))
        print(name, np.round(mesh.extents, 2).tolist(), flush=True)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("work", type=Path)
    args = p.parse_args()
    args.work.mkdir(parents=True, exist_ok=True)
    load_meshes(args.work, json.loads((HERE / "placas.json").read_text())["objects"])
