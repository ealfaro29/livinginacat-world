# /// script
# requires-python = ">=3.12"
# dependencies = ["build123d==0.13.0", "trimesh==5.2.1"]
# ///
"""FT412 V2, estudio de distribución. Milímetros. X derecha, Y fondo, Z arriba."""
from pathlib import Path
from math import pi, atan, tan, radians, sin, cos, sqrt, dist
import base64, gzip, json, struct
import trimesh
from build123d import (
    Align, Axis, Box, Color, Compound, Cylinder, Plane, Polygon, Pos,
    RectangleRounded, Vector, export_step, export_stl, extrude, import_step,
)

HERE = Path(__file__).resolve().parent
if (HERE/'referencias').is_dir():
    CAD=PORTAL=HERE/'referencias'
else:
    project=HERE.parents[2]
    CAD=project/'hardware/ft412/step'
    PORTAL=project/'hardware/ft412-accessories/marco-camara/FT412_Marco_Camara_Adafruit_REV02'
W, D, H = 324., 398., 354.
BASE, RIM = 80., 132.
FRONT = (D-355)/2
BED = FRONT+157.5
ARCH = BED+80
GLASS = BASE+20+3+1+7.8  # seat, EVA nominal, iPhone 14
LENS = GLASS+155
GANTRY = BED+64
E = .05
CENTER_MIN = (Align.CENTER, Align.CENTER, Align.MIN)

PALETTE = {
    "shell":"#c5c1b4", "graphite":"#343f48", "edge":"#242c33", "black":"#22272a",
    "print":"#237778", "secondary":"#40545a", "steel":"#b4c3c8", "light":"#d0d8d8",
    "board":"#29674d", "blue":"#46689a", "amber":"#e7a955", "screen":"#477a86",
    "belt":"#474e53", "accent":"#51c7af", "reserved":"#e5ac60", "warm":"#ac774a",
}
parts = []
def box(x0,x1,y0,y1,z0,z1):
    return Pos(x0,y0,z0)*Box(x1-x0,y1-y0,z1-z0,align=(Align.MIN,)*3)
def rounded(cx,cy,z,w,d,h,r):
    return Pos(cx,cy,z)*extrude(RectangleRounded(w,d,r),amount=h)
def cylinder(x,y,z,diam,height,axis=(0,0,1)):
    return Plane(origin=(x,y,z),z_dir=axis).location*Cylinder(diam/2,height,align=CENTER_MIN)
def yz(points,x0,x1):
    pl=Plane((x0,0,0),(0,1,0),(1,0,0))
    return extrude(pl*Polygon(*points,align=None),amount=x1-x0,dir=(1,0,0))
def xz(points,y0,y1):
    pl=Plane((0,y0,0),(1,0,0),(0,-1,0))
    return extrude(pl*Polygon(*points,align=None),amount=y1-y0,dir=(0,1,0))
def joined(shapes):
    return shapes[0].fuse(*shapes[1:]).clean() if len(shapes)>1 else shapes[0]
def add(key,group,color,shape,print_part=False):
    solids=shape.solids()
    if not solids or not all(s.is_valid for s in solids):
        raise ValueError(f"Sólido inválido: {key}")
    if print_part and len(solids)!=1:
        raise ValueError(f"{key} tiene {len(solids)} cuerpos")
    shape.label=key
    shape.color=Color(PALETTE[color])
    parts.append((key,group,color,shape,print_part))
    return shape
def quadrants(prefix,group,color,shape):
    # Seam clearance is shown in full size. The front LCD sits within one quarter.
    for side,xa,xb in [('I',-W, -.15),('D',.15,W)]:
        for end,ya,yb in [('F',-10,D/2-.15),('T',D/2+.15,D+10)]:
            tile=shape & box(xa,xb,ya,yb,-1,H+1)
            add(f"{prefix}_{side}{end}", group,color,tile,True)
def rod(a,b,r):
    v=Vector(*b)-Vector(*a)
    return cylinder(*a,2*r,v.length,tuple(v.normalized()))
