# /// script
# requires-python = ">=3.12"
# dependencies = ["build123d==0.13.0", "trimesh==5.2.1"]
# ///
"""FT412. One-piece arm that slides onto two slots from the extrusion end."""

import argparse
from hashlib import sha256
import importlib.util
import json
from pathlib import Path

from build123d import Axis, Color, Compound, Plane, export_step, export_stl, import_step

ROOT = Path(__file__).resolve().parent
REFERENCE = ROOT.with_name("FT412_Soportes_Modulares_REV01")
spec = importlib.util.spec_from_file_location("soporte_common", REFERENCE / "generar.py")
common = importlib.util.module_from_spec(spec)
spec.loader.exec_module(common)

ARM_TOP = 46.0
ARM_HALF = 17.0
BEAM_BOTTOM = 30.0
FOOT_WIDTH_ALONG_ARM = 14.0
EXTERIOR_CLEARANCE = 0.22
THROAT = 4.50
HEAD = 8.30
TAB_DEPTH = 4.75
SLOT_CENTERS = (10.0, 30.0)
FOAM = 1.0


def rail_tab(center):
    stem = THROAT / 2
    head = HEAD / 2
    # The narrow part stays between the lips. The wide part is behind them.
    # X is the sliding direction, so the two tabs are constant along X.
    section = [
        (0.78, center - stem), (-1.95, center - stem),
        (-2.55, center - head), (-3.95, center - head),
        (-TAB_DEPTH, center - 3.30), (-TAB_DEPTH, center + 3.30),
        (-3.95, center + head), (-2.55, center + head),
        (-1.95, center + stem), (0.78, center + stem),
    ]
    side = Plane((-ARM_HALF, 0, 0), (0, 1, 0), (1, 0, 0))
    tab = common.prism(section, side, 2 * ARM_HALF)
    # A short lead-in at each end helps the printed wings get past a saw-cut edge.
    lead = [
        (-17, -3.75), (-16, -4.85), (16, -4.85),
        (17, -3.75), (17, 1), (-17, 1),
    ]
    width_lead = [
        (-17, -3.1), (-15.8, -4.2), (15.8, -4.2), (17, -3.1),
        (17, 3.1), (15.8, 4.2), (-15.8, 4.2), (-17, 3.1),
    ]
    depth_limit = common.prism(lead, Plane((0, 0, center - 5.0)), 10)
    wing_plane = Plane((0, -6, center), (-1, 0, 0), (0, 1, 0))
    wing_limit = common.prism(width_lead, wing_plane, 7)
    return (tab & depth_limit & wing_limit).clean()


def integrated_arm(reach, foot_drop):
    y = reach - FOOT_WIDTH_ALONG_ARM
    section = [
        (EXTERIOR_CLEARANCE, 6), (8.6, 6), (8.6, 22), (16.6, BEAM_BOTTOM),
        (y - 7, BEAM_BOTTOM), (y, BEAM_BOTTOM - 7), (y, -foot_drop),
        (reach, -foot_drop), (reach, ARM_TOP), (EXTERIOR_CLEARANCE, ARM_TOP),
    ]
    side = Plane((-ARM_HALF, 0, 0), (0, 1, 0), (1, 0, 0))
    shape = common.prism(section, side, 2 * ARM_HALF).fuse(*(rail_tab(z) for z in SLOT_CENTERS))

    # Captive square M5 nuts load from the free tip of the arm.
    slot_section = [
        (-4.35, 36.4), (4.35, 36.4), (4.35, 42.25), (2.8, 43.8),
        (2.8, ARM_TOP + common.EPS), (-2.8, ARM_TOP + common.EPS),
        (-2.8, 43.8), (-4.35, 42.25),
    ]
    slot_plane = Plane((0, common.ARM_SLOT_START, 0), (-1, 0, 0), (0, 1, 0))
    slot = common.prism(slot_section, slot_plane, reach - common.ARM_SLOT_START + common.EPS)
    return shape.cut(slot).clean()


