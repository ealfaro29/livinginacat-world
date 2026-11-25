# /// script
# requires-python = ">=3.12"
# dependencies = ["lxml>=5,<7", "numpy>=1.26", "scipy>=1.13", "trimesh==5.2.1"]
# ///
"""Write or verify the portable multiplate project using Bambu's native X2D profile."""

import argparse
import hashlib
import json
import math
import re
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo
from lxml import etree as ET

import numpy as np
import trimesh
from scipy.spatial import cKDTree

HERE = Path(__file__).resolve().parents[1]
PRESET = HERE.parent / "01-Frente-y-cama-R01/Bambu/01_Cama_iPhone14_PETG_X2D_0.4.3mf"
FILENAME = "FT412-V2_Completa_PETG_X2D_0.4.3mf"
OUT = HERE / "Bambu" / FILENAME
CORE = "http://schemas.microsoft.com/3dmanufacturing/core/2015/02"
PROD = "http://schemas.microsoft.com/3dmanufacturing/production/2015/06"
BBL = "http://schemas.bambulab.com/package/2021"
PKG = "http://schemas.openxmlformats.org/package/2006/relationships"
REL = "http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"
MODEL = "3D/3dmodel.model"
SETTINGS = "Metadata/model_settings.config"
PROFILE = "Metadata/project_settings.config"
IDENTITY = "1 0 0 0 1 0 0 0 1"
LAYOUT = json.loads((HERE / "placas.json").read_text())
OBJECTS = LAYOUT["objects"]


def uid(label):
    return str(uuid5(NAMESPACE_URL, "ft412-v2-completa-r01/" + str(label)))


def meta(parent, key, value):
    return ET.SubElement(parent, "metadata", key=key, value=str(value))


