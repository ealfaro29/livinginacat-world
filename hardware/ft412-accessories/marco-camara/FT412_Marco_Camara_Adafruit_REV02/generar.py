# /// script
# requires-python = ">=3.12"
# dependencies = ["build123d==0.13.0", "trimesh==5.2.1"]
# ///
"""Marco superior FT412. En montaje, Z=0 es la cara alta del aluminio."""

import argparse
from hashlib import sha256
import importlib.util
import json
from math import sqrt
from pathlib import Path

from build123d import (
    Align, Axis, Color, Compound, Cylinder, Plane, SlotOverall,
    export_step, export_stl, extrude, import_step,
)
import trimesh


ROOT = Path(__file__).resolve().parent
PRIVATE = ROOT.parents[1]
REFERENCE = PRIVATE / "soportes-modulares"
ARM03 = REFERENCE / "FT412_Soportes_Modulares_REV03"
PROFILE = REFERENCE / "FT412_Soportes_Modulares_REV01/qa/20x40-05.step"
BOX_ROOT = PRIVATE / "print-prep/FT412_Caja_Adafruit_5648_32x20x10"
spec = importlib.util.spec_from_file_location("soporte_rev03", ARM03 / "generar.py")
arm03 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(arm03)
block = arm03.common.block
prism = arm03.common.prism
overlap = arm03.common.overlap

EPS = 0.06
DEPTH_HALF = 17.0
FOOT_REACH = 20.0
LEG_OUTSIDE = 36.0
JOINT_TIP = -22.0
JOINT_THICKNESS = 10.0
NUT_HALF = 4.3
LAP_CLEARANCE_X = 2.4
SCREW_SHANK_DIAMETER = 5.65
SCREW_HEAD_CLEARANCE = 10.8

BEAM_HALF_LENGTH = 121.0
BEAM_HEIGHT = 24.0
BEAM_Y = -5.0
KEY_CENTER = -9.0
KEY_STEM = 5.7
KEY_HEAD = 9.35
KEY_HEIGHT = 5.4
KEY_RAMP_START = 1.65
KEY_RAMP_END = 8.25
KEY_TOP_GAP = 0.35
GUIDE_GAP_LEFT = 0.32
GUIDE_GAP_RIGHT = 2.35
LATCH_STOP_Y = 12.60
LATCH_ENGAGEMENT = 1.20

SLOT_LENGTH = 38.8
SLOT_WIDTH = 6.8
CAMERA_WEB = 3.2
BOX_X = 73.5
BOX_LENGTH = 36.4
BOX_WIDTH = 24.4
BOX_LENGTH_COLLARS = 39.6
BOX_SEAT_DEPTH = 1.1
BOX_TIE_CENTERS = (BOX_X - 7.5, BOX_X + 7.5)


def rounded_passage(plane, diameter, length):
    """Circular clearance with a 45° crown along the layer direction."""
    r = diameter / 2
    tangent = r / sqrt(2)
    disk = plane * Cylinder(r, length, align=(Align.CENTER, Align.CENTER, Align.MIN))
    crown = prism(
        [(-tangent, tangent), (tangent, tangent), (0, r * sqrt(2))],
        plane, length,
    )
    return disk.fuse(crown).clean()


def key_profile(center, lap_top, side_gap=0.0, top_gap=0.0):
    stem = KEY_STEM + side_gap
    head = KEY_HEAD + side_gap
    top = lap_top + KEY_HEIGHT + top_gap
    return [
        (center-stem, lap_top-EPS), (center+stem, lap_top-EPS),
        (center+stem, lap_top+0.55), (center+head, lap_top+3.15),
        (center+head, top), (center-head, top),
        (center-head, lap_top+3.15), (center-stem, lap_top+0.55),
    ]


def guide_key(lap_top):
    # U = -Y in assembly. A ramp on the rear tip grows from the shelf
    # in the first printed layers of the key and guides the beam on entry.
    plane = Plane((-KEY_RAMP_END, 0, 0), (0, 1, 0), (1, 0, 0))
    key = prism(key_profile(KEY_CENTER, lap_top), plane, DEPTH_HALF+KEY_RAMP_END)
    ramp = prism([
        (-DEPTH_HALF-EPS, lap_top-1), (KEY_RAMP_END+EPS, lap_top-1),
        (KEY_RAMP_END+EPS, lap_top-0.04),
        (KEY_RAMP_START, lap_top+KEY_HEIGHT), (-DEPTH_HALF-EPS, lap_top+KEY_HEIGHT),
    ], Plane((0, KEY_CENTER-KEY_HEAD-EPS, 0), (-1, 0, 0), (0, 1, 0)), 2*(KEY_HEAD+EPS))
    return (key & ramp).clean()


