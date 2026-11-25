# /// script
# requires-python = ">=3.12"
# dependencies = ["lxml>=5,<7"]
# ///
"""Build the two-plate V2 starter project from its approved individual projects."""

from argparse import ArgumentParser
from copy import deepcopy
import json
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

from lxml import etree

BATCH = Path(__file__).resolve().parents[1]
PLATES = (
    "01_Cama_iPhone14_PETG_X2D_0.4.3mf",
    "02_Frente_consola_PETG_X2D_0.4.3mf",
)
COMBINED = "FT412-V2_Inicio_PETG_X2D_0.4.3mf"
PROD = "{http://schemas.microsoft.com/3dmanufacturing/production/2015/06}"
ROOT_MODEL = "3D/3dmodel.model"
MODEL_RELS = "3D/_rels/3dmodel.model.rels"
CONFIG = "Metadata/model_settings.config"
PROFILE = "Metadata/project_settings.config"


def read_xml(archive, key):
    return etree.fromstring(
        archive.read(key),
        parser=etree.XMLParser(resolve_entities=False, no_network=True),
    )


def xml(tree):
    return etree.tostring(tree, encoding="UTF-8", xml_declaration=True)


def identifier(label):
    return str(uuid5(NAMESPACE_URL, "ft412-v2/r01/" + label))


def store_file(archive, name, data):
    # Fixed timestamps make regenerating an unchanged project byte-identical.
    entry = ZipInfo(name)
    entry.create_system = 3
    entry.external_attr = 0o100644 << 16
    archive.writestr(entry, data, compress_type=ZIP_DEFLATED, compresslevel=6)


def make_project(output):
    with ZipFile(BATCH / "Bambu" / PLATES[0]) as first:
        profile = json.loads(first.read(PROFILE))
        content_types = first.read("[Content_Types].xml")
        package_rels = first.read("_rels/.rels")
        outer = read_xml(first, ROOT_MODEL)
        rels = read_xml(first, MODEL_RELS)
    resources = outer.find("{*}resources")
    build = outer.find("{*}build")
    resources.clear()
    build.clear()
    build.set(PROD + "UUID", identifier("build"))
    outer.find('{*}metadata[@name="Title"]').text = "FT412 V2 | Tanda 01 / Batch 01"
    link_template = deepcopy(rels[0])
    for child in list(rels):
        rels.remove(child)
    settings = etree.Element("config")
    volumes = {}
    plates = []
    # Bambu places the next X2D bed one width plus a 20% gap to the right.
    width = max(float(p.split("x")[0]) for p in profile["printable_area"])
    for index, filename in enumerate(PLATES):
        number = index + 1
        volume_id = str(2 * number - 1)
        object_id = str(2 * number)
        target = f"3D/Objects/object_{number}.model"
        with ZipFile(BATCH / "Bambu" / filename) as source:
            props = json.loads(source.read(PROFILE))
            model = read_xml(source, ROOT_MODEL)
            obj = model.find("{*}resources/{*}object")
            comp = obj.find("{*}components/{*}component")
            mesh = read_xml(source, comp.get(PROD + "path").lstrip("/"))
            item = model.find("{*}build/{*}item")
            values = read_xml(source, CONFIG)
        mesh_object = mesh.find("{*}resources/{*}object")
        mesh_object.set("id", volume_id)
        mesh_object.set(PROD + "UUID", identifier(filename + "/volume"))
        obj.set("id", object_id)
        obj.set(PROD + "UUID", identifier(filename + "/object"))
        comp.set("objectid", volume_id)
        comp.set(PROD + "path", "/" + target)
        comp.set(PROD + "UUID", identifier(filename + "/instance"))
        resources.append(obj)
        item.set("objectid", object_id)
        item.set(PROD + "UUID", identifier(filename + "/item"))
        transform = item.get("transform").split()
        transform[9] = f"{float(transform[9]) + index * width * 1.2:.6f}"
        item.set("transform", " ".join(transform))
        build.append(item)

        obj_settings = values.find("object")
        obj_settings.set("id", object_id)
        part = obj_settings.find("part")
        part.set("id", volume_id)
        # Keep both processes on one printer profile. Only these per-object
        # settings differ between the released projects.
        changes = {
            k for k in props.keys() | profile.keys() if props.get(k) != profile.get(k)
        }
        if not changes <= {"enable_support", "sparse_infill_density"}:
            raise ValueError(f"Incompatible plate settings: {sorted(changes)}")
        for k in sorted(changes):
            override = etree.Element("metadata", key=k, value=props[k])
            part.addprevious(override)
        settings.append(obj_settings)
        plate = values.find("plate")
        plate.find('metadata[@key="plater_id"]').set("value", str(number))
        inst = plate.find("model_instance")
        inst.find('metadata[@key="object_id"]').set("value", object_id)
        inst.find('metadata[@key="identify_id"]').set("value", str(number))
        plates.append(plate)
        link = deepcopy(link_template)
        link.set("Id", f"rel-{number}")
        link.set("Target", "/" + target)
        rels.append(link)
        volumes[target] = xml(mesh)
    settings.extend(plates)
    etree.SubElement(settings, "assemble")
    output.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(output, "w", ZIP_DEFLATED, compresslevel=6) as archive:
        for name, data in {
            "[Content_Types].xml": content_types,
            "_rels/.rels": package_rels,
            ROOT_MODEL: xml(outer),
            MODEL_RELS: xml(rels),
            CONFIG: xml(settings),
            PROFILE: json.dumps(profile, ensure_ascii=False, indent=2),
            **volumes,
        }.items():
            store_file(archive, name, data)


if __name__ == "__main__":
    args = ArgumentParser(description=__doc__)
    args.add_argument("--output", type=Path, default=BATCH / "Bambu" / COMBINED)
    args.add_argument(
        "--package",
        type=Path,
        help="Also write the public ZIP with both STLs and the print guide.",
    )
    options = args.parse_args()
    make_project(options.output)
    if options.package:
        options.package.parent.mkdir(parents=True, exist_ok=True)
        with ZipFile(options.package, "w") as archive:
            store_file(archive, "Bambu/" + COMBINED, options.output.read_bytes())
            for member in (
                "Piezas/01_Cama_iPhone14.stl",
                "Piezas/02_Frente_consola.stl",
                "README.md",
                "Vista-tanda-01.png",
            ):
                store_file(archive, member, (BATCH / member).read_bytes())
