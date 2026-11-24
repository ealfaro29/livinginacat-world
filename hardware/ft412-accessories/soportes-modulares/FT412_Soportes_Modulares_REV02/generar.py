# /// script
# requires-python = ">=3.12"
# dependencies = ["build123d==0.13.0", "trimesh==5.2.1"]
# ///
"""Brazo con una pata al extremo exterior. X sigue el perfil y Y sale del marco."""

import argparse
from hashlib import sha256
import importlib.util
import json
from pathlib import Path

from build123d import Axis, Color, Compound, Plane, export_step, export_stl, import_step

ROOT = Path(__file__).resolve().parent
PREVIOUS = ROOT.with_name("FT412_Soportes_Modulares_REV01")
spec = importlib.util.spec_from_file_location("base_modular", PREVIOUS / "generar.py")
common = importlib.util.module_from_spec(spec)
spec.loader.exec_module(common)

DEFAULT_REACH = 75.0
FRAME_FOOT = 22.0
EVA = 1.0
FOOT_THICKNESS = 14.0
BEAM_BOTTOM = 30.0
CLIP_FACE = 23.3
ANCHOR_Z = 30.0
KEY_Z = 10.0
ANCHOR_SEAT = 6.8
KEEPER_SEAT = 21.0
BASE_NAME = "01_Base_2040_un_anclaje.stl"


def mounting_base():
    b = common.block
    base = b(-18, 18, 0, common.BASE_FACE, 0, 40)

    # One metal T-nut in the upper slot. The lower key locates the base
    # in the second slot and stops it from rotating about the upper bolt.
    key_section = [
        (0.35, KEY_Z - 2.2), (0, KEY_Z - 2.2),
        (-1.35, KEY_Z - 0.85), (-1.35, KEY_Z + 0.85),
        (0, KEY_Z + 2.2), (0.35, KEY_Z + 2.2),
    ]
    key = common.prism(key_section, Plane((-12, 0, 0), (0, 1, 0), (1, 0, 0)), 24)
    cuts = [
        common.bore_y(common.M5_CLEARANCE, -common.EPS, common.BASE_FACE + common.EPS, ANCHOR_Z),
        common.bore_y(common.M5_BUTTON_CLEARANCE, ANCHOR_SEAT, common.BASE_FACE + common.EPS, ANCHOR_Z),
        common.bore_y(common.M5_CLEARANCE, -common.EPS, common.BASE_FACE + common.EPS, common.LOCK_HEIGHT),
        b(-4.4, 4.4, -common.EPS, 4.45, common.LOCK_HEIGHT - 4.4, common.LOCK_HEIGHT + 4.4),
    ]
    for x in common.GUIDE_CENTERS:
        cuts.append(common.guide_shape(x, 6.3, common.BASE_FACE + common.EPS, 8.7, 5.36,
                                       common.GUIDE_STOP, 40 + common.EPS))
    return base.fuse(key).cut(*cuts).clean()