def guide_groove(x, lap_top, side_gap):
    # Open towards the front. The terminal ramp is the stop in the assembly direction.
    ramp_end = KEY_RAMP_END+0.64-BEAM_Y
    ramp_start = KEY_RAMP_START+0.55-BEAM_Y
    plane = Plane((x, -DEPTH_HALF-EPS, 0), (-1, 0, 0), (0, 1, 0))
    groove = prism(key_profile(0, lap_top, side_gap, KEY_TOP_GAP), plane,
                   DEPTH_HALF+EPS+ramp_end)
    ramp = prism([
        (-DEPTH_HALF-2*EPS, lap_top-1), (ramp_end, lap_top-1),
        (ramp_end, lap_top-0.03),
        (ramp_start, lap_top+KEY_HEIGHT+KEY_TOP_GAP),
        (-DEPTH_HALF-2*EPS, lap_top+KEY_HEIGHT+KEY_TOP_GAP),
    ], Plane((x-KEY_HEAD-side_gap-EPS, 0, 0), (0, 1, 0), (1, 0, 0)),
        2*(KEY_HEAD+side_gap+EPS))
    return (groove & ramp).clean()


def rear_latch(clear_height, end):
    # The clip is printed flat with the rest of the L. Its locking face is
    # perpendicular to the sliding direction and lies behind the seated beam.
    root = clear_height - 4.5
    plane = Plane((-DEPTH_HALF, 0, 0), (0, 1, 0), (1, 0, 0))
    stem = prism([
        (end+0.85, root), (end+2.85, root), (end+2.85, clear_height+24.6),
        (end+3.75, clear_height+26.5), (end+3.45, clear_height+28.5),
        (end+1.25, clear_height+28.5), (end+0.85, clear_height+27.0),
    ], plane, 8.1)
    tooth = prism([
        (-DEPTH_HALF, end+0.85), (-LATCH_STOP_Y, end-LATCH_ENGAGEMENT),
        (-LATCH_STOP_Y, end+1.45), (-DEPTH_HALF, end+1.45),
    ], Plane((0, 0, clear_height+20.1)), 3.2)
    flex_room = block(-DEPTH_HALF-EPS, -7.6, end-1.3, end+7.3,
                      clear_height-2.6, clear_height+JOINT_THICKNESS+EPS)
    return stem.fuse(tooth).clean(), flex_room


def side_support(clear_height, rail_half_width, latched):
    # Local X runs along the extrusion. Local Y points out of the machine.
    pad = arm03.EXTERIOR_CLEARANCE
    top = clear_height + JOINT_THICKNESS
    profile = [
        (pad, -38), (2.25, -40), (14, -40), (LEG_OUTSIDE, -25),
        (LEG_OUTSIDE, top), (JOINT_TIP, top), (JOINT_TIP, clear_height),
        (2, clear_height), (FOOT_REACH, clear_height - 18),
        (FOOT_REACH, 35), (9, 0), (pad, 0),
    ]
    print_side = Plane((-DEPTH_HALF, 0, 0), (0, 1, 0), (1, 0, 0))
    body = prism(profile, print_side, 2 * DEPTH_HALF)
    tabs = [arm03.rail_tab(z).translate((0, 0, -40)) for z in arm03.SLOT_CENTERS]
    body = body.fuse(*tabs)

    # The M5 pressure screw locks the axial position on the web between slots.
    # Its square nut loads from the end of the printed piece.
    lock_plane = Plane((0, -EPS, -20), (0, 0, 1), (0, 1, 0))
    lock_bore = rounded_passage(lock_plane, SCREW_SHANK_DIAMETER, 11.0)
    access_plane = Plane((0, 10.5, -20), (0, 0, 1), (0, 1, 0))
    access = rounded_passage(access_plane, SCREW_HEAD_CLEARANCE, LEG_OUTSIDE - 10.5 + EPS)
    lock_nut = block(-DEPTH_HALF-EPS, NUT_HALF, 3, 7.45,
                     -20-NUT_HALF, -20+NUT_HALF)

    side = body.cut(lock_bore, access, lock_nut).fuse(guide_key(top)).clean()
    if not latched:
        return side, tabs, None
    latch, relief = rear_latch(clear_height, BEAM_HALF_LENGTH-rail_half_width)
    return side.cut(relief).fuse(latch).clean(), tabs, latch