def cable(key,points,r=1.9,color='black',group='cables'):
    # Routing centerlines. Bend radii and connector plug envelopes are separate design work.
    add(key,group,color,Compound(children=[rod(a,b,r) for a,b in zip(points,points[1:])]))

# Closed lower equipment compartment and structural perimeter
outer=rounded(0,D/2,4,W-6,D-8,128,14)
inner=rounded(0,D/2,3,W-12,D-14,130,11)
wall=outer.cut(inner)
cuts=[box(-96.5,-31.5,-1,11,19,67), cylinder(90,-1,43,12.7,15,(0,1,0)),
      box(65,113,D-10,D+1,30,58)]
for xx in (-64-36.5,-64+36.5):
    for zz in (43-22.25,43+22.25):
        cuts.append(cylinder(xx,-1,zz,4.2,16,(0,1,0)))
for yy in list(range(40,143,9))+list(range(248,370,9)):
    for zz in (27,45,63):
        cuts.append(box(-W/2-1,W/2+1,yy,yy+5.5,zz,zz+11))
# Two recessed grip pockets in the front skirt give access to the lift-off nose.
cuts.extend([rounded(x,5,105,43,13,5,2.2) for x in (-82,82)])
wall=wall.cut(*cuts)
quadrants("Faldon","flanc","graphite",wall)
floor=rounded(0,D/2,4,W-13,D-15,3,10)
quadrants("Piso_de_servicio","floor","secondary",floor)
for i,x in enumerate((-134,134)):
    for j,y in enumerate((25,D-25)):
        add(f"Pata_{i}{j}",'floor','edge',rounded(x,y,0,31,23,4,5),True)
deck=rounded(0,D/2,BASE-3,W-14,D-16,3,9)
tie_down_y=[FRONT+72,FRONT+150,FRONT+263,FRONT+322]
deck=deck.cut(*(cylinder(side*87,yy,BASE-4,4.6,5) for side in (-1,1) for yy in tie_down_y))
deck=deck.cut(*(rounded(x,y,BASE-4,w,d,6,3) for x,y,w,d in
               [(-135,326,19,29),(134,322,21,34),(0,90,18,14),(149,ARCH+26,12,22)]))
quadrants("Tabique_superior","deck","secondary",deck)

# Screen window, recessed bezel and mechanical cut-off. Outer case includes their projection.
bezel=box(-108,-20,0,5,14,72).cut(box(-95.5,-32.5,-1,6,20,66))
add("Bisel_TS24_5mm","front","edge",bezel,True)
add("TS24_vidrio_62x45","front","screen",box(-95,-33,2.1,4.1,20.5,65.5))
add("TS24_placa_80x50","pcb","board",box(-104,-24,9,11,18,68))
add("TS24_cintas","cables","warm",Compound(children=[
    box(-90,-77,11,61,27,28.5),box(-67,-54,11,61,27,28.5)]))
add("S301T_cuerpo_y_palanca","front","steel",Compound(children=[
    box(81.5,98.5,8,40,34.5,51.5),cylinder(90,1,43,15.4,4,(0,1,0)),
    rod((90,1.8,43),(90,.9,52),2.1)]))

# Lift-off enclosure. Front opening for light, faceted sides, vents away from rails.
outline=[(0,RIM+.4),(0,175),(42,225),(120,H),(270,H),(D,249),(D,RIM+.4)]
inside=[(3,RIM-1),(3,174),(44.5,223),(122,H-3.2),(269,H-3.2),(D-3,247.5),(D-3,RIM-1)]
cowl=yz(outline,-W/2,W/2).cut(yz(inside,-W/2+3,W/2-3))
hoodcuts=[box(-91,91,-5,57,158,258)]
for y in range(43,126,13):
    hoodcuts.append(yz([(y,152),(y+5,152),(y+25,192),(y+20,192)],-W/2-1,W/2+1))
