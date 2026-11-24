"""Create two independent editable X2D projects with native Bambu toolpaths."""
import argparse
import hashlib
import json
import re
import subprocess
import tempfile
import uuid
import xml.etree.ElementTree as ET
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

import numpy as np
import trimesh
from scipy.spatial import cKDTree

OUT = Path(__file__).resolve().parent.parent
MODELS = OUT.parents[2] / "ft412-accessories"
TEMPLATE = (MODELS / "print-prep" /
            "FT412_06_Soporte_Electronica_PETG_X2D_0.4_REVISION_S301T.3mf")
BAMBU = "/Applications/BambuStudio.app/Contents/MacOS/BambuStudio"
PARTS = {"01_Cama_iPhone14": False, "02_Frente_consola": True}
CORE = "http://schemas.microsoft.com/3dmanufacturing/core/2015/02"
PRODUCTION = "http://schemas.microsoft.com/3dmanufacturing/production/2015/06"
BBL = "http://schemas.bambulab.com/package/2021"
RELS = "http://schemas.openxmlformats.org/package/2006/relationships"
MODEL_REL = "http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"


def metadata(parent, key, value):
    ET.SubElement(parent, "metadata", key=key, value=str(value))


def xml(element):
    return ET.tostring(element, encoding="utf-8", xml_declaration=True)


def relationship(target):
    root = ET.Element("Relationships", xmlns=RELS)
    ET.SubElement(root, "Relationship", Target=target, Id="rel-1", Type=MODEL_REL)
    return xml(root)


