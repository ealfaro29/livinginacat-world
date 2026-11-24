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
JOINT_RADIAL_CENTER = -9.0
JOINT_AXIAL_CENTERS = (-8.75, 8.75)
NUT_HALF = 4.3
NUT_CENTER_Z = 3.95
NUT_POCKET_HEIGHT = 4.45
LAP_CLEARANCE_X = 2.4
HARDWARE_FLOAT_X = 2.0
SCREW_SHANK_DIAMETER = 5.65
SCREW_HEAD_CLEARANCE = 10.8

BEAM_HALF_LENGTH = 121.0
BEAM_HEIGHT = 24.0
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


def elongated_passage(plane, diameter, travel, length):
    """Supportable clearance slot. Local X runs along the slot."""
    r = diameter / 2
    tangent = r / sqrt(2)
    slot = plane * SlotOverall(diameter + travel, diameter)
    body = extrude(slot, amount=length, dir=plane.z_dir)
    half = travel / 2
    crown = prism(
        [(-half - tangent, tangent), (half + tangent, tangent),
         (half, r * sqrt(2)), (-half, r * sqrt(2))],
        plane, length,
    )
    return body.fuse(crown).clean()


def side_support(clear_height):
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

    cuts = [lock_bore, access, lock_nut]
    for axial in JOINT_AXIAL_CENTERS:
        opening, stop = sorted(((-DEPTH_HALF-EPS if axial < 0 else DEPTH_HALF+EPS),
                                axial + (NUT_HALF if axial < 0 else -NUT_HALF)))
        cuts.append(block(
            opening, stop, JOINT_RADIAL_CENTER-NUT_HALF, JOINT_RADIAL_CENTER+NUT_HALF,
            clear_height + NUT_CENTER_Z - NUT_POCKET_HEIGHT/2,
            clear_height + NUT_CENTER_Z + NUT_POCKET_HEIGHT/2,
        ))
        origin = (axial, JOINT_RADIAL_CENTER, clear_height-EPS)
        cuts.append(rounded_passage(
            Plane(origin, (0, -1, 0), (0, 0, 1)), SCREW_SHANK_DIAMETER,
            JOINT_THICKNESS + 2*EPS,
        ))
    return body.cut(*cuts).clean(), tabs


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

    # Screw head bearing surface is 16.0 mm above the printed nut's lower edge.
    fastener_x = rail_half_width + JOINT_RADIAL_CENTER
    seat_z = clear_height + 17.8
    for x in (-fastener_x, fastener_x):
        for y in JOINT_AXIAL_CENTERS:
            cuts.append(elongated_passage(
                Plane((x, y, lap_top-EPS), (1, 0, 0), (0, 0, 1)),
                SCREW_SHANK_DIAMETER, 2*HARDWARE_FLOAT_X, top-lap_top+2*EPS,
            ))
            cuts.append(elongated_passage(
                Plane((x, y, seat_z), (1, 0, 0), (0, 0, 1)),
                SCREW_HEAD_CLEARANCE, 2*HARDWARE_FLOAT_X, top-seat_z+EPS,
            ))
    return outer.cut(*cuts).clean()


def locate_right(local, offset):
    return local.rotate(Axis.Z, -90).translate((offset, 0, 0))


