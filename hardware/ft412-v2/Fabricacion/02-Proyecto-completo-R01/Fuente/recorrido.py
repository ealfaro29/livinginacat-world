# /// script
# requires-python = ">=3.12"
# dependencies = ["build123d==0.13.0", "trimesh==5.2.1"]
# ///
"""Check the print revision against the reference hardware at critical travel positions."""

import importlib.util
import json
from itertools import pairwise
from pathlib import Path

import numpy as np
from build123d import Compound, import_step
from geometria import (
    CX,
    SIDES,
    STEP,
    block,
    common,
    fixed_axle,
    moving_bridge,
    optical_arch,
    rear_shell,
    rear_shell_r01,
    strap_mount,
    tool_carriage,
)
from motores import carrier


def bounds(s):
    bb = s.bounding_box()
    return np.array([tuple(bb.min), tuple(bb.max)])


def main():
    asm = import_step(STEP)
    parts = {s.label: s for grp in asm.children for s in grp.children}
    first_batch = (
        Path(__file__).resolve().parents[2] / "01-Frente-y-cama-R01/Fuente/generar.py"
    )
    spec = importlib.util.spec_from_file_location("first_batch", first_batch)
    first = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(first)
    parts["Carcasa_delante"] = first.restore_pi_hooks(parts["Carcasa_delante"])
    parts["Tabique_sobre_electronica"] = first.phone_deck(
        parts["Tabique_sobre_electronica"]
    )
    rear = rear_shell(parts["Carcasa_detras"])
    bridge = moving_bridge(parts["Puente_transversal_nuevo"])
    head = tool_carriage(parts["Carro_portapunta"])
    assert common(bridge, parts["MGN9_X"]) < 0.01
    names = (
        "Carcasa_",
        "Tabique_",
        "Asiento_",
        "Canal_cables",
        "C922_",
        "Capota_",
        "Portico_",
        "NEMA17",
        "Polea_motriz",
        "Polea_frente",
        "Polea_retorno",
        "Eje_motor_",
        "MGN9_Y",
    )
    fixed = {name: s for name, s in parts.items() if name.startswith(names)}
    fixed.update(
        Carcasa_detras=rear,
        Soporte_rescate_R01=carrier(),
        Portico_camara_una_pieza=optical_arch(parts["Portico_camara_una_pieza"]),
    )
    for sign, tag in zip(SIDES, ("I", "D")):
        name = "Asiento_Y_" + tag
        fixed[name] = fixed_axle(parts[name], CX + sign * 57.25, 11.5)
    targets = [(name, shape, bounds(shape)) for name, shape in fixed.items()]
    tested = 0

    def clear(shape, description):
        nonlocal tested
        bb = bounds(shape)
        for name, s, bb2 in targets:
            if np.min(np.minimum(bb[1], bb2[1]) - np.maximum(bb[0], bb2[0])) < 0.001:
                continue
            tested += 1
            v = common(shape, s)
            assert v < 0.015, (description, name, round(v, 4))

    # Include the mechanical ends with a full MGN9H block still on each rail,
    # the operating limits inset 2 mm on each side, and both motor centre lines.
    x_positions = (-55.05, -53.05, -46, -26, 0, 26, 46, 53.05, 55.05)
    y_positions = (-105.05, -103.05, -90, 0, 90, 103.05, 105.05)
    for dy in y_positions:
        clear(bridge.translate((0, dy, 0)), ("bridge", dy))
        for name in ("Patin_Y_I", "Patin_Y_D", "MGN9_X"):
            moving = parts[name].translate((0, dy, 0))
            for mount in (rear, fixed["Soporte_rescate_R01"]):
                assert common(moving, mount) < 0.01, (name, dy, "rear motor support")
        for tag in ("A", "B"):
            for k in (0, 1):
                clear(
                    parts[f"Polea_puente_{tag}_{k}"].translate((0, dy - 9, 0)),
                    ("idler", tag, k, dy),
                )
        for dx in x_positions:
            clear(head.translate((dx, dy, 0)), ("toolhead", dx, dy))
            clear(
                parts["Solenoide_412"].translate((dx - 3.8, dy, 0)),
                ("solenoid", dx, dy),
            )
    # Conservative continuous XY travel over the motor mounts, including
    # hardware heads over the complete +/-2 mm motor-adjustment interval.
    # A box per Z band contains every possible translated tool contour.
    mount_additions = rear.cut(rear_shell_r01(parts["Carcasa_detras"]))
    obstacles = {
        "added shell material": mount_additions,
        "carrier": fixed["Soporte_rescate_R01"],
    }
    for tag, x, z in (("A", -31, 84.3), ("B", 21, 91.3)):
        for dx in (-15.5, 15.5):
            for dy in (-15.5, 15.5):
                diameter = 6.5 if tag == "B" and dy < 0 else 5.7
                bottom = z + 3 if tag == "B" and dy < 0 else z + 5
                top = z + 5 if tag == "B" and dy < 0 else z + 6.65
                obstacles[f"screw {tag} {dx} {dy}"] = block(
                    x + dx - diameter / 2,
                    x + dx + diameter / 2,
                    275 + dy - diameter / 2 - 2,
                    275 + dy + diameter / 2 + 2,
                    bottom,
                    top,
                )
    sweep_count = 0
    for moving in (
        head,
        parts["Solenoide_412"].translate((-3.8, 0, 0)),
        parts["Varilla_y_punta"].translate((-3.8, 0, 0)),
    ):
        bb = moving.bounding_box()
        edges = sorted(
            {bb.min.Z, bb.max.Z}
            | {
                z
                for z in (
                    76,
                    79.45,
                    80,
                    83,
                    86.2,
                    86.65,
                    88,
                    91.3,
                    96.25,
                    96.6,
                    100,
                    101,
                    110,
                    118,
                    130,
                )
                if bb.min.Z < z < bb.max.Z
            }
        )
        for low, high in pairwise(edges):
            region = moving.intersect(
                block(-150, 150, 0, 350, low + 0.0001, high - 0.0001)
            )
            if not region or not region.solids():
                continue
            b = Compound(children=region.solids()).bounding_box()
            envelope = block(
                b.min.X - 55.15,
                b.max.X + 55.15,
                b.min.Y - 105.15,
                b.max.Y + 105.15,
                low,
                high,
            )
            for label, obstacle in obstacles.items():
                assert common(envelope, obstacle) < 0.01, (
                    "continuous travel",
                    label,
                    low,
                    high,
                )
                sweep_count += 1
    # Locate the separate insulating mounts. Their underside adhesive lands
    # touch the floor. A 0.4 mm layer is allocated for mounting tape.
    shelves = [
        ("Geekworm", 58, 47, -43, 94.5),
        ("DFRobot", 35, 49, -31, 255),
        ("fuse", 32, 18, -25, 45),
    ]
    for name, width, length, x, y in shelves:
        sh = strap_mount(width, length).translate((x, y, 3.4))
        clear(sh, name)
        for other in ("MKS_DLC32_V22", "Raspberry_Pi_5", "Caja_Adafruit_5648"):
            assert common(sh, parts[other]) < 0.001, (name, other)
    print(
        json.dumps(
            {
                "x_positions_mm": x_positions,
                "y_positions_mm": y_positions,
                "tip_x_offset_mm": -3.8,
                "moving_idler_y_offset_from_reference_mm": -9,
                "head_positions": len(x_positions) * len(y_positions),
                "continuous_mount_and_fastener_sweep_pairs": sweep_count,
                "rail_and_carrier_positions_per_variant": 3 * len(y_positions),
                "narrow_phase_pairs": tested,
                "collisions_at_checked_positions": 0,
                "scope": "Rigid reference hardware and printed parts at the listed positions; physical belt wrap, cables and heat require assembly.",
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