for y in range(286,361,12):
    hoodcuts.append(yz([(y,159),(y+5,159),(y+27,205),(y+22,205)],-W/2-1,W/2+1))
for x in (-118,-106,-94,94,106,118):
    hoodcuts.append(rounded(x,234,H-4,5,56,6,2.3))
# Rear finger recess doubles as a light slot. No rib crosses the camera keep-out.
hoodcuts.append(rounded(0,259,H-4,58,12,7,5.8))
cowl=cowl.cut(*hoodcuts)
quadrants("Cubierta","hood","shell",cowl)

# Single uninterrupted seat under each full Y rail. No aluminum, printed outer twin slots.
def long_station(side,ya,yb):
    shape=box(95,115,ya,yb,BASE,BASE+40)
    slot=[(-2.7,40.5),(2.7,40.5),(2.7,38.1),(4.65,37),(4.65,35.6),
          (3,33.6),(-3,33.6),(-4.65,35.6),(-4.65,37),(-2.7,38.1)]
    holes=[xz([(105+x,BASE+z) for x,z in slot],ya-1,yb+1)]
    for z in (BASE+10,BASE+30):
        section=[(116,-2.7),(113.15,-2.7),(112.25,-4.65),(110.6,-4.65),
                 (109.65,-3.6),(109.65,3.6),(110.6,4.65),(112.25,4.65),
                 (113.15,2.7),(116,2.7)]
        holes.append(xz([(x,z+v) for x,v in section],ya-1,yb+1))
    holes.append(xz([(97.4,BASE+15),(101.9,BASE+10.5),(106.3,BASE+15),
                     (106.3,BASE+24),(101.9,BASE+28.5),(97.4,BASE+24)],ya-1,yb+1))
    for seam in (FRONT+37.5,FRONT+295.5):
        for direction,edge in [(1,ya),(-1,yb)]:
            if abs(seam-edge)<.01:
                yy=seam+8*direction
                holes.append(cylinder(94,yy,BASE+6,3.4,12,(1,0,0)))
                holes.append(box(98.4,101.2,min(seam,yy)-2.9,max(seam,yy)+2.9,BASE+3.1,BASE+8.9))
    for yy in tie_down_y:
        if ya+8<yy<yb-8:
            shape=shape.fuse(rounded(90.4,yy,BASE,19.6,16,5,3))
            holes.append(cylinder(87,yy,BASE-1,4.6,7))
    if side==1 and ya<FRONT+286.5<yb:
        yy=FRONT+286.5
        holes.append(box(108,116,yy-3.1,yy+3.1,BASE+34.5,BASE+37.5))
    section=shape.cut(*holes).clean()
    return section if side==1 else section.mirror(Plane.YZ)
rails=[]
for side,tag in [(-1,"I"),(1,"D")]:
    for label,start,end in [('Frente',0,37.5),('Asiento',37.5,295.5),('Cola',295.5,355)]:
        support=long_station(side,FRONT+start,FRONT+end)
        add(f"Perfil_Y_{tag}_{label}",'structure','print',support,True)
        if label=='Asiento': rails.append(support)
    # Positive location at each splice, beneath the continuous steel rail.
    for j,y in enumerate((FRONT+37.5,FRONT+295.5)):
        x=side*95
        plate=box(x-2.9 if side>0 else x,x if side>0 else x+2.9,y-15,y+15,BASE+.2,BASE+13)
        for yy in (y-8,y+8):
            plate=plate.cut(cylinder(x-4,yy,BASE+6,3.5,8,(1,0,0)))
        add(f"Union_lateral_{tag}_{j}",'structure','secondary',plate,True)
for name,y,hi in [('Frente',FRONT+10,40),('Fondo',FRONT+345,40),
                  ('Cama_F',FRONT+107.5,20),('Cama_T',FRONT+207.5,20)]:
    h=10 if name.startswith('Cama') else 40
    z=BASE+hi
    shape=box(-95,95,y-10,y+10,z-h,z)
    shape=shape.cut(box(-96,96,y-2.7,y+2.7,z-6.4,z+1),
                    box(-96,96,y-4.7,y+4.7,z-6.4,z-2.2))
    add("Travesano_"+name,'structure','print',shape,True)

