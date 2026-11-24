"""FT412 Bento v1. Millimetres. Python: manifold3d, trimesh, numpy, matplotlib.
Independent assembly accessory. Does not change the machine or its inventory.
"""
import json, math, hashlib, os
from pathlib import Path
import numpy as np
import trimesh
import manifold3d as mf
from matplotlib.textpath import TextPath
from matplotlib.font_manager import FontProperties

OUT=Path(os.environ.get('FT412_BENTO_OUTPUT',str(Path(__file__).resolve().parents[1] if Path(__file__).parent.name=='Fuente' else Path(__file__).resolve().parent)))
W,D=212.,180.
BASE,WALL,PART=2.0,2.0,1.6
RIM_HEIGHT,CLEARANCE=2.4,.35
FONT=FontProperties(family='DejaVu Sans',weight='bold')

def rr(w,d,r=5,n=12):
    pts=[]
    for cx,cy,a in [(w/2-r,-d/2+r,-90),(w/2-r,d/2-r,0),(-w/2+r,d/2-r,90),(-w/2+r,-d/2+r,180)]:
        for t in np.linspace(a,a+90,n,endpoint=False):
            pts.append([cx+r*math.cos(math.radians(t)),cy+r*math.sin(math.radians(t))])
    return np.array(pts)

def cross(w,d,r=5): return mf.CrossSection([rr(w,d,r)],mf.FillRule.EvenOdd)
def extr(w,d,r,h,z=0): return cross(w,d,r).extrude(h).translate([0,0,z])
def loft(sections):
    # sections = [(w, d, radius, z)]; aligned, equally sampled rings.
    vertices=np.concatenate([np.column_stack((rr(w,d,r),np.full(48,z))) for w,d,r,z in sections])
    faces=[]; n=48
    for k in range(len(sections)-1):
        for i in range(n):
            a=k*n+i;b=k*n+(i+1)%n;c=b+n;d=a+n
            faces.extend([[a,b,c],[a,c,d]])
    faces += [[0,i+1,i] for i in range(1,n-1)]
    off=(len(sections)-1)*n
    faces += [[off,off+i,off+i+1] for i in range(1,n-1)]
    m=mf.Manifold(mf.Mesh64(vertices,np.asarray(faces,dtype=np.uint64)))
    assert m.status()==mf.Error.NoError
    return m

def text(s,height,maxwidth):
    tp=TextPath((0,0),s,size=10,prop=FONT)
    cs=mf.CrossSection(tp.to_polygons(),mf.FillRule.EvenOdd)
    xmin,ymin,xmax,ymax=cs.bounds()
    scale=min(height/(ymax-ymin),maxwidth/(xmax-xmin))
    return cs.translate([-xmin,-ymin]).scale([scale,scale])

def raised(s,height,width,x,y,z,depth=.6):
    cs=text(s,height,width);x0,y0,x1,y1=cs.bounds()
    return cs.translate([x-(x1-x0)/2,y]).extrude(depth).translate([0,0,z-.08])

