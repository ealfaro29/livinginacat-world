"""Export only mechanical geometry, neutral STEP and diagrams for the public viewer."""
import argparse
import array
import base64
import gzip
import json
import math
from pathlib import Path
import re
import struct
import sys
import zipfile

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
DEST = ROOT / "public/assets/v2/visor"
GROUPS = {"base", "front", "electronics", "toggle", "switchmount", "deck", "phone",
          "rails", "movingY", "movingX", "driveFix", "belt", "arch", "camera", "pod",
          "harness", "power", "herrajesFijos", "herrajesY", "herrajesX", "herrajesOptica", "detalleSwitch"}
EXPECTED = {"base": 2, "movingX": 4, "movingY": 10}
PUBLIC_NAMES = re.compile(r"[A-Za-z][A-Za-z_0-9-]{0,70}\Z")
SCREW_NAMES = re.compile(r"(?:T_721[39]|Q_M3)_(?:Costura_del_chasis|Asientos_al_piso|Portico_a_carcasa|Panel_de_servicio|Guias_Y|Guia_X|Patines_Y|Patin_X|Motores|Placa_MKS|Altura_camara)_\d\d\Z")
ORDINARY = {"T_7213":14, "T_7219":60, "Q_M3":54}


def little_array(kind, raw):
    out = array.array(kind)
    out.frombytes(raw)
    if sys.byteorder != "little":
        out.byteswap()
    return out


def to_little(values):
    if sys.byteorder != "little":
        values.byteswap()
    return values.tobytes()


def export_meshes(source):
    entries = json.loads(gzip.decompress((source / ".geometria.gz").read_bytes()))
    data = bytearray()
    views, accessors, meshes, nodes, materials = [], [], [], [], []
    color_indices, names, counts, fasteners = {}, set(), {}, dict.fromkeys(ORDINARY, 0)
    def add_view(payload, target, stride=None):
        data.extend(b"\0" * (-len(data) % 4))
        view = {"buffer":0,"byteOffset":len(data),"byteLength":len(payload),"target":target}
        if stride is not None:
            view["byteStride"] = stride
        views.append(view)
        data.extend(payload)
        return len(views) - 1

    def linear(byte):
        s = byte/255
        return s/12.92 if s <= .04045 else ((s+.055)/1.055)**2.4

    for entry in entries:
        name, group, color = (entry[k] for k in ("n", "g", "c"))
        if not PUBLIC_NAMES.fullmatch(name) or name in names or group not in GROUPS or not re.fullmatch(r"#[0-9a-f]{6}",color):
            raise ValueError("Unexpected mesh identifier or material")
        names.add(name)
        counts[group] = 1 + counts.get(group,0)
        for prefix in fasteners:
            if name.startswith(prefix + "_"):
                if not SCREW_NAMES.fullmatch(name):
                    raise ValueError("Unexpected mounting interface")
                fasteners[prefix] += 1
        positions = little_array("f", base64.b64decode(entry["v"],validate=True))
        indices = little_array("I", base64.b64decode(entry["i"],validate=True))
        count = len(positions)//3
        if len(positions)%3 or len(indices)%3 or not count or max(indices)>=count or count>65535:
            raise ValueError("Invalid indexed geometry")
        mm100 = [round(n*100) for n in positions]
        if min(mm100) < -32768 or max(mm100)>32767:
            raise ValueError("Mesh outside quantization extent")
        # VEC3 SHORT attributes must be aligned to four bytes for each vertex.
        packed = array.array("h", [0]*(4*count))
        for axis in range(3):
            packed[axis::4] = array.array("h",mm100[axis::3])
        view = add_view(to_little(packed),34962,8)
        pos_index = len(accessors)
        accessors.append({"bufferView":view,"componentType":5122,"count":count,"type":"VEC3",
                          "min":[min(mm100[k::3]) for k in range(3)],
                          "max":[max(mm100[k::3]) for k in range(3)]})
        view = add_view(to_little(array.array("H",indices)),34963)
        index_index = len(accessors)
        accessors.append({"bufferView":view,"componentType":5123,"count":len(indices),"type":"SCALAR",
                          "min":[min(indices)],"max":[max(indices)]})
        if color not in color_indices:
            color_indices[color] = len(materials)
            rgb = [linear(int(color[i:i+2],16)) for i in (1,3,5)]
            metal = color in ("#b4c3c8","#d0d8d8")
            materials.append({"name":color,"pbrMetallicRoughness":{"baseColorFactor":[*rgb,1],
                              "metallicFactor":.54 if metal else .04,"roughnessFactor":.37 if metal else .64}})
        primitive = {"attributes":{"POSITION":pos_index},"indices":index_index,"material":color_indices[color]}
        meshes.append({"primitives":[primitive]})
        nodes.append({"name":name,"mesh":len(meshes)-1,"extras":{"group":group}})
    if any(counts.get(k)!=v for k,v in EXPECTED.items()) or fasteners!=ORDINARY:
        raise ValueError("CAD revision differs from the published fastener schedule")
    # Restore millimetres in the workshop. GLB uses metres and Y-up.
    root = len(nodes)
    nodes.append({"name":"FT412 V2","children":list(range(root)),
                  "matrix":[.00001,0,0,0, 0,0,-.00001,0, 0,.00001,0,0, 0,0,0,1]})
    data.extend(b"\0"*(-len(data)%4))
    doc = {"asset":{"version":"2.0","generator":"FT412"},"scene":0,"scenes":[{"nodes":[root]}],
           "extensionsUsed":["KHR_mesh_quantization"],"extensionsRequired":["KHR_mesh_quantization"],
           "nodes":nodes,"meshes":meshes,"materials":materials,"accessors":accessors,"bufferViews":views,
           "buffers":[{"byteLength":len(data)}]}
    head=json.dumps(doc,separators=(",",":"),ensure_ascii=True,allow_nan=False).encode()
    head+=b" "*(-len(head)%4)
    total=12+8+len(head)+8+len(data)
    (DEST/"consola.glb").write_bytes(struct.pack("<4sII",b"glTF",2,total) +
        struct.pack("<I4s",len(head),b"JSON")+head+struct.pack("<I4s",len(data),b"BIN\x00")+data)