def crossbar(clear_height, rail_half_width):
    top = clear_height + BEAM_HEIGHT
    lap_top = clear_height + JOINT_THICKNESS
    shoulder = rail_half_width + JOINT_TIP - LAP_CLEARANCE_X
    outline = [
        (-BEAM_HALF_LENGTH, lap_top), (-shoulder, lap_top),
        (-shoulder + 5.0, clear_height), (shoulder - 5.0, clear_height),
        (shoulder, lap_top), (BEAM_HALF_LENGTH, lap_top),
        (BEAM_HALF_LENGTH, top), (-BEAM_HALF_LENGTH, top),
    ]
    beam_plane = Plane((0, DEPTH_HALF, 0), (1, 0, 0), (0, -1, 0))
    outer = prism(outline, beam_plane, 2 * DEPTH_HALF)

    # The C922 is turned down with the underside of its clip against the front.
    # The back pocket gives access to the head of a short photographic screw.
    camera_z = clear_height + 12.0
    front = Plane((0, -DEPTH_HALF-EPS, camera_z), (-1, 0, 0), (0, 1, 0))
    camera_slot = extrude(front * SlotOverall(SLOT_LENGTH, SLOT_WIDTH),
                          amount=CAMERA_WEB+2*EPS, dir=(0, 1, 0))
    rear = block(-32, 32, -DEPTH_HALF+CAMERA_WEB, DEPTH_HALF+EPS,
                 clear_height+3.5, top-3.5)
    cuts = [camera_slot, rear]
    for x in (-24.5, 24.5):
        cuts.append(block(x-2.9, x+2.9, -DEPTH_HALF-EPS, -DEPTH_HALF+CAMERA_WEB+EPS,
                          camera_z-1.75, camera_z+1.75))

    # Tray locates the existing case without changing its lid or cable collars.
    cuts.append(block(BOX_X-BOX_LENGTH/2-0.35, BOX_X+BOX_LENGTH/2+0.35,
                      -BOX_WIDTH/2-0.35, BOX_WIDTH/2+0.35, top-BOX_SEAT_DEPTH, top+EPS))
    cuts.append(block(BOX_X-BOX_LENGTH_COLLARS/2-2.0, BOX_X+BOX_LENGTH_COLLARS/2+2.0,
                      -5.8, 5.8, top-BOX_SEAT_DEPTH, top+EPS))
    for x in BOX_TIE_CENTERS:
        cuts.append(block(x-2.85, x+2.85, -DEPTH_HALF-EPS, DEPTH_HALF+EPS,
                          top-6.2, top-2.8))

    guide_x = rail_half_width + KEY_CENTER
    cuts.extend((guide_groove(-guide_x, lap_top, GUIDE_GAP_LEFT),
                 guide_groove(guide_x, lap_top, GUIDE_GAP_RIGHT)))
    return outer.cut(*cuts).translate((0, BEAM_Y, 0)).clean()


def locate_right(local, offset):
    return local.rotate(Axis.Z, -90).translate((offset, 0, 0))