TRAYS = [{'file': '01_Tornillos',
  'name': '01 TORNILLOS',
  'height': 22,
  'cols': 4,
  'rows': 4,
  'cells': [{'code': 'A01',
             'title': 'M3x6',
             'detail': 'BOTON',
             'col': 0,
             'row': 0,
             'colspan': 1,
             'rowspan': 1},
            {'code': 'A02',
             'title': 'M3x8',
             'detail': 'BOTON',
             'col': 1,
             'row': 0,
             'colspan': 1,
             'rowspan': 1},
            {'code': 'A03',
             'title': 'M3x10',
             'detail': 'BOTON',
             'col': 2,
             'row': 0,
             'colspan': 1,
             'rowspan': 1},
            {'code': 'A04',
             'title': 'M3x16',
             'detail': 'BOTON',
             'col': 3,
             'row': 0,
             'colspan': 1,
             'rowspan': 1},
            {'code': 'A05',
             'title': 'M3x25',
             'detail': 'BOTON',
             'col': 0,
             'row': 1,
             'colspan': 1,
             'rowspan': 1},
            {'code': 'A06',
             'title': 'M5x10',
             'detail': 'BOTON',
             'col': 1,
             'row': 1,
             'colspan': 1,
             'rowspan': 1},
            {'code': 'A07',
             'title': 'M5x12',
             'detail': 'BOTON',
             'col': 2,
             'row': 1,
             'colspan': 1,
             'rowspan': 1},
            {'code': 'A08',
             'title': 'M5x16',
             'detail': 'BOTON',
             'col': 3,
             'row': 1,
             'colspan': 1,
             'rowspan': 1},
            {'code': 'A09',
             'title': 'M5x20',
             'detail': 'BOTON',
             'col': 0,
             'row': 2,
             'colspan': 1,
             'rowspan': 1},
            {'code': 'A10',
             'title': 'M3x8',
             'detail': 'AVELLANADO',
             'col': 1,
             'row': 2,
             'colspan': 1,
             'rowspan': 1},
            {'code': 'A11',
             'title': 'M3x10',
             'detail': 'AVELLANADO',
             'col': 2,
             'row': 2,
             'colspan': 1,
             'rowspan': 1},
            {'code': 'A12',
             'title': 'M5x12',
             'detail': 'AVELLANADO',
             'col': 3,
             'row': 2,
             'colspan': 1,
             'rowspan': 1},
            {'code': 'A13',
             'title': 'M4x8',
             'detail': 'ESCUADRA',
             'col': 0,
             'row': 3,
             'colspan': 1,
             'rowspan': 1,
             'customXMM': 0,
             'customWidthMM': 36},
            {'code': 'A14',
             'title': 'EJE 5x10',
             'detail': 'ROSCA M4',
             'col': 1,
             'row': 3,
             'colspan': 1,
             'rowspan': 1,
             'customXMM': 37.6,
             'customWidthMM': 40},
            {'code': 'A15',
             'title': 'EJE 5x20',
             'detail': 'ROSCA M4',
             'col': 2,
             'row': 3,
             'colspan': 1,
             'rowspan': 1,
             'customXMM': 79.2,
             'customWidthMM': 84},
            {'code': 'A16',
             'title': 'RESERVA',
             'detail': 'TORNILLOS',
             'col': 3,
             'row': 3,
             'colspan': 1,
             'rowspan': 1,
             'customXMM': 164.8,
             'customWidthMM': 43.2}]},
 {'file': '02_Tuercas_y_Arandelas',
  'name': '02 TUERCAS Y ARANDELAS',
  'height': 22,
  'cols': 4,
  'rows': 3,
  'cells': [{'code': 'B01',
             'title': 'M3',
             'detail': 'CUADRADA',
             'col': 0,
             'row': 0,
             'colspan': 1,
             'rowspan': 1},
            {'code': 'B02',
             'title': 'M4',
             'detail': 'CUADRADA',
             'col': 1,
             'row': 0,
             'colspan': 1,
             'rowspan': 1},
            {'code': 'B03',
             'title': 'M5',
             'detail': 'CUADRADA',
             'col': 2,
             'row': 0,
             'colspan': 1,
             'rowspan': 1},
            {'code': 'B04',
             'title': 'M4 PERFIL',
             'detail': 'KIT ESCUADRA',
             'col': 3,
             'row': 0,
             'colspan': 1,
             'rowspan': 1},
            {'code': 'B05',
             'title': 'M3 PERFIL',
             'detail': 'RN05BM3',
             'col': 0,
             'row': 1,
             'colspan': 1,
             'rowspan': 1},
            {'code': 'B06',
             'title': 'M5 PERFIL',
             'detail': 'RN05BM5',
             'col': 1,
             'row': 1,
             'colspan': 1,
             'rowspan': 1},
            {'code': 'B07',
             'title': 'M5 PLANA',
             'detail': 'DIN 125',
             'col': 2,
             'row': 1,
             'colspan': 1,
             'rowspan': 1},
            {'code': 'B08',
             'title': '5 / 10 x 9',
             'detail': 'SEPARADOR',
             'col': 3,
             'row': 1,
             'colspan': 1,
             'rowspan': 1},
            {'code': 'B09',
             'title': '0.1 mm',
             'detail': 'SHIM 5 / 8',
             'col': 0,
             'row': 2,
             'colspan': 1,
             'rowspan': 1},
            {'code': 'B10',
             'title': '0.2 mm',
             'detail': 'SHIM 5 / 8',
             'col': 1,
             'row': 2,
             'colspan': 1,
             'rowspan': 1},
            {'code': 'B11',
             'title': '0.3 mm',
             'detail': 'SHIM 5 / 8',
             'col': 2,
             'row': 2,
             'colspan': 1,
             'rowspan': 1},
            {'code': 'B12',
             'title': '0.5 mm',
             'detail': 'SHIM 5 / 8',
             'col': 3,
             'row': 2,
             'colspan': 1,
             'rowspan': 1}]},
 {'file': '03_Piezas_Pequenas',
  'name': '03 PIEZAS PEQUENAS',
  'height': 36,
  'cols': 4,
  'rows': 3,
  'cells': [{'code': 'C01',
             'title': 'ESCUADRAS',
             'detail': 'GS20-05W',
             'col': 0,
             'row': 0,
             'colspan': 2,
             'rowspan': 1},
            {'code': 'C02',
             'title': 'SOLENOIDE',
             'detail': 'ADAFRUIT 412',
             'col': 2,
             'row': 0,
             'colspan': 2,
             'rowspan': 1},
            {'code': 'C03',
             'title': 'PLACAS',
             'detail': '40 x 18',
             'col': 0,
             'row': 1,
             'colspan': 1,
             'rowspan': 1},
            {'code': 'C04',
             'title': 'POLEAS LISAS',
             'detail': 'AGUJERO 5',
             'col': 1,
             'row': 1,
             'colspan': 1,
             'rowspan': 1},
            {'code': 'C05',
             'title': 'DENTADAS',
             'detail': 'POLEAS LOCAS',
             'col': 2,
             'row': 1,
             'colspan': 1,
             'rowspan': 1},
            {'code': 'C06',
             'title': 'POLEAS MOTOR',
             'detail': 'GT2 20T',
             'col': 3,
             'row': 1,
             'colspan': 1,
             'rowspan': 1},
            {'code': 'C07',
             'title': 'PUNTAS',
             'detail': 'MALLA 7 mm',
             'col': 0,
             'row': 2,
             'colspan': 1,
             'rowspan': 1},
            {'code': 'C08',
             'title': 'S301T / FUSIBLE',
             'detail': 'Y PORTAFUSIBLE',
             'col': 1,
             'row': 2,
             'colspan': 1,
             'rowspan': 1},
            {'code': 'C09',
             'title': 'CABLES JST',
             'detail': 'PH3 / XH3',
             'col': 2,
             'row': 2,
             'colspan': 1,
             'rowspan': 1},
            {'code': 'C10',
             'title': 'DRIVERS',
             'detail': 'EN BOLSA ESD',
             'col': 3,
             'row': 2,
             'colspan': 1,
             'rowspan': 1}]}]