def publish_step(source):
    data=(source/"FT412-V2.step").read_bytes()
    forbidden = rb"/Users/|/private/|/var/folders/|/home/|[a-z0-9._+-]+@[a-z0-9.-]+\.[a-z]+|https?://|TBA\d{9,}|1Z[A-Z0-9]{16}"
    if re.search(forbidden,data,re.I) or not data.startswith(b"ISO-10303-21;") or b"END-ISO-10303-21;" not in data:
        raise ValueError("Unexpected STEP references")
    if not re.search(rb"FILE_NAME\('[^']+',\s*'[^']+',\('Author'\),\('Open CASCADE'\),\s*'Open CASCADE STEP processor [^']+','build123d','Unknown'\);",data):
        raise ValueError("Inspect author metadata before releasing this model")
    name=zipfile.ZipInfo("FT412-V2.step",(2026,11,23,0,0,0))
    name.compress_type=zipfile.ZIP_DEFLATED
    name.create_system=3
    name.external_attr=0o100644<<16
    with zipfile.ZipFile(DEST/"ft412-v2-step.zip","w",compression=zipfile.ZIP_DEFLATED,compresslevel=9) as archive:
        archive.writestr(name,data,compresslevel=9)


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("revision",type=Path,help="Directory of the approved mechanical revision")
    source=ap.parse_args().revision
    DEST.mkdir(parents=True,exist_ok=True)
    export_meshes(source)
    publish_step(source)
    inputs={"herrajes":source/"FT412-V2-Herrajes.png"}
    for mode in ("outside","hardware","travel","optics","switch","electronics"):
        angle="side" if mode=="optics" else "iso"
        inputs[mode]=source/".revision"/(mode+"-"+angle+".png")
    for name, path in inputs.items():
        with Image.open(path) as original:
            image=original.convert("RGB")
            image.save(DEST/(name+".webp"),format="WEBP",quality=88,method=6,exif=b"",icc_profile=b"")
if __name__=="__main__":
    main()