def steel_rail(x,y,z,length,transverse=False):
    rail=box(-4.5,4.5,0,length,0,6.5)
    for u in range(5,int(length),20):
        rail=rail.cut(cylinder(0,u,-.5,3.5,8),cylinder(0,u,3.2,5.9,4))
    if transverse: rail=rail.rotate(Axis.Z,-90)
    return rail.translate((x,y,z))
for s,tag in [(-1,"I"),(1,"D")]:
    add("MGN9_Y_"+tag,'motion','steel',steel_rail(s*105,FRONT+41.5,BASE+40,250))
    add("Patin_Y_"+tag,'motion','light',rounded(s*105,GANTRY,BASE+46.5,20,39.9,6.5,1.5))
    outer_pad=box(min(s*113,s*92.5),max(s*113,s*92.5),GANTRY-12,GANTRY+12,BASE+53,BASE+67)
    saddle_arm=box(min(s*113,s*78),max(s*113,s*78),GANTRY-12,GANTRY+12,BASE+62,BASE+67)
    add("Union_XY_"+tag,'motion','secondary',outer_pad.fuse(saddle_arm).clean())
bridge=box(-92.5,92.5,GANTRY-6,GANTRY+6,BASE+43,BASE+62)
bridge=bridge.cut(box(-94,94,GANTRY-2.7,GANTRY+2.7,BASE+55.6,BASE+63),
                  box(-94,94,GANTRY-4.7,GANTRY+4.7,BASE+55.6,BASE+59.8))
add('Puente_X_185','structure','print',bridge,True)
add('MGN9_X_150','motion','steel',steel_rail(-75,GANTRY,BASE+62,150,True))
add('Patin_X','motion','light',rounded(8,GANTRY,BASE+68.5,39.9,20,6.5,1.5))

bed=import_step(CAD/'fdm_phone_bed_x1.step').translate((0,BED,BASE+20))
add("Cama_original_iPhone",'motion','graphite',bed)
add('iPhone14_cuerpo','motion','steel',rounded(0,BED,GLASS-7.8,71.5,146.7,7.0,9))
add('iPhone14_vidrio','motion','black',rounded(0,BED,GLASS-.8,71.15,146.35,.8,8.8))
add('iPhone14_pantalla','motion','screen',rounded(0,BED,GLASS,66.5,140.5,.06,7.2))
add('iPhone14_muesca','motion','black',rounded(0,BED+67.6,GLASS+.07,25,5,.08,1.8))
cable('Lightning_interno',[(0,BED-74,GLASS-4),(0,BED-85,GLASS-4),(0,90,92),(0,90,72)],2)
# Carriage envelope and actuator. Only the phone bed and camera portal use imported V1 solids.
add('Mordaza_carro','motion','graphite',rounded(8,GANTRY-2,BASE+75,40,27,7,2))
add('Portasolenoide','motion','secondary',joined([box(-17,33,GANTRY-15,GANTRY+8,BASE+81.8,BASE+86),
      box(-17,33,GANTRY-17,GANTRY-13,BASE+49,BASE+85)]))
tx,ty=8,GANTRY-25
add('Adafruit_412_cuerpo','motion','steel',box(tx-7,tx+7,ty-8.5,ty+8.5,GLASS+15,GLASS+44.7))
add('Bobina_412','motion','warm',cylinder(tx,ty,GLASS+18,13,24))
for z in (GLASS+20,GLASS+37):
    add(f'Brida_solenoide_{int(z)}','motion','graphite',box(tx-22,tx+22,ty-10.5,ty-8.3,z,z+4))