def make_tray(t):
    H=t['height']
    solid=loft([(W,D,6,0),(W,D,6,H-2),(W+4,D+4,8,H),(W+4,D+4,8,H+RIM_HEIGHT)])
    solid=solid-extr(W+2*CLEARANCE,D+2*CLEARANCE,6+CLEARANCE,RIM_HEIGHT+.2,H)
    stepX=(W-2*WALL+PART)/t['cols']; stepY=(D-2*WALL+PART)/t['rows']
    holes=[]; additions=[]
    for c in t['cells']:
        cw=c['colspan']*stepX-PART;ch=c['rowspan']*stepY-PART
        x=-W/2+WALL+c['col']*stepX;y=-D/2+WALL+c['row']*stepY
        if 'customXMM' in c:x=-W/2+WALL+c['customXMM'];cw=c['customWidthMM']
        cx=x+cw/2;cy=y+ch/2
        # 45-degree internal floor chamfer makes it easier to retrieve hardware.
        cavity=loft([(cw-4,ch-4,1,BASE),(cw,ch,3,BASE+2),(cw,ch,3,H+RIM_HEIGHT+1)]).translate([cx,cy,0])
        holes.append(cavity)
        # Self-supporting 45-degree shelf keeps labels above loose hardware.
        zz=H-3.2;dep=9.0
        pts=np.array([[a,b,z] for a in [x+2,x+cw-2] for b,z in [(y-.4,zz-dep-.4),(y-.4,zz),(y+dep,zz)]])
        wedge=trimesh.convex.convex_hull(pts)
        additions.append(mf.Manifold(mf.Mesh64(np.asarray(wedge.vertices),np.asarray(wedge.faces,dtype=np.uint64))))
        additions.append(raised(c['title'],3.1,cw-7,cx,y+5,zz))
        additions.append(raised(c['detail'],2.35,cw-7,cx,y+1,zz))
        c['insideMM']=[round(cw,3),round(ch,3),round(H-BASE,3)]
        c['pocketXY']=[x,y,cw,ch]
        c['clearLengthBeyondLabelMM']=round(ch-dep,3)
    solid=mf.Manifold.batch_boolean([solid]+holes,mf.OpType.Subtract)
    solid=mf.Manifold.batch_boolean([solid]+additions,mf.OpType.Add)
    # Broad, engraved front identifier. Cuts only 0.55 mm into the 2.4 mm wall.
    label=text(t['name'],4.0,180).extrude(.7).rotate([90,0,0])
    bb=label.bounding_box();label=label.translate([-(bb[0]+bb[3])/2,-D/2+.55,9-bb[2]])
    solid=solid-label
    return solid

