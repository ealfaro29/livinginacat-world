# /// script
# requires-python = ">=3.12"
# dependencies = ["build123d==0.13.0", "trimesh==5.2.1"]
# ///
"""Soporte para el FT412. X sigue el perfil, Y apunta hacia fuera y Z hacia arriba."""

import argparse
import json
from pathlib import Path

from build123d import (
    Align, Axis, Box, Color, Compound, Cylinder, Plane, Polygon, Pos,
    export_step, export_stl, extrude, import_step,
)
import trimesh


ROOT = Path(__file__).resolve().parent
EPS = 0.06
BASE_FACE = 11.0
ARM_BACK = 11.3
ARM_KNEE = 19.3
ARM_TOP = 46.0
ARM_HALF_WIDTH = 17.0
GUIDE_CENTERS = (-10.6, 10.6)
GUIDE_STOP = 3.0
LOCK_HEIGHT = 20.0
ANCHOR_LEVELS = (10.0, 30.0)
M5_CLEARANCE = 5.55
M5_BUTTON_CLEARANCE = 10.2
ARM_SLOT_START = 25.0


def block(x0, x1, y0, y1, z0, z1):
    return Pos(x0, y0, z0) * Box(
        x1 - x0, y1 - y0, z1 - z0,
        align=(Align.MIN, Align.MIN, Align.MIN),
    )


def prism(points, plane, distance):
    face = plane * Polygon(*points, align=None)
    return extrude(face, amount=distance, dir=plane.z_dir)


def bore_y(diameter, y0, y1, z):
    plane = Plane((0, y0, z), (1, 0, 0), (0, 1, 0))
    return plane * Cylinder(
        diameter / 2, y1 - y0, align=(Align.CENTER, Align.CENTER, Align.MIN),
    )


def guide_shape(center, inner, outer, root, mouth, z0, z1):
    points = [
        (center - root / 2, inner), (center + root / 2, inner),
        (center + mouth / 2, outer), (center - mouth / 2, outer),
    ]
    return prism(points, Plane((0, 0, z0)), z1 - z0)


def mounting_base():
    base = block(-18, 18, 0, BASE_FACE, 0, 40)
    cuts = []
    for z in ANCHOR_LEVELS:
        # A 12 mm fastener seated at Y = 6.8 mm projects 5.2 mm into the T-slot.
        cuts.append(bore_y(M5_CLEARANCE, -EPS, BASE_FACE + EPS, z))
        cuts.append(bore_y(M5_BUTTON_CLEARANCE, 6.8, BASE_FACE + EPS, z))

    for x in GUIDE_CENTERS:
        # The rear of the groove is wider. The open end is at the top.
        cuts.append(guide_shape(x, 6.3, BASE_FACE + EPS, 8.7, 5.36, GUIDE_STOP, 40 + EPS))

    # Put an 8 x 8 x 4 square nut into this pocket before mounting the base.
    cuts.append(block(-4.4, 4.4, -EPS, 4.45, LOCK_HEIGHT - 4.4, LOCK_HEIGHT + 4.4))
    cuts.append(bore_y(M5_CLEARANCE, -EPS, BASE_FACE + EPS, LOCK_HEIGHT))
    return base.cut(*cuts).clean()