add('Punta_malla','motion','warm',cylinder(tx,ty,GLASS+2.3,8.8,12.7))
for s,t in [(-1,'A'),(1,'B')]:
    x,y=s*47.5,FRONT+313
    face=BASE+40+(8 if s==-1 else 12)
    add('NEMA17_'+t,'motion','black',rounded(x,y,face-38,42,42,38,3))
    add('Soporte_motor_'+t,'motion','secondary',import_step(CAD/f'fdm_motor_mount_{t}_x1.step').rotate(Axis.Z,90).translate((x,y,face)))
    add('Motriz_'+t,'motion','steel',cylinder(x,y,face+6,13,12))
    for name,px,py,hh in [('delante',s*105,FRONT+30,13),('atras',s*105,FRONT+321,21),
                            ('retorno',s*86,FRONT+332,12),('puente',s*86,GANTRY-7,15)]:
        st=BASE+49 if name!='puente' else BASE+60
        add(f'Polea_{name}_{t}','motion','steel',cylinder(px,py,st,14,hh))
    # Representative visible segments only, without manufacturing data for belt paths.
    cable('Correa_'+t,[(s*112,FRONT+30,BASE+55+(s+1)*4.5),
                         (s*112,FRONT+320,BASE+55+(s+1)*4.5)],2.4,'belt','motion')
    cable('Correa_transversal_'+t,[(s*85,GANTRY-13,BASE+67+(s+1)*4.5),
                                   (8,GANTRY-13,BASE+67+(s+1)*4.5)],2.1,'belt','motion')

# Reuse the exact three B-reps of the print now underway, in their assembled positions.
old=import_step(PORTAL/'FT412_Marco_Camara_Adafruit_REV02.step')
arch=[]
for n,child in enumerate(old.children):
    arch.append(add(['L_V1_izquierda','L_V1_derecha','Travesano_V1_sin_tornillos'][n],
                    'camera','print',child.translate((0,ARCH,BASE+40)),True))
# A small two-face portrait saddle turns the folded foot through 90 degrees.
face_y=ARCH-22
saddle=joined([box(-12,22,face_y-3.4,face_y,BASE+186.8,BASE+211),
               box(-12,22,face_y-.4,face_y+8,BASE+187.2,BASE+189.75),
               box(18.6,22,BED-8,face_y-2,BASE+192,BASE+211)])
saddle=saddle.cut(cylinder(0,face_y-5,BASE+202,6.8,7,(0,1,0)))
saddle=saddle.cut(box(17,24,BED-3.45,BED+3.45,BASE+198,BASE+207),
                  cylinder(17,BED,BASE+198,6.9,9,(1,0,0)),
                  cylinder(17,BED,BASE+207,6.9,9,(1,0,0)))
add('Escuadra_optica_vertical','camera','secondary',saddle,True)
# Mount-to-beam hardware and the camera's photographic thread have separate jobs.
add('C922_carcasa_esquematica','camera','graphite',rounded(0,BED,LENS+2,33,95,24,8))
add('C922_frente','camera','black',rounded(0,BED,LENS+1,30,90,2,7))
add('C922_lente','camera','blue',cylinder(0,BED,LENS,13,2))
add('C922_pie_plegado','camera','black',box(11,18.6,BED-20,BED+21,LENS+24,LENS+53))
cable('USB_C922_en_columna',[(10,BED+35,LENS+18),(26,BED+55,LENS+24),
       (35,ARCH-27,BASE+211),(142,ARCH-27,BASE+211),(146,ARCH-21,BASE+199),
       (146,ARCH-21,BASE+46),(149,ARCH+26,BASE+35),(149,ARCH+26,68)],2.3)
for z in (BASE+75,BASE+147):
    clip=box(140,152,ARCH-24.5,ARCH-17,z,z+4).cut(box(142,150,ARCH-23,ARCH-16.9,z-1,z+5))
    add(f'Clip_camara_{int(z)}','camera','secondary',clip,True)