def save(m,stem):
    m=m.simplify(0.00001)
    assert m.status()==mf.Error.NoError and len(m.decompose())==1,(stem,m.status(),len(m.decompose()))
    raw=m.to_mesh64();mesh=trimesh.Trimesh(np.asarray(raw.vert_properties)[:,:3],np.asarray(raw.tri_verts),process=True)
    if not mesh.is_watertight:
        print('Mesh diagnostic',stem,len(mesh.vertices),len(mesh.faces),mesh.is_watertight,mesh.is_winding_consistent,mesh.volume,flush=True)
    assert mesh.is_watertight and mesh.is_winding_consistent and mesh.volume>0
    path=OUT/'STL'/f'{stem}.stl';mesh.export(path)
    reload=trimesh.load_mesh(path,process=True)
    assert reload.is_watertight and reload.is_winding_consistent
    return dict(file=path.name,sha256=hashlib.sha256(path.read_bytes()).hexdigest(),triangles=len(mesh.faces),boundsMM=mesh.bounds.tolist(),sizeMM=mesh.extents.tolist(),volumeCM3=round(mesh.volume/1000,3),watertight=True,consistentNormals=True,connectedComponents=len(m.decompose()))

def main():
    (OUT/"STL").mkdir(parents=True,exist_ok=True)
    (OUT/"Fuente").mkdir(parents=True,exist_ok=True)
    models=[]; shapes=[]
    for t in TRAYS:
        print('Generating',t['file'],flush=True);m=make_tray(t);shapes.append(m);models.append(save(m,t['file']))
    lid=extr(W,D,6,2.4)
    # A solid grip rib, not a bridge or unsupported handle.
    grip=loft([(84,18,6,2.3),(80,14,5,7.2)])
    lid=lid+grip+raised('FT412',7,70,0,28,2.4,.8)+raised('BENTO / V1',3.3,110,0,-36,2.4,.6)
    models.append(save(lid,'04_Tapa'))
    # Matching small coupon: real rim geometry and the bottom corner of a tray.
    crop=mf.Manifold.cube([32,32,9]).translate([-W/2-3,-D/2-3,17])
    rim_sample=loft([(W,D,6,17),(W,D,6,20),(W+4,D+4,8,22),(W+4,D+4,8,24.4)])
    rim_sample=rim_sample-extr(W-2*WALL,D-2*WALL,6-WALL,10,16.9)-extr(W+2*CLEARANCE,D+2*CLEARANCE,6+CLEARANCE,3,22)
    receiver=(rim_sample^crop).translate([W/2+3,D/2+3,-17])
    male=extr(W,D,6,2.4)^mf.Manifold.cube([28,28,3]).translate([-W/2,-D/2,-.1])
    male=male.translate([W/2+45,D/2,0])
    # Print coupon as two independent solids intentionally.
    for name,m in [('00_Prueba_Encaje_Base',receiver),('00_Prueba_Encaje_Esquina',male)]:models.append(save(m,name))
    collisions=[]
    for lo,hi in [(shapes[0],shapes[1]),(shapes[1],shapes[2]),(shapes[2],lid)]:
        H=22 if lo is not shapes[2] else 36
        collisions.append(round((lo^hi.translate([0,0,H])).volume(),9))
    assert max(collisions)<.0001,collisions
    spec=dict(version=1,units='mm',materialPreparation='PLA',nozzleMM=.4,bodyMM=[W,D],maximumFootprintMM=[W+4,D+4],stackPitchMM=[22,22,36],closedHeightMM=87.2,radialStackClearanceMM=CLEARANCE,floorMM=BASE,dividerMM=PART,outerWallMM=WALL,rimHeightMM=RIM_HEIGHT,compartments=sum(len(t['cells']) for t in TRAYS),trays=TRAYS,models=models,nominalStackIntersectionVolumeMM3=collisions,physicalFitTested=False)
    (OUT/'Fuente'/'diseno.json').write_text(json.dumps(spec,ensure_ascii=False,indent=2))
    print(json.dumps(dict(compartments=spec['compartments'],volumes=[x['volumeCM3'] for x in models],collisionMM3=collisions),indent=2))

if __name__=='__main__':main()
