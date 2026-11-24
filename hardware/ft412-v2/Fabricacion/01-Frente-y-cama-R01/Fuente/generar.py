# /// script
# requires-python = ">=3.12"
# dependencies = ["build123d==0.13.0", "trimesh==5.2.1"]
# ///
"""Generate the two V2 R01 bench parts from the named bodies of the reference STEP."""
import argparse
import hashlib
import json
from itertools import product
from pathlib import Path

import trimesh
from build123d import (Align, Box, Cylinder, Plane, Polygon, Pos, RectangleRounded,
                      export_step, export_stl, extrude, import_step)

OUT = Path(__file__).resolve().parent.parent
DEFAULT_STEP = OUT.parents[1] / "Consola-tornilleria" / "FT412-V2.step"
REFERENCE_SHA = "362b71880a2ef7e8eed44361729774c055c95f51518e1a5895e9b0351b1de580"
DECK = "01_Cama_iPhone14"
FRONT = "02_Frente_consola"
CX, CY = -5.0, 138.0
BACK_Z, GLASS_Z = 47.2, 55.0
PHONE_W, PHONE_L = 71.52, 146.71
HALF_W, HALF_L = PHONE_W / 2, PHONE_L / 2
PLAY = 0.30


def box(x1, x2, y1, y2, z1, z2):
    return Pos(x1, y1, z1) * Box(x2-x1, y2-y1, z2-z1, align=(Align.MIN,)*3)


def rounded(x, y, w, d, r, z1, z2):
    return Pos(x, y, z1) * extrude(RectangleRounded(w, d, r), amount=z2-z1)


def intersection_mm3(a, b):
    common = a.intersect(b)
    return sum(s.volume for s in common.solids()) if common is not None else 0.0


def restore_pi_hooks(front):
    # The concept split trimmed all Pi features at Z=11. Restore the original
    # lip sections while leaving the board datum and the lower half untouched.
    additions = []
    # The old carrier left sealed drill pockets under its two molded pins.
    # Fill them so the printer lays a solid column under each locating pin.
    for x in (14.5, 63.5):
        additions.append(Pos(x, 79, 3.95) * Cylinder(1.32, 2.32,
                         align=(Align.CENTER, Align.CENTER, Align.MIN)))
    for x in (19.0, 58.0):
        additions.append(box(x-2.3, x+2.3, 73.65, 75.05, 10.0, 11.7))
        additions.append(box(x-2.3, x+2.3, 74.6, 76.55, 10.85, 12.05))
    for side in (-1, 1):
        edge = 39 + side*28
        points = [(edge+side*u, z) for u, z in
                  [(.35, 9.8), (1.7, 9.8), (1.7, 11.8), (.35, 12.8),
                   (-.75, 11.5), (-.75, 10.85), (.35, 10.85)]]
        plane = Plane((0, 119.5, 0), (1, 0, 0), (0, -1, 0))
        additions.append(extrude(plane * Polygon(*points, align=None), amount=6, dir=(0, 1, 0)))
    return front.fuse(*additions).clean()


def phone_deck(deck):
    # Fill the concept's 0.4 mm underside gap so the tray has a continuous
    # bed-facing surface. Its new seating face sets the naked phone glass at Z=55.
    bed = rounded(CX, CY, 82, 156, 10, 44, 46.5)
    seat = rounded(CX, CY, 73.6, 148.8, 8, 46.35, BACK_Z)
    window_x, window_y = CX+HALF_W+.6-20, CY+HALF_L+.6-20
    camera_opening = rounded(window_x, window_y, 40, 40, 3, 42, 54)
    lightning_opening = rounded(CX, 55, 18, 22, 2, 42, 54)
    # The concept's cropped service opening left a 1 × 46 mm unsupported
    # sliver beside the switch wires. Open this edge up to the existing notch.
    cable_edge = box(58.9, 61, 32.9, 79, 43, 54)
    deck = deck.fuse(bed, seat).cut(camera_opening, lightning_opening, cable_edge)
    # Side openings clear the buttons. The short locating pads bear on the
    # phone frame away from them and leave 0.30 mm per side at nominal size.
    deck = deck.cut(box(-48, -39, 143, 189, BACK_Z, 54),
                    box(29, 38, 146, 169.5, BACK_Z, 54))
    stops = []
    for side in (-1, 1):
        x = CX + side*(HALF_W + PLAY + 1.4)
        for offset in (-45, 58):
            stops.append(rounded(x, CY+offset, 2.8, 11, .85, 46.6, 50.8))
        y = CY + side*(HALF_L + PLAY + 1.4)
        for offset in (-19, 16):
            stops.append(rounded(CX+offset, y, 10, 2.8, .85, 46.6, 50.8))
    return deck.fuse(*stops).clean()