def verify_geometry(local, tabs, profile, left, right, beam, height, half_span):
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
    for name, leg, orientation in (("izq", left, -1), ("der", right, 1)):
        checks[f"unión_travesaño_{name}"] = overlap(leg, beam)
        # Coverage of ±2 mm per side on the actual horizontal lap joint.
        for shift in (-HARDWARE_FLOAT_X, HARDWARE_FLOAT_X):
            checks[f"ancho_{name}_{shift:+g}"] = overlap(
                leg.translate((orientation*shift, 0, 0)), beam
            )
        for y in JOINT_AXIAL_CENTERS:
            x = orientation * (half_span + JOINT_RADIAL_CENTER)
            for shift in (-HARDWARE_FLOAT_X, 0, HARDWARE_FLOAT_X):
                bolt = Plane((x+shift, y, height+1.85)) * Cylinder(
                    2.5, 16.0, align=(Align.CENTER, Align.CENTER, Align.MIN)
                )
                checks[f"paso_m5_{name}_{y:+g}_{shift:+g}"] = overlap(beam, bolt)

    # Use the original base in its printed orientation and restore the lid.
    enclosure_base = trimesh.load_mesh(BOX_ROOT / "FT412_Adafruit_5648_Base.stl")
    enclosure_lid = trimesh.load_mesh(BOX_ROOT / "FT412_Adafruit_5648_Tapa.stl")
    enclosure_lid.apply_transform(trimesh.transformations.rotation_matrix(
        3.141592653589793, (1, 0, 0)
    ))
    enclosure_base.apply_translation((BOX_X, 0, height+BEAM_HEIGHT-BOX_SEAT_DEPTH))
    enclosure_lid.apply_translation((BOX_X, 0, height+BEAM_HEIGHT-BOX_SEAT_DEPTH+13.2))
    bounds = trimesh.util.concatenate((enclosure_base, enclosure_lid)).bounds
    bottom = bounds[0][2]
    box_floor = block(BOX_X-BOX_LENGTH/2, BOX_X+BOX_LENGTH/2,
                      -BOX_WIDTH/2, BOX_WIDTH/2, bottom, bottom+1.6)
    collar_floor_envelope = block(BOX_X-BOX_LENGTH_COLLARS/2, BOX_X+BOX_LENGTH_COLLARS/2,
                                  -5.42, 5.42, bottom, bottom+1.6)
    checks["asiento_caja_de_adafruit"] = overlap(box_floor, beam)
    checks["pasacables_caja_de_adafruit"] = overlap(collar_floor_envelope, beam)
    camera_z = height + 12
    for x in (-16, 0, 16):
        camera_screw = Plane((x, -DEPTH_HALF-EPS, camera_z), (1, 0, 0), (0, 1, 0)) * Cylinder(
            6.35/2, 12, align=(Align.CENTER, Align.CENTER, Align.MIN)
        )
        checks[f"ajuste_tornillo_camara_{x:+d}"] = overlap(camera_screw, beam)
    for x in BOX_TIE_CENTERS:
        tie = block(x-2.4, x+2.4, -DEPTH_HALF-EPS, DEPTH_HALF+EPS,
                    height+BEAM_HEIGHT-5.8, height+BEAM_HEIGHT-3.2)
        checks[f"paso_cincho_{x:g}"] = overlap(tie, beam)
    assert max(checks.values()) < 0.01, {k: v for k, v in checks.items() if v >= 0.01}
    enclosure_base.export(ROOT / "qa/caja_base_montada.stl")
    enclosure_lid.export(ROOT / "qa/caja_tapa_montada.stl")
    return checks, capture


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ancho-exterior", type=float, default=230)
    parser.add_argument("--alto-libre", type=float, default=150)
    args = parser.parse_args()
    if not 222 <= args.ancho_exterior <= 238 or not 100 <= args.alto_libre <= 180:
        parser.error("Ancho exterior de 222–238 mm y alto libre de 100–180 mm.")
    (ROOT / "STL").mkdir(exist_ok=True)
    (ROOT / "qa").mkdir(exist_ok=True)

    height = args.alto_libre
    half_span = args.ancho_exterior / 2
    local, tabs = side_support(height)
    right = locate_right(local, half_span)
    left = right.mirror(Plane.YZ)
    beam = crossbar(height, half_span)
    profile = None
    if PROFILE.exists():
        profile = arm03.common.canonical_profile(PROFILE).translate((0, 0, -40))
        checks, capture = verify_geometry(local, tabs, profile, left, right, beam, height, half_span)

    parts = [
        ("01_L_izquierda", "L izquierda", left, -90),
        ("02_L_derecha", "L derecha", right, -90),
        ("03_Travesano_C922_Adafruit", "Travesaño C922 y Adafruit", beam, 90),
    ]
    meshes = {}
    for key, label, solid, rotation in parts:
        path = ROOT / "STL" / f"{key}.stl"
        flat = arm03.common.add_to_bed(solid, Axis.X, rotation)
        meshes[path.name] = arm03.common.verify_mesh(flat, path)
        meshes[path.name]["sha256"] = sha256(path.read_bytes()).hexdigest()
        solid.label = label
        solid.color = Color("#287eaa" if rotation < 0 else "#f0a44b")
        assert export_stl(solid, ROOT / "qa" / f"{key}_montado.stl", tolerance=0.06)

    step = ROOT / "FT412_Marco_Camara_Adafruit_REV01.step"
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
        "captura_al_extraer_hacia_el_costado_mm3": [round(v, 3) for v in capture],
        "stl": meshes,
        "verificacion_fisica": "Pendiente de comprobar entrada, apriete, campo visual y recorrido.",
    }
    (ROOT / "qa/verificacion.json").write_text(json.dumps(report, indent=2, ensure_ascii=False)+"\n")
    print(f"Verificación CAD aprobada para {len(meshes)} piezas y {len(checks)} comprobaciones.")


if __name__ == "__main__":
    main()