def seed_project(work, name, supports, template):
    with ZipFile(template) as base:
        cfg = json.loads(base.read("Metadata/project_settings.config"))
        content_types = base.read("[Content_Types].xml")
    assert cfg["printer_settings_id"] == "Bambu Lab X2D 0.4 nozzle"
    assert cfg["filament_type"] == ["PETG"] and cfg["filament_nozzle_map"] == ["0"]
    cfg.update({"layer_height": "0.2", "initial_layer_print_height": "0.2",
                "wall_loops": "4", "sparse_infill_pattern": "gyroid",
                "sparse_infill_density": "25%" if supports else "20%",
                "top_shell_layers": "5", "bottom_shell_layers": "5", "top_shell_thickness": "1",
                "enable_support": str(int(supports)), "support_type": "tree(auto)",
                "support_on_build_plate_only": "0", "support_threshold_angle": "30",
                "support_top_z_distance": "0.28", "support_bottom_z_distance": "0.28",
                "support_object_xy_distance": "0.4", "enable_prime_tower": "0",
                "brim_type": "outer_only", "brim_width": "5", "brim_object_gap": "0.12",
                "filament_map_mode": "Manual", "filament_map": ["1"], "filament_nozzle_map": ["0"],
                "curr_bed_type": "Textured PEI Plate", "print_sequence": "by layer"})
    mesh = trimesh.load_mesh(OUT / "Piezas" / (name + ".stl"))
    model = ET.Element("model", unit="millimeter", xmlns=CORE)
    spec = ET.SubElement(ET.SubElement(ET.SubElement(model, "resources"), "object",
                                      id="1", type="model"), "mesh")
    vertices = ET.SubElement(spec, "vertices")
    for x, y, z in mesh.vertices:
        ET.SubElement(vertices, "vertex", x=f"{x:.7f}", y=f"{y:.7f}", z=f"{z:.7f}")
    triangles = ET.SubElement(spec, "triangles")
    for i, j, k in mesh.faces:
        ET.SubElement(triangles, "triangle", v1=str(i), v2=str(j), v3=str(k))

    assembly = ET.Element("model", {"unit": "millimeter", "xmlns": CORE, "xmlns:p": PRODUCTION,
                            "xmlns:BambuStudio": BBL, "requiredextensions": "p"})
    ET.SubElement(assembly, "metadata", name="Application").text = "BambuStudio-02.09.01.70"
    ET.SubElement(assembly, "metadata", name="BambuStudio:3mfVersion").text = "1"
    reference = "/3D/Objects/part.model"
    obj = ET.SubElement(ET.SubElement(assembly, "resources"), "object",
                        {"id": "2", "type": "model", "p:UUID": str(uuid.uuid5(uuid.NAMESPACE_URL, name))})
    part_id = str(uuid.uuid5(uuid.NAMESPACE_URL, name+"/part"))
    ET.SubElement(ET.SubElement(obj, "components"), "component",
                  {"objectid": "1", "p:path": reference, "p:UUID": part_id})
    ET.SubElement(ET.SubElement(assembly, "build"), "item",
                  {"objectid": "2", "p:UUID": str(uuid.uuid5(uuid.NAMESPACE_URL, name+"/build")),
                   "transform": "1 0 0 0 1 0 0 0 1 128 128 0", "printable": "1"})
    settings = ET.Element("config")
    project_obj = ET.SubElement(settings, "object", id="2")
    metadata(project_obj, "name", name)
    metadata(project_obj, "extruder", "1")
    ET.SubElement(project_obj, "metadata", face_count=str(len(mesh.faces)))
    part = ET.SubElement(project_obj, "part", id="1", subtype="normal_part", uuid=part_id)
    metadata(part, "name", name)
    metadata(part, "source_file", name+".stl")
    metadata(part, "matrix", "1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1")
    plate = ET.SubElement(settings, "plate")
    for key, value in {"plater_id":"1", "plater_name":name, "locked":"false",
                       "filament_map_mode":"Manual", "filament_maps":"1",
                       "filament_volume_maps":"0"}.items():
        metadata(plate, key, value)
    inst = ET.SubElement(plate, "model_instance")
    for key,value in (("object_id", "2"), ("instance_id", "0"), ("identify_id", "1")):
        metadata(inst, key, value)
    path = work / "entrada.3mf"
    with ZipFile(path, "w", ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", content_types)
        z.writestr("_rels/.rels", relationship("/3D/3dmodel.model"))
        z.writestr("3D/3dmodel.model", xml(assembly))
        z.writestr("3D/_rels/3dmodel.model.rels", relationship(reference))
        z.writestr(reference[1:], xml(model))
        z.writestr("Metadata/model_settings.config", xml(settings))
        z.writestr("Metadata/project_settings.config", json.dumps(cfg))
    return path


def verify(project, name, supports):
    with ZipFile(project) as z:
        assert z.testzip() is None
        cfg = json.loads(z.read("Metadata/project_settings.config"))
        plate = ET.fromstring(z.read("Metadata/slice_info.config")).find("plate")
        info = {el.get("key"): el.get("value") for el in plate.findall("metadata")}
        obj = plate.findall("object")
        assert len(obj) == 1 and obj[0].get("name") == name and obj[0].get("skipped") == "false"
        assert info["outside"] == "false" and info["support_used"] == str(supports).lower()
        assert info["filament_maps"] == "1" and plate.find("nozzle").get("extruder_id") == "1"
        filaments = plate.findall("filament")
        assert len(filaments)==1 and filaments[0].get("type") == "PETG"
        assert filaments[0].get("nozzle_diameter") == "0.40"
        assert cfg["printer_settings_id"] == "Bambu Lab X2D 0.4 nozzle"
        assert cfg["layer_height"] == "0.2" and cfg["brim_width"] == "5" and cfg["wall_loops"] == "4"
        assert cfg["filament_nozzle_map"] == ["0"] and cfg["enable_prime_tower"]=="0"
        gcode = z.read("Metadata/plate_1.gcode").decode()
        layers = re.search(r"; total layer number: (\d+)", gcode, re.I)
        if not layers:
            layers = re.search(r";\s*total_layer_number\s*=\s*(\d+)", gcode, re.I)
        assert layers and int(layers[1]) > 30 and "G1 X" in gcode
        models = [f for f in z.namelist() if f.startswith("3D/Objects/") and f.endswith(".model")]
        assert len(models) == 1
        model = ET.fromstring(z.read(models[0]))
        verts = np.array([[float(v.get(axis)) for axis in ("x","y","z")]
                          for v in model.findall(".//{*}vertex")])
        faces = np.array([[int(f.get(index)) for index in ("v1","v2","v3")]
                          for f in model.findall(".//{*}triangle")])
        assembly = ET.fromstring(z.read("3D/3dmodel.model"))
        build = assembly.find(".//{*}item")
        assert len(assembly.findall(".//{*}item")) == 1 and build.get("printable") == "1"
        for item in (assembly.find(".//{*}component"), build):
            transform = np.fromstring(item.get("transform"), sep=" ").reshape(4,3)
            assert np.array_equal(transform[:3], np.eye(3))
            verts += transform[3]
        verts -= np.array([128., 128., 0.])
        src = trimesh.load_mesh(OUT/"Piezas"/(name+".stl"))
        dist, idx = cKDTree(src.vertices).query(verts)
        assert dist.max() < .0001
        def sorted_triangles(f):
            rows = np.sort(f, axis=1)
            return rows[np.lexsort(rows.T[::-1])]
        assert np.array_equal(sorted_triangles(idx[faces]), sorted_triangles(src.faces))
        plate_json = json.loads(z.read("Metadata/plate_1.json"))
        x0,y0,x1,y1 = plate_json["bbox_all"]
        assert min(x0,y0) > 0 and max(x1,y1) < 256 and abs(verts[:,2].min()) < .0001
        assert "; FEATURE: Brim" in gcode and ("; FEATURE: Support interface" in gcode) == supports
        return {"layers": int(layers[1]), "estimated_seconds": int(info["prediction"]),
                "estimated_petg_g": float(info["weight"]), "supports_generated": supports,
                "plate": plate_json.get("bbox_all"), "editable_mesh_triangles": len(faces),
                "matches_source_stl_at_100_percent": True, "outside_plate": False,
                "sha256": hashlib.sha256(project.read_bytes()).hexdigest()}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--template", type=Path, default=TEMPLATE)
    args = parser.parse_args()
    results = {}
    for name, supports in PARTS.items():
        with tempfile.TemporaryDirectory(prefix="bambu-ft412-v2-") as folder:
            work = Path(folder)
            input_file = seed_project(work, name, supports, args.template)
            filename = name + "_PETG_X2D_0.4.3mf"
            with (OUT/"QA"/(name+".log")).open("w") as log:
                subprocess.run([BAMBU, "--debug", "2", "--arrange", "0", "--orient", "0",
                                "--slice", "1", "--outputdir", str(work),
                                "--export-3mf", filename, str(input_file)],
                               cwd=work, stdout=log, stderr=subprocess.STDOUT, check=True)
            assert json.loads((work/"result.json").read_text())["return_code"] == 0
            results[name] = verify(work/filename, name, supports)
            (work/filename).replace(OUT/"Bambu"/filename)
            print(name, results[name], flush=True)
    (OUT/"QA"/"laminado.json").write_text(json.dumps(results, indent=2)+"\n")


if __name__ == "__main__":
    main()