def arm(length):
    tip = BASE_FACE + length
    half = ARM_HALF_WIDTH
    leg = block(-half, half, ARM_BACK, ARM_KNEE, 3, ARM_TOP)
    beam = block(-half, half, ARM_KNEE - 0.4, tip, 30, ARM_TOP)
    # Reinforce the inside corner of the L.
    rib_plane = Plane((-half, 0, 0), (0, 1, 0), (1, 0, 0))
    rib = prism([(18.8, 7.5), (44, 30.4), (18.8, 30.4)], rib_plane, 2 * half)
    tongues = [
        guide_shape(x, 6.65, 11.46, 7.87, 4.50, GUIDE_STOP, 39.65)
        for x in GUIDE_CENTERS
    ]
    shape = leg.fuse(beam, rib, *tongues).clean()

    # The flat square nuts enter at the tip of this single M5 slot.
    # The sloped shoulders leave clearance for the nut and its screw.
    slot_section = [
        (-4.35, 36.4), (4.35, 36.4), (4.35, 42.25), (2.8, 43.8),
        (2.8, ARM_TOP + EPS), (-2.8, ARM_TOP + EPS), (-2.8, 43.8), (-4.35, 42.25),
    ]
    # This plane uses -X as its local horizontal axis. The section is symmetric.
    slot_plane = Plane((0, ARM_SLOT_START, 0), (-1, 0, 0), (0, 1, 0))
    slot = prism(slot_section, slot_plane, tip - ARM_SLOT_START + EPS)
    keeper = bore_y(M5_CLEARANCE, ARM_BACK - EPS, 17.1, LOCK_HEIGHT)
    access = bore_y(M5_BUTTON_CLEARANCE, 17, tip + EPS, LOCK_HEIGHT)
    return shape.cut(slot, keeper, access).clean()


def overlap(first, second):
    result = first.intersect(second)
    return sum(s.volume for s in result.solids()) if result else 0.0


def add_to_bed(shape, axis, rotation):
    flat = shape.rotate(axis, rotation)
    b = flat.bounding_box()
    return flat.translate((-b.min.X, -b.min.Y, -b.min.Z))


def verify_mesh(shape, destination):
    solids = shape.solids()
    assert len(solids) == 1 and shape.is_valid and shape.volume > 0, destination.name
    assert export_stl(shape, destination, tolerance=0.05, angular_tolerance=0.10)
    mesh = trimesh.load_mesh(destination)
    assert mesh.is_watertight and mesh.is_winding_consistent, destination.name
    assert len(mesh.split(only_watertight=False)) == 1, destination.name
    return {
        "bounds_mm": mesh.bounds.round(3).tolist(),
        "volume_cm3": round(shape.volume / 1000, 3),
    }