def validate(deck, front, parts, groups):
    checks = {}
    def clear(label, a, b):
        v = intersection_mm3(a, b)
        assert v < .002, (label, v)
        checks[label] = round(v, 6)

    clear("deck/front", deck, front)
    for name in ("Carcasa_detras", "Asiento_Y_I", "Asiento_Y_D", "Ventilador_CanaKit",
                 "Disipador_CanaKit", "MKS_DLC32_V22", "Reserva_convertidor_CC"):
        clear("deck/"+name, deck, parts[name])
    for name in ("Carcasa_detras", "Raspberry_Pi_5", "Vidrio_TS24_62x45",
                 "PCB_pantalla_TS24", "S301T_cuerpo", "S301T_casquillo_M12",
                 "Asiento_Y_I", "Asiento_Y_D"):
        clear("front/"+name, front, parts[name])
    # Verify four contact areas at the same Z instead of just checking a bounding box.
    for x, y in ((-25, -46), (23, -46), (-25, 38), (7, 25)):
        pad = box(CX+x-2, CX+x+2, CY+y-2, CY+y+2, BACK_Z-.12, BACK_Z)
        assert intersection_mm3(deck, pad) > pad.volume-.0001
    phone = rounded(CX, CY, PHONE_W, PHONE_L, 9, BACK_Z, GLASS_Z)
    clear("deck/phone_nominal", deck, phone)
    # Apple drawing sheet 1 detail D. A rounded, oversized keep-out encloses
    # the plateau and both lenses at their full 3.42 mm projection, with 0.3 mm
    # additional depth. The outer extent is conservatively 1.0..36.0 mm inward.
    camera = rounded(CX+HALF_W-18.5, CY+HALF_L-18.5, 35, 35, 3, BACK_Z-3.72, BACK_Z+.01)
    for x, y in product((-PLAY, PLAY), repeat=2):
        clear(f"deck/camera_max_{x}_{y}", deck, camera.translate((x, y, 0)))
    clear("deck/lightning", deck, box(CX-7, CX+7, CY-HALF_L-14, CY-HALF_L, 47.7, 54.55))
    clear("deck/left_buttons", deck, box(CX-HALF_W-.75, CX-HALF_W+.1, 146, 184, 48.5, 53.5))
    clear("deck/right_button", deck, box(CX+HALF_W-.1, CX+HALF_W+.75, 150, 166, 48.5, 53.5))
    clear("deck/switch_wire_access", deck, box(59.01, 60.01, 33.1, 78.9, 43.5, 47))
    for name, group in groups.items():
        if group == "electronics" or group == "harness":
            clear("camera_below_deck/"+name, camera, parts[name])
    for x in (19., 58.):
        lip = box(x-1, x+1, 75.6, 76.4, 11.1, 11.6)
        assert intersection_mm3(front, lip) > lip.volume-.0001
    for x in (11., 67.):
        lip = box(x-.1, x+.1, 121, 124, 10.95, 11.2)
        assert intersection_mm3(front, lip) > lip.volume-.0001
    # All changes are below the lowest retracted moving element at any XY.
    original_deck, original_front = parts["Tabique_sobre_electronica"], parts["Carcasa_delante"]
    change_ceiling = max(s.bounding_box().max.Z for a, b in ((front,original_front),(deck,original_deck))
                         for s in a.cut(b).solids())
    moving_min = min(parts[n].bounding_box().min.Z for n, g in groups.items()
                     if g in ("movingX", "movingY", "herrajesX", "herrajesY"))
    assert moving_min-change_ceiling > 5
    return {"intersections_mm3": checks, "added_material_z_max_mm": round(change_ceiling, 3),
            "retracted_moving_parts_z_min_mm": round(moving_min, 3),
            "glass_datum_mm": GLASS_Z, "back_seat_mm": BACK_Z, "xy_nominal_play_per_side_mm": PLAY,
            "camera_window_mm": [40, 40], "tested_camera_projection_mm": 3.72}


def write_part(name, shape):
    assert len(shape.solids()) == 1 and shape.is_valid
    bounds = shape.bounding_box()
    oriented = shape.translate((-bounds.center().X, -bounds.center().Y, -bounds.min.Z))
    oriented.label = name
    prefix = OUT / "Piezas" / name
    assert export_step(oriented, prefix.with_suffix(".step"))
    assert export_stl(oriented, prefix.with_suffix(".stl"), tolerance=.025, angular_tolerance=.08)
    m = trimesh.load_mesh(prefix.with_suffix(".stl"))
    assert m.is_watertight and m.is_winding_consistent and m.is_volume and m.body_count == 1
    assert min(m.area_faces) > 0 and abs(m.bounds[0, 2]) < 1e-4
    assert abs(m.volume-oriented.volume)/oriented.volume < .001
    return {"dimensions_mm": m.extents.round(3).tolist(), "triangles": len(m.faces),
            "solid_volume_mm3": round(oriented.volume, 3),
            "one_watertight_solid": True,
            "stl_sha256": hashlib.sha256(prefix.with_suffix(".stl").read_bytes()).hexdigest()}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("step", nargs="?", type=Path, default=DEFAULT_STEP)
    source = parser.parse_args().step
    assert hashlib.sha256(source.read_bytes()).hexdigest() == REFERENCE_SHA, "Reference STEP differs"
    assembly = import_step(source)
    parts = {obj.label: obj for group in assembly.children for obj in group.children}
    groups = {obj.label: group.label for group in assembly.children for obj in group.children}
    front, deck = restore_pi_hooks(parts["Carcasa_delante"]), phone_deck(parts["Tabique_sobre_electronica"])
    report = validate(deck, front, parts, groups)
    report.update({"parent_step_sha256": REFERENCE_SHA, "parts": {DECK: write_part(DECK, deck),
                   FRONT: write_part(FRONT, front)}, "physical_fit_verified": False,
                   "apple_drawing": "https://developer.apple.com/download/files/accessories/dimensional-drawings/iphone-14.pdf"})
    (OUT/"QA"/"geometria.json").write_text(json.dumps(report, indent=2)+"\n")
    print(json.dumps(report["parts"], indent=2), flush=True)


if __name__ == "__main__":
    main()
