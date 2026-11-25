# /// script
# requires-python = ">=3.12"
# dependencies = ["build123d==0.13.0", "trimesh==5.2.1"]
# ///
"""Check the print revision against the reference hardware at critical travel positions."""

import json
import importlib.util
from pathlib import Path
import numpy as np
from build123d import import_step
from geometria import (
    CX,
    SIDES,
    STEP,
    common,
    fixed_axle,
    moving_bridge,
    optical_arch,
    rear_shell,
    strap_mount,
    tool_carriage,
)


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
                "narrow_phase_pairs": tested,
                "collisions_at_checked_positions": 0,
                "scope": "Rigid reference hardware and printed parts at the listed positions; physical belt wrap, cables and heat require assembly.",
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