add('Acceso_referencia_riel','routing','warm',rod((116,FRONT+286.5,BASE+36),(109,FRONT+286.5,BASE+36),1))
# Equipment on separate floor carriers. Plug clearance is reserved around the boards.
def carrier(name,cx,cy,w,d,holes):
    tray=rounded(cx,cy,7,w+7,d+7,3,4)
    for x,y in holes:
        boss=cylinder(x,y,9.9,7,5.1)
        tray=tray.fuse(boss).cut(cylinder(x,y,9,2.7,7))
    add(name,'pcb','secondary',tray.clean(),True)
px,py=66,109
pi_holes=[(px-39+i,py-24.5+j) for i in (0,58) for j in (0,49)]
carrier('Cuna_Pi',px,py,85,56,pi_holes)
add('Raspberry_Pi_5','pcb','board',rounded(px,py,15,85,56,1.6,2.6))
for j in (-18,0,18):
    add('USB_LAN_Pi_'+str(j),'pcb','steel',box(px+29,px+44,py+j-6,py+j+6,16.6,32))
add('Disipador_CanaKit','pcb','steel',rounded(px-4,py,17,53,43,11,2))
add('Fan_CanaKit','pcb','black',rounded(px-4,py,28,40,40,10,3).cut(cylinder(px-4,py,27,31,12)))
add('Fan_buje','pcb','secondary',cylinder(px-4,py,32,13,6))
for angle in range(0,360,60):
    blade=rounded(8.4,0,33,15,4,2,1.6).rotate(Axis.Z,angle).translate((px-4,py,0))
    add('Aspa_'+str(angle),'pcb','secondary',blade)
mx,my=-66,106
mks_holes=[(mx+i,my+j) for i in (-41,41) for j in (-31,31)]
carrier('Cuna_MKS_patron_provisional',mx,my,90,70,mks_holes)
add('MKS_DLC32_V2_2','pcb','black',rounded(mx,my,15,90,70,1.6,2.5))
for i in (-15,10):
    add('TMC2209_'+str(i),'pcb','blue',box(mx+i-8,mx+i+8,my+9,my+29,17,26))
    for f in (-5,-1.7,1.7,5):
        add('Aleta_'+str(i)+'_'+str(f),'pcb','steel',box(mx+i+f-0.6,mx+i+f+.6,my+10,my+28,26,35))
add('USB_MKS','pcb','steel',box(mx+32,mx+46,my-22,my-8,16.6,28))
add('ESP32','pcb','light',box(mx-37,mx-18,my-25,my-5,16.6,20))
for name,x,y,w,d,h,col in [('Caja_Adafruit_5648',-72,189,39.6,24.4,13.2,'print'),
                            ('Portafusible_3A',12,185,48,28,26,'edge')]:
    add(name,'pcb',col,rounded(x,y,7,w,d,h,3))
add('Fusible_3A','pcb','warm',rounded(12,185,32.7,20,7,4,1.5))
for side in (-1,1):
    x=side*134
    for n,(ya,yb) in enumerate([(44,183),(186,226)]):
        tray=box(x-8,x+8,ya,yb,7,17).cut(box(x-5.4,x+5.4,ya-1,yb+1,9,18))
        add(f'Canal_{side}_{n}','routing','secondary',tray,True)
cable('USB_MKS_a_Pi',[(mx+46,my-15,22),(-7,91,22),(-7,52,17),(121,52,17),
                    (126,67,20),(126,110,23),(px+44,109,23)],2.2,'black')
cable('USB_C922_a_Pi',[(149,ARCH+26,68),(149,ARCH+26,39),(149,208,32),(149,151,27),
                        (128,145,25),(126,91,23),(px+44,91,23)],2.3)
cable('Lazo_superior_solenoide',[(8,GANTRY-22,GLASS+44),(30,GANTRY-18,183),
       (72,GANTRY+5,191),(112,GANTRY+35,179),(132,310,150),(134,322,125),(134,322,80)],1.9,'black','motion')
cable('Mazo_12V',[(89,36,39),(89,43,20),(134,47,14),(134,215,14),
                  (114,221,14),(20,221,14),(15,199,18)],2.4,'warm')