def verify_geometry(local, tabs, profile, left, right, beam, latch, height, half_span):
    checks = {}
    for offset in (-81, -60, -43, 0, 43, 60, 81):
        checks[f"entrada_pestañas_axial_{offset:+d}"] = overlap(
            local.translate((offset, 0, 0)), profile
        )
    checks["apoyo_sobre_perfil_amarrado"] = overlap(
        local.translate((0, -arm03.EXTERIOR_CLEARANCE, 0)), profile
    )
    capture = [overlap(tab.translate((0, 1.2, 0)), profile) for tab in tabs]
    assert min(capture) > 1.0, capture
    plain_left = right.mirror(Plane.YZ)
    checks["encastre_izquierdo_con_seguro"] = overlap(left, beam)
    checks["encastre_derecho"] = overlap(right, beam)
    for dx in (-2, 0, 2):
        right_shifted = right.translate((dx, 0, 0))
        for dy in (0, 1, 5, 12, 23, 34):
            displaced = beam.translate((0, dy, 0))
            right_overlap = overlap(right_shifted, displaced)
            checks[f"deslizamiento_derecho_dx{dx:+d}_dy{dy}"] = right_overlap
            if dx == 0:
                checks[f"deslizamiento_izquierdo_dy{dy}"] = overlap(plain_left, displaced)
    catch_at_left = beam.translate((0, 1.5, 0))
    stops = {
        "no_sale_arriba_izq": overlap(left, beam.translate((0, 0, 1.9))),
        "no_sale_arriba_der": overlap(right, beam.translate((0, 0, 1.9))),
        "no_desliza_hacia_atras_con_seguro": overlap(left, catch_at_left),
        "tope_hacia_adelante_izq": overlap(left, beam.translate((0, -1.6, 0))),
        "tope_hacia_adelante_der": overlap(right, beam.translate((0, -1.6, 0))),
    }
    assert min(stops.values()) > 0.7, stops
    # Check the free end of the hook in two positions. The rotation is a
    # clearance proxy for the flexure, not a structural simulation.
    end = BEAM_HALF_LENGTH-half_span
    hook = latch & block(-18, -8, end-2, end+5, height+19, height+29)
    hinge = Axis((0, end+1.85, height-2.6), (1, 0, 0))
    open_hook = locate_right(hook.rotate(hinge, -4.2), half_span).mirror(Plane.YZ)
    for dy in (1, 3, 8, 16, 32):
        checks[f"seguro_abierto_dy{dy}"] = overlap(open_hook, beam.translate((0, dy, 0)))

    # Use the original base in its printed orientation and restore the lid.
    enclosure_base = trimesh.load_mesh(BOX_ROOT / "FT412_Adafruit_5648_Base.stl")
    enclosure_lid = trimesh.load_mesh(BOX_ROOT / "FT412_Adafruit_5648_Tapa.stl")
    enclosure_lid.apply_transform(trimesh.transformations.rotation_matrix(
        3.141592653589793, (1, 0, 0)
    ))
    enclosure_base.apply_translation((BOX_X, BEAM_Y, height+BEAM_HEIGHT-BOX_SEAT_DEPTH))
    enclosure_lid.apply_translation((BOX_X, BEAM_Y, height+BEAM_HEIGHT-BOX_SEAT_DEPTH+13.2))
    bounds = trimesh.util.concatenate((enclosure_base, enclosure_lid)).bounds
    bottom = bounds[0][2]
    box_floor = block(BOX_X-BOX_LENGTH/2, BOX_X+BOX_LENGTH/2,
                      BEAM_Y-BOX_WIDTH/2, BEAM_Y+BOX_WIDTH/2, bottom, bottom+1.6)
    collar_floor_envelope = block(BOX_X-BOX_LENGTH_COLLARS/2, BOX_X+BOX_LENGTH_COLLARS/2,
                                  BEAM_Y-5.42, BEAM_Y+5.42, bottom, bottom+1.6)
    checks["asiento_caja_de_adafruit"] = overlap(box_floor, beam)
    checks["pasacables_caja_de_adafruit"] = overlap(collar_floor_envelope, beam)
    camera_z = height + 12
    for x in (-16, 0, 16):
        camera_screw = Plane((x, BEAM_Y-DEPTH_HALF-EPS, camera_z), (1, 0, 0), (0, 1, 0)) * Cylinder(
            6.35/2, 12, align=(Align.CENTER, Align.CENTER, Align.MIN)
        )
        checks[f"ajuste_tornillo_camara_{x:+d}"] = overlap(camera_screw, beam)
    for x in BOX_TIE_CENTERS:
        tie = block(x-2.4, x+2.4, BEAM_Y-DEPTH_HALF-EPS, BEAM_Y+DEPTH_HALF+EPS,
                    height+BEAM_HEIGHT-5.8, height+BEAM_HEIGHT-3.2)
        checks[f"paso_cincho_{x:g}"] = overlap(tie, beam)
    assert max(checks.values()) < 0.01, {k: v for k, v in checks.items() if v >= 0.01}
    enclosure_base.export(ROOT / "qa/caja_base_montada.stl")
    enclosure_lid.export(ROOT / "qa/caja_tapa_montada.stl")
    return checks, capture, stops


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ancho-exterior", type=float, default=230)
    parser.add_argument("--alto-libre", type=float, default=150)
    args = parser.parse_args()
    if not 224 <= args.ancho_exterior <= 236 or not 100 <= args.alto_libre <= 180:
        parser.error("Ancho exterior de 224–236 mm y alto libre de 100–180 mm.")
    (ROOT / "STL").mkdir(exist_ok=True)
    (ROOT / "qa").mkdir(exist_ok=True)

    height = args.alto_libre
    half_span = args.ancho_exterior / 2
    local, tabs, _ = side_support(height, half_span, False)
    latched_side, _, latch = side_support(height, half_span, True)
    right = locate_right(local, half_span)
    left = locate_right(latched_side, half_span).mirror(Plane.YZ)
    beam = crossbar(height, half_span)
    profile = None
    if PROFILE.exists():
        profile = arm03.common.canonical_profile(PROFILE).translate((0, 0, -40))
        checks, capture, stops = verify_geometry(local, tabs, profile, left, right, beam,
                                                 latch, height, half_span)

    parts = [
        ("01_L_izquierda", "L izquierda con seguro", left, -90),
        ("02_L_derecha", "L derecha", right, -90),
        ("03_Travesano_C922_Adafruit", "Travesaño C922 y Adafruit", beam, 90),
    ]
    meshes = {}
    for key, label, solid, rotation in parts:
        path = ROOT / "STL" / f"{key}.stl"
        flat = solid.rotate(Axis.X, rotation)
        flat = arm03.common.add_to_bed(flat, Axis.Z, 90 if rotation < 0 else 0)
        meshes[path.name] = arm03.common.verify_mesh(flat, path)
        meshes[path.name]["sha256"] = sha256(path.read_bytes()).hexdigest()
        solid.label = label
        solid.color = Color("#287eaa" if rotation < 0 else "#f0a44b")
        assert export_stl(solid, ROOT / "qa" / f"{key}_montado.stl", tolerance=0.06)

    step = ROOT / "FT412_Marco_Camara_Adafruit_REV02.step"
    assert export_step(Compound(children=[left, right, beam]), step)
    reloaded_solids = import_step(step).solids()
    assert len(reloaded_solids) == 3 and all(s.is_valid for s in reloaded_solids)
    if profile is None:
        return
    right_profile = locate_right(profile, half_span)
    left_profile = right_profile.mirror(Plane.YZ)
    assert export_stl(right_profile, ROOT / "qa/perfil_derecho.stl", tolerance=0.1)
    assert export_stl(left_profile, ROOT / "qa/perfil_izquierdo.stl", tolerance=0.1)
    report = {
        "ancho_exterior_entre_caras_de_aluminio_mm": args.ancho_exterior,
        "altura_bajo_travesano_desde_aluminio_mm": height,
        "vuelo_de_la_pata_mm": FOOT_REACH,
        "ancho_total_ensamblado_mm": args.ancho_exterior+2*LEG_OUTSIDE,
        "largo_de_travesano_mm": 2*BEAM_HALF_LENGTH,
        "solidos_STEP": len(reloaded_solids),
        "caja_envolvente_mm": [BOX_LENGTH_COLLARS, BOX_WIDTH, 13.2],
        "solape_digital_mm3": {k: round(v, 5) for k, v in checks.items()},
        "interferencias_positivas_de_retencion_mm3": {k: round(v, 3) for k, v in stops.items()},
        "travesaño": "dos colas de milano y seguro flexible integrado en la L izquierda",
        "desplazamiento_en_profundidad_del_travesaño_mm": BEAM_Y,
        "variación_comprobada_de_ancho_mm": [-2, 2],
        "captura_al_extraer_hacia_el_costado_mm3": [round(v, 3) for v in capture],
        "stl": meshes,
        "verificacion_fisica": "Pendiente de comprobar entrada, apriete, campo visual y recorrido.",
    }
    (ROOT / "qa/verificacion.json").write_text(json.dumps(report, indent=2, ensure_ascii=False)+"\n")
    print(f"Verificación CAD aprobada para {len(meshes)} piezas y {len(checks)} comprobaciones.")


if __name__ == "__main__":
    main()