def verify_fit(arm, rail, reach, foot_drop):
    overlap = common.overlap
    rail_edge = rail.bounding_box().max.X
    offsets = (0, rail_edge - 17, rail_edge, rail_edge + 10, rail_edge + 17, rail_edge + 20)
    checks = {}
    for sign in (-1, 1):
        for offset in offsets:
            dx = sign * offset
            checks[f"entrada_axial_x{dx:g}"] = overlap(arm.translate((dx, 0, 0)), rail)

    for y in (common.ARM_SLOT_START + 4.3, (reach + common.ARM_SLOT_START) / 2, reach - 4.3, reach):
        nut = common.block(-4, 4, y - 4, y + 4, 37.35, 41.35)
        checks[f"recorrido_tuerca_m5_y{y:g}"] = overlap(arm, nut)
    worktop = common.block(-80, 80, -24, reach + 12, -foot_drop - 2, -foot_drop)
    checks["plano_apoyo_nominal"] = overlap(arm, worktop)
    assert max(checks.values()) < 0.0001, checks

    # A forced pull out of the flat side hits both metal lips.
    # The intentional overlap proves capture in this direction, not load capacity.
    capture = {f"pestaña_z{z:g}": overlap(rail, rail_tab(z).translate((0, 1.2, 0))) for z in SLOT_CENTERS}
    assert min(capture.values()) > 1, capture
    return checks, capture


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--alcance", type=float, default=86, help="Del aluminio a la punta, en mm")
    parser.add_argument("--bajada", type=float, default=22, help="Del aluminio al pie impreso, en mm")
    args = parser.parse_args()
    if not 55 <= args.alcance <= 110 or not 12 <= args.bajada <= 35:
        parser.error("Alcance válido de 55 a 110 mm y bajada de 12 a 35 mm.")

    arm = integrated_arm(args.alcance, args.bajada)
    if not (REFERENCE / "qa" / "20x40-05.step").exists():
        common.verify_mesh(common.add_to_bed(arm, Axis.Y, -90), ROOT / "Brazo_L_pestañas_integradas.stl")
        assert export_step(arm, ROOT / "Piezas_impresas.step")
        return
    rail = common.canonical_profile(REFERENCE / "qa" / "20x40-05.step")
    checks, capture = verify_fit(arm, rail, args.alcance, args.bajada)

    stl_path = ROOT / "Brazo_L_pestañas_integradas.stl"
    mesh = common.verify_mesh(common.add_to_bed(arm, Axis.Y, -90), stl_path)
    arm.label, arm.color = "Brazo L con dos pestañas integradas", Color("#DD9A42")
    rail.label, rail.color = "Corte FramingTech 20x40-05", Color("#ABAFB9")
    step_path = ROOT / "Montaje_REV03_EDITABLE.step"
    assert export_step(Compound(children=[rail, arm]), step_path)
    solids = import_step(step_path).solids()
    assert len(solids) == 2 and all(s.is_valid for s in solids)

    qa = ROOT / "qa"
    qa.mkdir(exist_ok=True)
    assert export_stl(arm, qa / "brazo.stl", tolerance=0.10)
    assert export_stl(rail, qa / "perfil.stl", tolerance=0.10)
    summary = {
        "alcance_desde_aluminio_mm": args.alcance,
        "bajada_hasta_el_plastico_mm": args.bajada,
        "eva_nominal_mm": FOAM,
        "bajada_total_con_eva_mm": args.bajada + FOAM,
        "borde_del_perfil_en_la_vista_mm": rail.bounding_box().max.X,
        "paso_centros_de_las_pestañas_mm": SLOT_CENTERS[1] - SLOT_CENTERS[0],
        "cuello_pestaña_mm": THROAT,
        "cabeza_pestaña_mm": HEAD,
        "profundidad_pestaña_mm": TAB_DEPTH,
        "encaje_y_recorrido_colision_mm3": {k: round(v, 6) for k, v in checks.items()},
        "interferencia_si_tira_hacia_fuera_mm3": {k: round(v, 3) for k, v in capture.items()},
        "solidos_step_validos": len(solids),
        "stl": mesh,
        "stl_sha256": sha256(stl_path.read_bytes()).hexdigest(),
        "alcance_de_validacion": "CAD del perfil y del brazo. Ajuste, entrada disponible en el marco y agarre longitudinal pendientes de comprobación física.",
    }
    (qa / "verificacion.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(summary, ensure_ascii=False, indent=2), flush=True)


if __name__ == "__main__":
    main()