# Rear dry volume for intact power modules and a finished, integration-rated distributor.
# A schematic guard divides service and power; no AC wiring is designed here.
partition=box(-146,146,228,231,7,74).cut(box(105,129,227,232,54,65))
for i,(a,b) in enumerate([(-150,-.15),(.15,150)]):
    add('Separador_energia_'+str(i),'power','graphite',partition & box(a,b,227,232,6,75),True)
for side in (-1,1):
    a,b=sorted((side*143.9,side*146))
    add('Tabique_canal_'+str(side),'power','secondary',box(a,b,230.95,390,7,76),True)
reserve=box(-143,143,238,381,8,74)
add('Reserva_para_fuentes_y_distribuidor','reserve','reserved',reserve)
rear_plate=box(62,116,D-4,D-1,27,61).cut(cylinder(90,D-5,43,14,6,(0,1,0)))
add('Placa_trasera_reemplazable','power','edge',rear_plate,True)

# Design checks on actual geometry, plus explicit limits of the study.
def common_volume(a,b):
    overlap=a & b
    return 0.0 if overlap is None else sum(s.volume for s in overlap.solids())
def pxfit(shape):
    b=shape.bounding_box(); w,d,h=b.size.X,b.size.Y,b.size.Z
    candidates=[]
    for deg in range(0,91):
        t=radians(deg); dx=w*cos(t)+d*sin(t);dy=w*sin(t)+d*cos(t)
        if max(dx,dy)<=246.001 and h<=250.001:
            candidates.append((max(dx,dy),deg,dx,dy,h))
    if not candidates: raise ValueError(f"Área de impresión {shape.label}: {w,d,h}")
    _,angle,dx,dy,z=min(candidates)
    return [angle,*[round(q,1) for q in (dx,dy,z)]]
report={'unidades':'mm','fase':'Anteproyecto de distribución','carcasa':[W,D,H],
        'frente_mecanico_y':FRONT,'centro_cama_y':BED,'distancia_lente_vidrio_nominal':LENS-GLASS,
        'compartimento_util_reservado':[286,143,66],
        'piezas_de_plastico_cabida_X2D':{},'intersecciones_mm3':{}}
for name,g,c,s,printed in parts:
    if printed:report['piezas_de_plastico_cabida_X2D'][name]=pxfit(s)
for i,side in enumerate(('I','D')):
    val=common_volume(arch[i],rails[i]); report['intersecciones_mm3']['L_con_perfil_'+side]=round(val,4)
    assert val<.1,(side,val)
for i,side in enumerate(('I','D')):
    for dy in (10,25,44,75):
        tested=arch[i].translate((0,dy,0))
        material=[s for k,group,_,s,_ in parts if k.startswith("Perfil_Y_"+side)]
        vol=sum(common_volume(tested,item) for item in material)
        assert vol<.1,(side,dy,vol)
        report['intersecciones_mm3'][f'entrada_L_{side}_{dy}']=round(vol,4)
partmap={n:s for n,_,_,s,_ in parts}
for k1,k2 in [('Puente_X_185','Union_XY_I'),('Puente_X_185','Union_XY_D'),('Escuadra_optica_vertical','Travesano_V1_sin_tornillos'),
              ('USB_C922_a_Pi','Tabique_canal_1'),('USB_C922_a_Pi','Separador_energia_1')]:
    vol=common_volume(partmap[k1],partmap[k2]);assert vol<.02,(k1,k2,vol)
    report['intersecciones_mm3'][k1+'_'+k2]=round(vol,4)
for name,g,c,s,_ in parts:
    if g in ('pcb','cables','deck','power','floor','flanc'):
        vol=common_volume(s,reserve)
        if vol>.02: raise ValueError(f"Bahía: {name} {vol}")
# Optical keep-out: conservative folded-camera box used with the long sensor axis along phone.
keepout=box(-22,22,BED-47.5,BED+47.5,LENS-4.5,LENS+71+4.5)
for key,shape in [('camara_cubierta',cowl),('camara_travesano',arch[2])]:
    v=common_volume(keepout,shape); assert v<.02,(key,v)
    report['intersecciones_mm3'][key]=round(v,4)