def canonical_profile(path):
    profile = import_step(path)
    bounds = profile.bounding_box()
    dimensions = [bounds.size.X, bounds.size.Y, bounds.size.Z]
    long_axis = dimensions.index(max(dimensions))
    if long_axis == 1:
        profile = profile.rotate(Axis.Z, -90)
    elif long_axis == 2:
        profile = profile.rotate(Axis.Y, 90)

    bounds = profile.bounding_box()
    if abs(bounds.size.Y - 40) < 0.1:
        profile = profile.rotate(Axis.X, 90)
        bounds = profile.bounding_box()
    assert abs(bounds.size.Y - 20) < 0.1 and abs(bounds.size.Z - 40) < 0.1

    # Use a short cut from the exact supplier profile for the assembly view.
    profile = profile.translate((-(bounds.min.X + bounds.max.X) / 2, -bounds.max.Y, -bounds.min.Z))
    return profile & block(-60, 60, -21, 0.01, -0.01, 40.01)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--perfil", type=Path, help="STEP del perfil FramingTech 20×40-05")
    parser.add_argument("--tuerca-perfil", type=Path, default=ROOT / "qa" / "RN05BM5.step")
    parser.add_argument("--largo", type=float, default=75)
    args = parser.parse_args()
    if not 50 <= args.largo <= 100:
        parser.error("El alcance del brazo debe estar entre 50 y 100 mm.")
    print("Modelando las dos piezas...", flush=True)

    base = mounting_base()
    extension = arm(args.largo)
    if args.perfil is None:
        verify_mesh(add_to_bed(base, Axis.X, 90), ROOT / "01_Base_perfil_2040.stl")
        verify_mesh(add_to_bed(extension, Axis.Y, -90), ROOT / f"02_Brazo_L_{args.largo:g}_M5.stl")
        assert export_step(Compound(children=[base, extension]), ROOT / "Piezas_impresas.step")
        return
    profile = canonical_profile(args.perfil)
    nut_cad = import_step(args.tuerca_perfil)
    # The loose ball is spring-loaded against the groove. Check the steel body.
    nut_body = max(nut_cad.solids(), key=lambda shape: shape.volume).rotate(Axis.Y, 90)
    rail_nuts = [nut_body.translate((0, -6.0, height)) for height in ANCHOR_LEVELS]
    measurements = {}
    for amount in (0, 0.5, 4, 10, 20, 32, 42):
        measurements[f"brazo_base_elevado_{amount:g}_mm"] = overlap(base, extension.translate((0, 0, amount)))
    measurements["base_perfil"] = overlap(base, profile)
    measurements["brazo_perfil"] = overlap(extension, profile)
    for z, nut in zip(ANCHOR_LEVELS, rail_nuts):
        measurements[f"cuerpo_RN05BM5_perfil_z{z:g}"] = overlap(profile, nut)
        # Check the usable bore and clearance to the aluminum at the screw tip.
        measurements[f"tornillo_perfil_z{z:g}"] = overlap(profile, bore_y(4.94, -5.2, 0, z))
    measurements["paso_tornillo_seguro"] = overlap(base, bore_y(4.94, 1, 11.29, LOCK_HEIGHT))
    tip = BASE_FACE + args.largo
    for y in (ARM_SLOT_START + 4.3, (ARM_SLOT_START + tip) / 2, tip - 4.3):
        envelope = block(-4, 4, y - 4, y + 4, 37.35, 41.35)
        measurements[f"tuerca_deslizante_y{y:g}"] = overlap(extension, envelope)
    assert max(measurements.values()) < 0.0001, measurements

    print("Exportando STL y ensamble...", flush=True)
    base_path = ROOT / "01_Base_perfil_2040.stl"
    arm_path = ROOT / f"02_Brazo_L_{args.largo:g}_M5.stl"
    meshes = {
        base_path.name: verify_mesh(add_to_bed(base, Axis.X, 90), base_path),
        arm_path.name: verify_mesh(add_to_bed(extension, Axis.Y, -90), arm_path),
    }
    base.label, base.color = "Base en el perfil", Color("#317B9D")
    extension.label, extension.color = "Brazo L con ranura M5", Color("#DD9A42")
    profile.label, profile.color = "FramingTech 20x40-05, corte", Color("#ABAFB9")
    # Keep supplier threads out of the exchange assembly. Some kernels
    # cannot re-import their detailed faces. The nut checks above use the originals.
    assembly = Compound(children=[profile, base, extension])
    assembly_path = ROOT / "Montaje_EDITABLE.step"
    assert export_step(assembly, assembly_path)
    exported_solids = import_step(assembly_path).solids()
    assert len(exported_solids) == 3 and all(s.is_valid for s in exported_solids)

    # In-place meshes support drawings without modifying the print orientation.
    drawing_mesh_dir = ROOT / "qa"
    drawing_mesh_dir.mkdir(exist_ok=True)
    for name, obj in (("perfil", profile), ("base", base), ("brazo", extension)):
        assert export_stl(obj, drawing_mesh_dir / f"{name}.stl", tolerance=0.1)
    for z in ANCHOR_LEVELS:
        shaft = bore_y(4.95, -5.2, 6.81, z)
        head = bore_y(9.5, 6.8, 9.56, z)
        assert export_stl(shaft.fuse(head), drawing_mesh_dir / f"anclaje_{z:g}.stl")

    report = {
        "alcance_desde_base_mm": args.largo,
        "paso_centro_ranuras_perfil_mm": ANCHOR_LEVELS[1] - ANCHOR_LEVELS[0],
        "luz_montaje_guia_mm_por_lado": 0.28,
        "proyeccion_anclajes_en_ranura_mm": 5.2,
        "penetracion_tornillo_de_seguro_en_tuerca_mm_nominal": 3.45,
        "colisiones_mm3": {k: round(v, 6) for k, v in measurements.items()},
        "stl": meshes,
        "solidos_validos_al_reabrir_STEP": len(exported_solids),
        "estado": "Ajuste nominal verificado en CAD. Holgura impresa y carga pendientes de validación física.",
    }
    (drawing_mesh_dir / "verificacion.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps(report, indent=2, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