def supported_arm(reach, foot_height):
    tip = common.BASE_FACE + reach
    half = common.ARM_HALF_WIDTH
    b = common.block

    clip = b(-half, half, common.ARM_BACK, CLIP_FACE, 12, common.ARM_TOP)
    stop = b(-half, half, 7.1, common.ARM_BACK + 0.25, 40, common.ARM_TOP)
    tongues = [
        common.guide_shape(x, 6.65, 11.46, 7.87, 4.50, 12, 40.05)
        for x in common.GUIDE_CENTERS
    ]

    # The leg at the free end reaches the same plane as the feet of the frame.
    # A diagonal shoulder spreads the load at its inside corner.
    section = [
        (CLIP_FACE - 0.4, BEAM_BOTTOM),
        (tip - FOOT_THICKNESS - 7, BEAM_BOTTOM),
        (tip - FOOT_THICKNESS, BEAM_BOTTOM - 7),
        (tip - FOOT_THICKNESS, -foot_height),
        (tip, -foot_height),
        (tip, common.ARM_TOP),
        (CLIP_FACE - 0.4, common.ARM_TOP),
    ]
    side = Plane((-half, 0, 0), (0, 1, 0), (1, 0, 0))
    span = common.prism(section, side, 2 * half)
    shape = clip.fuse(stop, span, *tongues).clean()

    slot_section = [
        (-4.35, 36.4), (4.35, 36.4), (4.35, 42.25), (2.8, 43.8),
        (2.8, common.ARM_TOP + common.EPS), (-2.8, common.ARM_TOP + common.EPS),
        (-2.8, 43.8), (-4.35, 42.25),
    ]
    slot_plane = Plane((0, common.ARM_SLOT_START, 0), (-1, 0, 0), (0, 1, 0))
    slot = common.prism(slot_section, slot_plane, tip - common.ARM_SLOT_START + common.EPS)

    # The locking screw is reached from the gap between the rail and the foot.
    keeper = common.bore_y(common.M5_CLEARANCE, common.ARM_BACK - common.EPS, KEEPER_SEAT + 0.1, common.LOCK_HEIGHT)
    head = common.bore_y(common.M5_BUTTON_CLEARANCE, KEEPER_SEAT, CLIP_FACE + 0.3, common.LOCK_HEIGHT)
    return shape.cut(slot, keeper, head).clean()