# Clear of the two metal guides for any fore/aft position of the lightweight bridge.
swept=box(-113.1,113.1,FRONT+41.5,FRONT+291.5,BASE+45,BASE+91)
for key,shape in [('zona_movil_cubierta',cowl),('zona_movil_LI',arch[0]),('zona_movil_LD',arch[1])]:
    v=common_volume(swept,shape); assert v<.02,(key,v)
    report['intersecciones_mm3'][key]=round(v,4)
t=tan(radians(78/2))
report['campo_optico_ideal_largo_ancho_mm']=[round(2*(LENS-GLASS)*t*k/sqrt(16**2+9**2),1) for k in (16,9)]
report['limites']=['La bahía es un volumen reservado. Faltan dimensiones de fuentes conectadas, distribución certificada y ensayo térmico.',
    'Los enchufes, radios de cable, iluminación con cubierta, rigidez, referencia de la punta y montaje final son pendientes.',
    'La comprobación de barrido solo comprende la envolvente definida y la cubierta y las L. Las correas y cables se representan por tramos.',
    'Perfiles, uniones, torres de placas y cierres están en fase de diseño. Cabida por BBox de una pieza no es laminado.']
model=Compound(label="FT412 V2 - Anteproyecto",children=[
    Compound(label=group,children=[s for _,g,_,s,_ in parts if g==group])
    for group in dict.fromkeys(g for _,g,_,_,_ in parts)])
assert export_step(model,HERE/'FT412-V2.step')
reloaded=import_step(HERE/'FT412-V2.step')
report['solidos_step_reabiertos']=len(reloaded.solids())
assert report['solidos_step_reabiertos']==len(model.solids()) and all(s.is_valid for s in reloaded.solids())
# Two actual modules from the assembly are also available as optional prototypes.
out=HERE/'Perfiles'
out.mkdir(exist_ok=True)
report['prototipos_STL']={}
for key,filename,angle in [('Perfil_Y_D_Frente','Extremo_derecho_37-5mm.stl',0),
                           ('Perfil_Y_D_Asiento','Perfil_derecho_258mm.stl',45)]:
    work=partmap[key].rotate(Axis.Z,angle)
    b=work.bounding_box()
    work=work.translate((-(b.min.X+b.max.X)/2,-(b.min.Y+b.max.Y)/2,-b.min.Z))
    path=out/filename
    assert export_stl(work,path,tolerance=.04)
    mesh=trimesh.load_mesh(path)
    assert mesh.is_volume and mesh.is_watertight and len(mesh.split())==1
    assert abs(mesh.volume-work.volume)/work.volume<.001 and min(mesh.bounds[0][2],1) >= -.001
    assert max(mesh.extents[:2])<=246 and mesh.extents[2]<250
    report['prototipos_STL'][filename]={'unidades':'mm','giro_en_cama':angle,
        'dimensiones_en_cama':[round(float(a),2) for a in mesh.extents],
        'una_malla_cerrada':True, 'escala':1, 'laminado':False}
(HERE/'verificacion.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
# Mesh stream is shared by all views; vertices for each face preserve CAD edges.
meshes=[]
for name,group,color,shape,_ in parts:
    v,f=shape.tessellate(.16,.20)
    xyz=[round(a,3) for p in v for a in p]
    idx=[j for tri in f for j in tri]
    def pack(fmt,values):
        return base64.b64encode(struct.pack('<'+str(len(values))+fmt,*values)).decode()
    meshes.append(dict(n=name,g=group,c=PALETTE[color],v=pack('f',xyz),i=pack('I',idx)))
(HERE/'.geometria.gz').write_bytes(gzip.compress(json.dumps(meshes,separators=(',',':')).encode()))
print(f"{len(parts)} elementos; {report['solidos_step_reabiertos']} sólidos; óptica {report['campo_optico_ideal_largo_ancho_mm']}; STEP verificado")