def origin(plate):
    width = math.ceil(math.sqrt(len(LAYOUT["plates"])))
    return np.array(
        [256 * 1.2 * ((plate - 1) % width), -256 * 1.2 * ((plate - 1) // width), 0.0]
    )


def pack(z, name, data):
    zipinfo = ZipInfo(name)
    zipinfo.create_system = 3
    zipinfo.external_attr = 0o100644 << 16
    if isinstance(data, ET._Element):
        data = ET.tostring(data, encoding="UTF-8", xml_declaration=True)
    z.writestr(zipinfo, data, ZIP_DEFLATED, compresslevel=6)


def model():
    return ET.Element(
        "{%s}model" % CORE,
        nsmap={None: CORE, "p": PROD, "BambuStudio": BBL},
        unit="millimeter",
    )


def mesh_xml(mesh, vid, label):
    root = model()
    obj = ET.SubElement(
        ET.SubElement(root, "resources"), "object", id=vid, type="model"
    )
    obj.set("{%s}UUID" % PROD, uid(label + "/mesh"))
    surface = ET.SubElement(obj, "mesh")
    vertices = ET.SubElement(surface, "vertices")
    for x, y, z in mesh.vertices:
        ET.SubElement(vertices, "vertex", x=f"{x:.7f}", y=f"{y:.7f}", z=f"{z:.7f}")
    faces = ET.SubElement(surface, "triangles")
    for a, b, c in mesh.faces:
        ET.SubElement(faces, "triangle", v1=str(a), v2=str(b), v3=str(c))
    return root


def make(meshdir, output):
    with ZipFile(PRESET) as ref:
        profile = json.loads(ref.read(PROFILE))
        types = ref.read("[Content_Types].xml")
    assert profile["printer_settings_id"] == "Bambu Lab X2D 0.4 nozzle"
    assert profile["filament_type"] == ["PETG"] and profile["filament_nozzle_map"] == [
        "0"
    ]
    outer = model()
    outer.set("requiredextensions", "p")
    for key, value in {
        "Application": "BambuStudio-02.09.01.70",
        "BambuStudio:3mfVersion": "1",
        "Title": "FT412 V2 | Proyecto completo / Complete project",
        "License": "MIT; see the bundled license notices",
    }.items():
        ET.SubElement(outer, "metadata", name=key).text = value
    objs = ET.SubElement(outer, "resources")
    build = ET.SubElement(outer, "build")
    build.set("{%s}UUID" % PROD, uid("build"))
    settings = ET.Element("config")
    root_rels = ET.Element("Relationships", nsmap={None: PKG})
    ET.SubElement(root_rels, "Relationship", Id="rel-1", Target="/" + MODEL, Type=REL)
    rels = ET.Element("Relationships", nsmap={None: PKG})
    plates = []
    for i, name in enumerate(LAYOUT["plates"], 1):
        p = ET.Element("plate")
        for k, v in {
            "plater_id": i,
            "plater_name": f"{i:02} {name}",
            "locked": "false",
            "filament_map_mode": "Manual",
            "filament_maps": "1",
            "filament_volume_maps": "0",
        }.items():
            meta(p, k, v)
        plates.append(p)
    output.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(output, "w") as archive:
        for i, row in enumerate(OBJECTS, 1):
            name = row["name"]
            vid, oid = str(2 * i - 1), str(2 * i)
            target = f"3D/Objects/object_{i}.model"
            mesh = trimesh.load_mesh(meshdir / (name + ".stl"))
            plate = row["plate"]
            x, y, _ = origin(plate) + np.array([*row["xy"], 0])
            pack(archive, target, mesh_xml(mesh, vid, name))
            ET.SubElement(
                rels, "Relationship", Id=f"rel-{i}", Target="/" + target, Type=REL
            )
            obj = ET.SubElement(objs, "object", id=oid, type="model")
            obj.set("{%s}UUID" % PROD, uid(name))
            comp = ET.SubElement(
                ET.SubElement(obj, "components"), "component", objectid=vid
            )
            comp.set("{%s}path" % PROD, "/" + target)
            comp.set("{%s}UUID" % PROD, uid(name + "/part"))
            comp.set("transform", IDENTITY + " 0 0 0")
            it = ET.SubElement(
                build,
                "item",
                objectid=oid,
                printable="1",
                transform=f"{IDENTITY} {x:.5f} {y:.5f} 0",
            )
            it.set("{%s}UUID" % PROD, uid(name + "/item"))
            config = ET.SubElement(settings, "object", id=oid)
            for k, v in {
                "name": name,
                "extruder": "1",
                "enable_support": int(row["support"]),
                "sparse_infill_density": str(row["infill"]) + "%",
                "wall_loops": row["walls"],
            }.items():
                meta(config, k, v)
            if name.startswith(("16_", "17_")):
                for k, v in {
                    "layer_height": "0.16",
                    "top_shell_layers": "6",
                    "bottom_shell_layers": "6",
                    "outer_wall_speed": "25",
                    "inner_wall_speed": "45",
                }.items():
                    meta(config, k, v)
            ET.SubElement(config, "metadata", face_count=str(len(mesh.faces)))
            part = ET.SubElement(
                config, "part", id=vid, subtype="normal_part", uuid=uid(name + "/part")
            )
            meta(part, "name", name)
            meta(part, "source_file", name + ".stl")
            meta(part, "matrix", "1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1")
            inst = ET.SubElement(plates[plate - 1], "model_instance")
            for k, v in {
                "object_id": oid,
                "instance_id": "0",
                "identify_id": i,
            }.items():
                meta(inst, k, v)
        settings.extend(plates)
        ET.SubElement(settings, "assemble")
        for path, data in [
            ("[Content_Types].xml", types),
            ("_rels/.rels", root_rels),
            ("3D/_rels/3dmodel.model.rels", rels),
            (MODEL, outer),
            (SETTINGS, settings),
            (PROFILE, json.dumps(profile, ensure_ascii=False, indent=2)),
        ]:
            pack(archive, path, data)
        pack(
            archive,
            "Metadata/LICENSE.txt",
            (HERE.parents[3] / "LICENSE").read_bytes()
            + b"\n"
            + (HERE.parents[2] / "ft412-coupler-rev01/LICENSE").read_bytes(),
        )


def values(elem):
    return {
        e.get("key"): e.get("value") for e in elem.findall("metadata") if e.get("key")
    }


def triangles(f):
    # Cyclic rotation preserves the winding. Reversed triangles are different.
    r = np.arange(3)[None, :] + f.argmin(axis=1)[:, None]
    rows = np.take_along_axis(f, r % 3, axis=1)
    return rows[np.lexsort(rows.T[::-1])]


def mesh_match(z, obj, item, src, center):
    comp = obj.find("{*}components/{*}component")
    tree = ET.fromstring(z.read(comp.get("{%s}path" % PROD).lstrip("/")))
    surface = tree.find(".//{*}mesh")
    verts = np.array(
        [[float(n.get(k)) for k in "xyz"] for n in surface.find("{*}vertices")]
    )
    faces = np.array(
        [
            [int(n.get(k)) for k in ("v1", "v2", "v3")]
            for n in surface.find("{*}triangles")
        ]
    )
    for e in (comp, item):
        tf = np.fromstring(e.get("transform", IDENTITY + " 0 0 0"), sep=" ").reshape(
            4, 3
        )
        verts = verts @ tf[:3] + tf[3]
    dist, ix = cKDTree(src.vertices).query(verts - center)
    assert dist.max() < 0.0002 and len(ix) == len(src.vertices), (
        src.metadata,
        dist.max(),
    )
    assert np.array_equal(triangles(ix[faces]), triangles(src.faces))
    return len(faces)


def verify(meshdir, filename, native, report):
    with ZipFile(filename) as z:
        assert z.testzip() is None
        cfg = json.loads(z.read(PROFILE))
        assert cfg["filament_type"] == ["PETG"] and cfg["filament_nozzle_map"] == ["0"]
        assert (
            cfg["printer_settings_id"] == "Bambu Lab X2D 0.4 nozzle"
            and cfg["brim_width"] == "5"
        )
        assert (
            cfg["enable_prime_tower"] == "0"
            and cfg["sparse_infill_pattern"] == "gyroid"
        )
        outer = ET.fromstring(z.read(MODEL))
        config = ET.fromstring(z.read(SETTINGS))
        items = {i.get("objectid"): i for i in outer.findall("{*}build/{*}item")}
        parts = {o.get("id"): o for o in outer.findall("{*}resources/{*}object")}
        assert len(config.findall("plate")) == len(LAYOUT["plates"])
        assert all(
            len(v) == len(OBJECTS) for v in (items, parts, config.findall("object"))
        )
        assert sum(
            len(plate.findall("model_instance")) for plate in config.findall("plate")
        ) == len(OBJECTS)
        objects = {row["name"]: row for row in OBJECTS}
        by_id = {}
        for el in config.findall("object"):
            oid = el.get("id")
            props = values(el)
            name = props["name"]
            row = objects[name]
            for key, val in {
                "enable_support": str(int(row["support"])),
                "wall_loops": str(row["walls"]),
                "sparse_infill_density": f"{row['infill']}%",
            }.items():
                assert props.get(key, cfg[key]) == val, (name, key, props.get(key))
            assert items[oid].get("printable") == "1"
            src = trimesh.load_mesh(meshdir / (name + ".stl"))
            center = origin(row["plate"]) + np.array([*row["xy"], 0])
            mesh_match(z, parts[oid], items[oid], src, center)
            lo, hi = src.bounds + np.array([*row["xy"], 0])
            assert (
                min(lo[:2]) >= 5
                and max(hi[:2]) <= 251
                and abs(lo[2]) < 0.0001
                and hi[2] < 261
            )
            by_id[oid] = name
        assert set(by_id.values()) == set(objects)
        for i, plate in enumerate(config.findall("plate"), 1):
            assert int(values(plate)["plater_id"]) == i
            assert {
                by_id[values(e)["object_id"]] for e in plate.findall("model_instance")
            } == {row["name"] for row in OBJECTS if row["plate"] == i}
        proof = {
            "objects": len(OBJECTS),
            "project_sha256": hashlib.sha256(filename.read_bytes()).hexdigest(),
            "plates": [],
        }
        if native:
            info = ET.fromstring(z.read("Metadata/slice_info.config"))
            assert len(info.findall("plate")) == len(LAYOUT["plates"])
            for i, plate in enumerate(info.findall("plate"), 1):
                props = values(plate)
                assert int(props["index"]) == i
                targets = {r["name"] for r in OBJECTS if r["plate"] == i}
                assert {e.get("name") for e in plate.findall("object")} == targets
                assert all(e.get("skipped") == "false" for e in plate.findall("object"))
                assert props["outside"] == "false" and props["filament_maps"] == "1"
                fil = plate.findall("filament")
                assert len(fil) == 1 and fil[0].get("type") == "PETG"
                assert (
                    fil[0].get("nozzle_diameter") == "0.40"
                    and plate.find("nozzle").get("extruder_id") == "1"
                )
                key = f"Metadata/plate_{i}.gcode"
                raw = z.read(key)
                assert (
                    z.read(key + ".md5").decode().strip().lower()
                    == hashlib.md5(raw).hexdigest()
                )
                assert b"; FEATURE: Brim" in raw and b"G1 X" in raw
                support = any(r["support"] for r in OBJECTS if r["plate"] == i)
                assert (b"; FEATURE: Support interface" in raw) == support
                assert props["support_used"] == str(support).lower()
                bounds = json.loads(z.read(f"Metadata/plate_{i}.json"))["bbox_all"]
                assert min(bounds[:2]) > 0 and max(bounds[2:]) < 256, (i, bounds)
                layers = int(re.search(rb"; total layer number: (\d+)", raw, re.I)[1])
                proof["plates"].append(
                    {
                        "plate": i,
                        "objects": sorted(targets),
                        "seconds": int(props["prediction"]),
                        "petg_g": float(props["weight"]),
                        "layers": layers,
                        "support": support,
                        "bbox_mm": bounds,
                    }
                )
        if report:
            report.write_text(json.dumps(proof, indent=2) + "\n")
        print(
            f"{'Native' if native else 'Portable'}: {len(OBJECTS)} objects, {len(LAYOUT['plates'])} plates",
            flush=True,
        )


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("meshes", type=Path)
    p.add_argument("--output", type=Path, default=OUT)
    p.add_argument(
        "--native",
        type=Path,
        help="Verify the project re-exported and sliced by Bambu Studio",
    )
    p.add_argument("--report", type=Path)
    args = p.parse_args()
    if not args.native:
        make(args.meshes, args.output)
    verify(args.meshes, args.native or args.output, bool(args.native), args.report)