def check_clearances(base, arm, profile, tip, foot_height):
    b = common.block
    overlap = common.overlap
    floor = b(-80, 80, -24, tip + 15, -foot_height - 2, -foot_height)
    contacts = {
        "brazo_perfil": overlap(arm, profile),
        "base_perfil": overlap(base, profile),
        "brazo_plano_apoyo": overlap(arm, floor),
        "paso_tornillo_M5x12_al_perfil": overlap(profile, common.bore_y(4.94, ANCHOR_SEAT - 12, 0, ANCHOR_Z)),
        "paso_tornillo_M5x20_de_seguro": overlap(
            base, common.bore_y(4.94, KEEPER_SEAT - 20, common.BASE_FACE, common.LOCK_HEIGHT),
        ),
        "acceso_al_seguro": overlap(
            arm, common.bore_y(9.9, KEEPER_SEAT + 0.03, tip - FOOT_THICKNESS - 4.2, common.LOCK_HEIGHT),
        ),
    }
    for dz in (0, 0.6, 4, 10, 20, 30, 42):
        contacts[f"insercion_vertical_{dz:g}_mm"] = overlap(base, arm.translate((0, 0, dz)))
    for y in (
        common.ARM_SLOT_START + 4.3,
        (tip + common.ARM_SLOT_START) / 2,
        tip - 4.3,
        tip,
    ):
        nut = b(-4, 4, y - 4, y + 4, 37.35, 41.35)
        contacts[f"recorrido_tuerca_y{y:g}"] = overlap(arm, nut)
    assert max(contacts.values()) < 1e-4, contacts

    kind = [(f.center().Y, f.area) for f in arm.faces() if abs(f.center().Z + foot_height) < 1e-5]
    assert len(kind) == 1
    foot_center, area = kind[0]
    assert abs(foot_center - (tip - FOOT_THICKNESS / 2)) < 1e-4
    assert abs(area - 2 * common.ARM_HALF_WIDTH * FOOT_THICKNESS) < 1e-4
    return contacts, area


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--largo", type=float, default=DEFAULT_REACH)
    parser.add_argument("--bajada", type=float, default=FRAME_FOOT, help="Del aluminio a la base de plástico, en mm")
    args = parser.parse_args()
    if not 50 <= args.largo <= 100 or not 12 <= args.bajada <= 35:
        parser.error("Largo válido de 50 a 100 mm y bajada de 12 a 35 mm.")
    base = mounting_base()
    arm = supported_arm(args.largo, args.bajada)
    if not (PREVIOUS / "qa" / "20x40-05.step").exists():
        common.verify_mesh(common.add_to_bed(base, Axis.X, 0), ROOT / BASE_NAME)
        common.verify_mesh(common.add_to_bed(arm, Axis.Y, -90), ROOT / f"02_Brazo_{args.largo:g}_con_pata.stl")
        assert export_step(Compound(children=[base, arm]), ROOT / "Piezas_impresas.step")
        return
    profile = common.canonical_profile(PREVIOUS / "qa" / "20x40-05.step")
    tip = common.BASE_FACE + args.largo
    contacts, area = check_clearances(base, arm, profile, tip, args.bajada)

    nut = import_step(PREVIOUS / "qa" / "RN05BM5.step")
    body = max(nut.solids(), key=lambda shape: shape.volume).rotate(Axis.Y, 90)
    contacts["cuerpo_RN05BM5_en_ranura_superior"] = common.overlap(
        profile, body.translate((0, -6, ANCHOR_Z)),
    )
    assert contacts["cuerpo_RN05BM5_en_ranura_superior"] < 1e-4

    base_path = ROOT / BASE_NAME
    arm_path = ROOT / f"02_Brazo_{args.largo:g}_con_pata.stl"
    base_mesh = common.verify_mesh(common.add_to_bed(base, Axis.X, 0), base_path)
    arm_mesh = common.verify_mesh(common.add_to_bed(arm, Axis.Y, -90), arm_path)

    base.label, base.color = "Base para perfil", Color("#317B9D")
    arm.label, arm.color = "Brazo M5 con apoyo exterior", Color("#DD9A42")
    profile.label, profile.color = "Corte FramingTech 20x40-05", Color("#ABAFB9")
    step_path = ROOT / "Montaje_REV02_EDITABLE.step"
    assert export_step(Compound(children=[profile, base, arm]), step_path)
    solids = import_step(step_path).solids()
    assert len(solids) == 3 and all(s.is_valid for s in solids)

    qa = ROOT / "qa"
    qa.mkdir(exist_ok=True)
    for name, shape in (("perfil", profile), ("base", base), ("brazo", arm)):
        assert export_stl(shape, qa / f"{name}.stl", tolerance=0.10)
    # Visual reference for the upper fastener only.
    shaft = common.bore_y(4.95, ANCHOR_SEAT - 12, ANCHOR_SEAT + 0.01, ANCHOR_Z)
    head = common.bore_y(9.5, ANCHOR_SEAT, ANCHOR_SEAT + 2.76, ANCHOR_Z)
    assert export_stl(shaft.fuse(head), qa / "anclaje.stl")

    results = {
        "alcance_desde_base_mm": args.largo,
        "base_sha256": sha256(base_path.read_bytes()).hexdigest(),
        "bajada_desde_perfil_hasta_plastico_mm": args.bajada,
        "eva_nominal_mm": EVA,
        "bajada_desde_perfil_con_eva_mm": args.bajada + EVA,
        "descenso_pata_desde_debajo_del_brazo_mm": BEAM_BOTTOM + args.bajada,
        "huella_nominal_pata_mm2": round(area, 3),
        "colisiones_mm3": {k: round(v, 6) for k, v in contacts.items()},
        "stl_base": base_mesh,
        "stl_brazo": arm_mesh,
        "herrajes_por_soporte": {
            "perfil": "1 #6633 M5×12 y 1 RN05BM5",
            "seguro": "1 #6635 M5×20 y 1 tuerca cuadrada M5 de 8×8×4",
            "ranura": "Tuercas cuadradas M5 de 8×8×4 por accesorio",
        },
        "solidos_validos_al_reabrir_STEP": len(solids),
        "estado": "Datos del CAD. La altura real y la carga requieren comprobación física.",
    }
    (qa / "verificacion.json").write_text(json.dumps(results, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(results, ensure_ascii=False, indent=2), flush=True)


if __name__ == "__main__":
    main()
