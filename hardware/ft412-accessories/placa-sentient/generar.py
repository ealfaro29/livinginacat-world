from pathlib import Path
import hashlib, json, math, shutil, zipfile, uuid
import xml.etree.ElementTree as ET
import numpy as np
import trimesh
from shapely.geometry import Polygon, box
from shapely import affinity
from svgpathtools import parse_path

OUT=Path(__file__).parent
LOGO=OUT/"sentient-symbol-original.svg"

svg=ET.parse(LOGO).getroot()
logo=None
for element in svg.iter():
    if element.tag.split('}')[-1]!='path': continue
    for sub in parse_path(element.attrib['d']).continuous_subpaths():
        points=[]
        for seg in sub:
            n=max(3,math.ceil(seg.length(error=1e-5)/.045))
            points.extend((seg.point(i/n).real,seg.point(i/n).imag) for i in range(n))
        polygon=Polygon(points)
        assert polygon.is_valid
        logo=polygon if logo is None else logo.symmetric_difference(polygon)
assert logo.geom_type=='Polygon' and logo.is_valid
minx,miny,maxx,maxy=logo.bounds
scale=40/(maxx-minx)
# Convert SVG's downward Y to a readable, upward Y on the visible front.
logo=affinity.scale(logo,xfact=scale,yfact=-scale,origin=(0,0))
lo=logo.bounds
logo=affinity.translate(logo,37.5-(lo[0]+lo[2])/2,37.5-(lo[1]+lo[3])/2)
outline=box(2.5,2.5,72.5,72.5).buffer(2.5,quad_segs=32)
groove=logo.buffer(.20,quad_segs=16)
assert outline.contains(groove)

def extrude(poly,height,z=0):
    shapes=[poly] if poly.geom_type=='Polygon' else list(poly.geoms)
    meshes=[]
    for shape in shapes:
        m=trimesh.creation.extrude_polygon(shape,height,engine='earcut')
        m.apply_translation([0,0,z]);meshes.append(m)
    return meshes

# A continuous 0.8 mm floor retains the black islands within the symbol.
lower=extrude(outline,.8)
upper=extrude(outline.difference(groove),.8,.8)
base=trimesh.boolean.union(lower+upper,engine='manifold')
badge=extrude(logo,2.4)[0]
assert np.allclose(base.extents,[75,75,1.6],atol=1e-5)
assert np.allclose(badge.extents[:1],[40],atol=1e-5)
meshes={'plate':base,'logo':badge}
names={'plate':'FT412_Placa_Sentient_75x75_Negra_Rebaje_0.8mm','logo':'FT412_Logo_Sentient_Amarillo_Relieve_2.4mm'}
files={}
for key,m in meshes.items():
    assert m.is_watertight and m.is_winding_consistent and len(m.split())==1
    m.remove_unreferenced_vertices()
    path=OUT/(names[key]+'.stl');m.export(path)
    files[key]={'stl':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
        'boundsMM':m.bounds.tolist(),'watertight':True,'connectedComponents':1,'volumeMM3':m.volume}

assembled=badge.copy();assembled.apply_translation([0,0,.8])
intersect=trimesh.boolean.intersection([base,assembled],engine='manifold')
assert abs(intersect.volume)<1e-6
# Horizontal nominal fit is checked in 2D as well as using the final meshes.
assert groove.contains(logo)
qa={'status':'TWO_PART_COSMETIC_PLATE_GEOMETRY_VERIFIED_NOT_PRINTED',
 'sourceLogo':LOGO.name,'sourceLogoSHA256':hashlib.sha256(LOGO.read_bytes()).hexdigest(),
 'widthMM':75,'heightMM':75,'blackPlateThicknessMM':1.6,
 'recessDepthMM':.8,'logoThicknessMM':2.4,'assembledLogoReliefMM':1.6,
 'logoWidthMM':40,'radialFitClearanceMM':.2,'cornerRadiusMM':2.5,
 'physicalParts':2,'clips':0,'mountingHoles':0,
 'originalSupportAndHoneycombUnmodified':True,
 'placement':'Front-facing solid zone; bottom edge above first two electronics-board screws. Keep honeycomb exposed. The requested 75 mm height extends above the original 64 mm solid wing.',
 'physicalFitVerified':False,'printed':False,'printStarted':False,
 'meshAssemblyIntersectionMM3':float(intersect.volume),'files':files}
(OUT/'geometry-verification.json').write_text(json.dumps(qa,indent=2,ensure_ascii=False)+'\n')
