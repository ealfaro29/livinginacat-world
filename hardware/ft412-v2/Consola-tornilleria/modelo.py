# /// script
# requires-python = ">=3.12"
# dependencies = ["build123d==0.13.0", "trimesh==5.2.1"]
# ///
"""FT412 V2. Diseño compacto desde los recorridos, unidades en milímetros.
X hacia la derecha, Y hacia atrás, Z arriba. No requiere archivos CAD de la V1.
"""
from pathlib import Path
from math import radians,sin,cos,sqrt,tan
import base64,gzip,json,struct
import trimesh
from build123d import (Align,Axis,Box,Color,Compound,Cylinder,Plane,Polygon,Pos,
    RectangleRounded,Sphere,Vector,export_step,export_stl,extrude,import_step)
HERE=Path(__file__).resolve().parent
W,D=196.,302.
CX,CY=-5.,138.
L_X,L_Y,RAIL,PATIN=150.,250.,77.5,39.9
Y0=13.
X0=CX-L_X/2
ELECTRONICS_TOP=44.
GLASS=55.
REF=GLASS+35.
OPTICAL=100.                   # medido por el dueño, del vidrio al centro del lente
LENS=GLASS+OPTICAL
H=LENS+71+2+3
SWITCH_FACE,SX,SZ,ANGLE=29.,48.,29.,16.
YRAILZ, XRAILZ=REF,130.5
BEAM_OFFSET=14.
A_Z,B_Z=105.,113.5
CENTER_MIN=(Align.CENTER,Align.CENTER,Align.MIN)
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
def rod(a,b,r):
    v=Vector(*b)-Vector(*a)
    return cylinder(*a,2*r,v.length,tuple(v.normalized()))
def cable(key,points,r=1.9,color='black',group='cables'):
    # Routing centerlines. Bend radii and connector plug envelopes are separate design work.
    add(key,group,color,Compound(children=[rod(a,b,r) for a,b in zip(points,points[1:])]))

def frontpad(x,y,z,w,h,depth,r):
    sketch = Plane((x,y,z),(1,0,0),(0,-1,0))*RectangleRounded(w,h,r)
    return extrude(sketch,amount=depth,dir=(0,1,0))

def rotated_box(x,y,z,w,d,h,r=2):
    return rounded(x,y,z,w,d,h,r)
def lookup(name):
    return next(s for n,g,c,s,p in parts if n==name)
def mirror(x):
    return 2*CX-x

# Lower shell and full-depth rail beds. Fresh construction around the running corridors.
# Every split is in a printed panel; neither steel guide has a joint.
floor=rounded(0,D/2,0,W,D,3,6)
for fore,ya,yb in [('delante',0,144.9),('detras',145.1,D)]:
    add('Piso_'+fore,'base','secondary',floor & box(-100,100,ya,yb,-1,4),True)
skirt=rounded(0,D/2,3,W,D,55,6).cut(rounded(0,D/2,2,W-6,D-6,57,3))
# LCD 65 x 48 at left, toggle at right.
LCD_X,LCD_Z=-46.,32.
skirt=skirt.cut(box(LCD_X-32.5,LCD_X+32.5,-1,5,LCD_Z-24,LCD_Z+24),
    box(SX-30.5,SX+30.5,-1,5,SZ-26,SZ+26),
    cylinder(48,D-5,26,12,7,(0,1,0)))
for xx in (LCD_X-36.5,LCD_X+36.5):
    for zz in (LCD_Z-22.25,LCD_Z+22.25):
        skirt=skirt.cut(cylinder(xx,-1,zz,3.5,6,(0,1,0)))
for yy in list(range(63,116,8))+list(range(157,226,8)):
    skirt=skirt.cut(box(-101,101,yy,yy+3.5,16,29),box(-101,101,yy+2,yy+5.5,33,42))
for side in (-1,1):
    for y in (186,206):
        skirt=skirt.cut(cylinder(side*99.5,y,50,3.4,7,(-side,0,0)),
                        cylinder(side*98.1,y,50,5.8,1.9,(-side,0,0)))
for fore,ya,yb in [('delante',-.1,144.9),('detras',145.1,D+.1)]:
    add('Carcasa_'+fore,'base','graphite',skirt & box(-101,101,ya,yb,0,62),True)
# Front screen layer and accessible right-hand mechanical toggle. The shroud starts at Y=0;
# no installed part projects beyond the measured outer case.
bezel=frontpad(LCD_X,0,LCD_Z,85,55,3,3).cut(frontpad(LCD_X,-1,LCD_Z,65,48,5,1.5))
# Show the front face as part of the wall instead of stacking a bezel through it.
for dx in (-36.5,36.5):
    for dz in (-22.25,22.25):
        bezel=bezel.cut(cylinder(LCD_X+dx,-1,LCD_Z+dz,3.5,6,(0,1,0)))
# The bezel lies on the screen island replacing its skin.
ni=next(i for i,t in enumerate(parts) if t[0]=='Carcasa_delante')
n,g,col,sh,pp=parts.pop(ni)
add(n,g,col,sh.cut(frontpad(LCD_X,-.1,LCD_Z,85,55,3.2,3)),True)
add('Bisel_pantalla_TS24','front','edge',bezel,True)
add('Vidrio_TS24_62x45','front','screen',frontpad(LCD_X,1.2,LCD_Z,62,45,2,1.5))
add('PCB_pantalla_TS24','electronics','board',box(-86,-6,5,6.6,7,57))
# Front switch. Mounting plane is recessed; the rear face stays open to reach both terminals.
# Manufacturer NKK Series S p. A109: shank M12x1, Ø12.5 + Ø3 at 9, panel <=4.7.
well = frontpad(SX,4,SZ,60,50,28,6).cut(frontpad(SX,3,SZ,55,45,26,4))
lip = frontpad(SX,1,SZ,80,57,3,7).cut(frontpad(SX,0,SZ,55,45,5,4))
mount = well.fuse(lip).cut(cylinder(SX,28,SZ,12.5,6,(0,1,0)),
    cylinder(SX,28,SZ+9,3,6,(0,1,0))).clean()
# The switch cup overlaps the front skin. Its separate viewer mesh is cut from this same solid.
# Ring, hex mounting nut and small marks visibly distinguish the two positions.
def ring(x,y,z,d,h,hole):
    return cylinder(x,y,z,d,h,(0,1,0)).cut(cylinder(x,y-.2,z,hole,h+.4,(0,1,0)))
def hex_nut(x,y,z,af,length,inner):
    radius=af/sqrt(3)
    pts=[(x+radius*cos(radians(i*60)),z+radius*sin(radians(i*60))) for i in range(6)]
    return xz(pts,y,y+length).cut(cylinder(x,y-.2,z,inner,length+.4,(0,1,0)))
add('S301T_arandela','toggle','steel',ring(SX,28.1,SZ,16.7,.9,12.05))
add('S301T_tuerca_hexagonal','toggle','light',hex_nut(SX,25.2,SZ,16,2.9,12.05))
add('S301T_casquillo_M12','toggle','steel',ring(SX,22,SZ,12,12,6.3))
add('S301T_cuerpo','toggle','black',frontpad(SX,34,SZ,16,28.5,17.4,1.3))
# 9.6 mm maximum behind the case. Both screw lugs are shown on the service side.
for i,sign in enumerate((-1,1)):
    z=SZ+sign*9
    add('S301T_terminal_'+str(i+1),'toggle','warm',box(SX-3,SX+3,51.4,59.8,z-2.5,z+2.5))
    add('S301T_tornillo_'+str(i+1),'toggle','steel',cylinder(SX,59.6,z,5.7,1.4,(0,1,0)))
def toggle(a):
    pivot=Vector(SX,22,SZ);direction=Vector(0,-cos(radians(a)),sin(radians(a)))
    cap=pivot + direction*(17.5-3.05)
    return rod(tuple(pivot),tuple(cap),2.7).fuse(Pos(*tuple(cap))*Sphere(3.05)).clean()
lever=add('S301T_palanca','toggle','light',toggle(-ANGLE))
add('Marca_I_12V','switchmount','light',box(SX-34.8,SX-33.1,.55,1.05,SZ+7,SZ+14))
add('Marca_O_12V','switchmount','light',ring(SX-34,.55,SZ-10,7,.5,4.3))
# Access with a 16 mm finger as a design proxy. Separate from the guaranteed mechanical throw.
back_wiring=box(SX-10,SX+10,61,78,SZ-17,SZ+17)

# Low separation deck leaves clearance beneath the raised, replaceable phone tray.
deck=rounded(0,138,44,W-6,226,2.8,4)
deck=deck.cut(rounded(CX,CY,43.9,76,151,3.1,9),
              rounded(CX,CY-87,43.9,15,16,3.1,3),rounded(88,168,43.9,10,24,3.1,2))
# Service openings for the recess and both screw-terminal wires, plus six seat feet.
deck=deck.cut(box(SX-31,SX+31,22,33,43,48),box(SX-11,SX+11,32.9,79,43,48))
for sign in (-1,1):
    for yfoot in (65,133,237):
        xfoot=CX+sign*(RAIL+5.5)
        deck=deck.cut(rounded(xfoot,yfoot,43,7.7,14.7,5,2.1))
# Vent the unobstructed right half of the Pi fan and keep ribs in the lid.
for xx in range(43,66,5):
    deck=deck.cut(box(xx,xx+2.7,94,135,43,48))
# Printed U tray and four individually accessible side lugs. Thumb space at front and for Lightning.
tray=rounded(CX,CY,44.4,82,156,2,10)
rim=rounded(CX,CY,46.4,79.5,153.9,6.3,8.8).cut(rounded(CX,CY,46.3,73.1,148.3,6.6,8))
rim=rim.cut(box(CX-16,CX+16,CY-80,CY-72,45.5,54))
tray=tray.fuse(rim)
add('Tabique_sobre_electronica','deck','secondary',(deck.fuse(tray) & box(-70,60,20,252,43,54)).clean(),True)
add('iPhone14','phone','steel',rounded(CX,CY,47.2,71.5,146.7,7.8,8.5))
add('Area_activa_iPhone','phone','screen',rounded(CX,CY,54.92,65,140.4,.08,7.7))
# Long seats keep both rail-running lanes continuous. Recessed rail screws follow the steel rail.
for side,t in ((-1,'I'),(1,'D')):
    x=CX+side*RAIL
    support=rounded(x,CY,55,17,250,35,2)
    # Lightening windows retain the ends and top flange without splitting the rail support.
    for y in (42,77,112,147,182,217):
        support=support.cut(yz([(y-10,60),(y+10,60),(y+10,77),(y+5,82),(y-5,82),(y-10,77)],x-10,x+10))
    for j in range(5,250,20):support=support.cut(cylinder(x,Y0+j,83,3.4,7.3))
    add('Asiento_Y_'+t,'rails','print',support,True)
    # Separate low feet connect the seat to the split base. The top hardware stays below the rail.
    for j,y in enumerate((65,133,237)):
        st=rounded(x+side*5.5,y,3,9,14,52.2,2)
        add(f'Pie_asiento_{t}_{j}','rails','secondary',st,True)
def steel(x,y,z,length,turn=False):
    sh=box(-4.5,4.5,0,length,0,6.5)
    for j in range(5,int(length),20):
        sh=sh.cut(cylinder(0,j,-.2,3.5,7),cylinder(0,j,3.3,6,3.5))
    if turn:sh=sh.rotate(Axis.Z,-90)
    return sh.translate((x,y,z))
def block(x,y,z,turn=False):
    # HIWIN MGN09H reference, 20 x 39.9, 10 mm assembled, underside Z=2.
    sh=rounded(0,0,2,20,PATIN,8,1.3).cut(box(-4.68,4.68,-21,21,1.8,6.7))
    for u in (-7.5,7.5):
        for vv in (-8,8):sh=sh.cut(cylinder(u,vv,6.9,2.5,3.3))
    if turn:sh=sh.rotate(Axis.Z,-90)
    return sh.translate((x,y,z))
for sf,t in ((-1,'I'),(1,'D')):
    x=CX+sf*RAIL
    add('MGN9_Y_'+t,'rails','steel',steel(x,Y0,REF,250))
    add('Patin_Y_'+t,'movingY','light',block(x,CY,REF))
    saddle=rounded(x,CY,100,22,29,5.4,2).fuse(rounded(x,CY+10,104,17,27,15.5,2)).clean()
    for u in (-7.5,7.5):
        for vv in (-8,8):saddle=saddle.cut(cylinder(x+u,CY+vv,99.9,3.4,4.3))
    lane=CX+sf*64.25
    saddle=saddle.cut(box(lane-2.6,lane+2.6,CY-16,CY+26,101.8,118.3))
    add('Silla_Y_'+t,'movingY','print',saddle,True)
beam=rounded(CX,CY+BEAM_OFFSET,119.5,168,13,11,2)
beam=beam.cut(box(CX-73,CX+73,CY+BEAM_OFFSET-2.6,CY+BEAM_OFFSET+2.6,120.6,123))
for xx in range(5,150,20):beam=beam.cut(cylinder(X0+xx,CY+BEAM_OFFSET,124.4,3.4,6.3))
add('Puente_transversal_nuevo','movingY','print',beam,True)
add('MGN9_X','movingY','steel',steel(X0,CY+BEAM_OFFSET,XRAILZ,150,True))
add('Patin_X','movingX','light',block(CX,CY+BEAM_OFFSET,XRAILZ,True))
# Centre the tool on the Y-block centres. Offset the X rail 14 mm toward the back.
plate=rounded(CX,CY+BEAM_OFFSET,140.5,34,20,5.4,2)
for u in (-8,8):
    for vv in (-7.5,7.5):plate=plate.cut(cylinder(CX+u,CY+BEAM_OFFSET+vv,140,3.5,5))
# One lateral spine passes in front of the transverse rail without crossing it.
spine=box(CX-5,CX+5,CY-13,CY-9,80,143.5)
tie=box(CX-6.5,CX+6.5,CY-13,CY+11,140.5,143.5)
shelf=box(CX-9,CX+9,CY-13,CY+6,80,83).cut(cylinder(CX,CY,79,8,5))
add('Carro_portapunta','movingX','print',plate.fuse(spine,tie,shelf).clean(),True)
add('Solenoide_412','movingX','steel',box(CX-7.55,CX+7.55,CY-8.5,CY+8.5,83,113))
add('Varilla_y_punta','movingX','warm',cylinder(CX,CY,GLASS+2,8.8,7).fuse(cylinder(CX,CY,GLASS+9,4,20)).clean())
# Fixed motors stay underneath the guide datum. Pulley centres sit inside the belt corridors.
for sign,t,bz,face in ((-1,'A',A_Z,87),(1,'B',B_Z,94)):
    x,y=CX+sign*26,275
    cradle=rounded(x,y,face-2.7,46,46,5.,3).cut(cylinder(x,y,face-3.3,23,6))
    cradle=cradle & box(x-24,x+24,y-21.2,y+21.5,face-4,face+2.3)
    for u in (-15.5,15.5):
        for z0 in (-15.5,15.5):cradle=cradle.cut(cylinder(x+u,y+z0,face-3.2,3.5,6))
    # Crosspiece connects to floor via two rear posts, outside the steel rail ends.
    for off in (-15,15):cradle=cradle.fuse(rounded(x-sign*24,y+off,3,5,6,face-5.65,1))
    add('Cuna_motor_'+t,'driveFix','secondary',cradle.clean(),True)
    add('NEMA17_'+t,'driveFix','black',rounded(x,y,face-2.7-38,42.3,42.3,38,2.6))
    add('Eje_motor_'+t,'driveFix','steel',cylinder(x,y,face-2.7,5,23.5))
    add('Polea_motriz_'+t,'driveFix','warm',cylinder(x,y,bz-3.5,13,7).cut(cylinder(x,y,bz-4,5.1,8)))
    xx=CX+sign*57.25
    for xx2,yy,station in [(xx,11.5,'frente'),(xx,279.5,'retorno')]:
        start=82.0 if station=='frente' else 3.0
        stand=cylinder(xx2,yy,start,9,A_Z-3.2-start)
        stand=stand.cut(cylinder(xx2,yy,A_Z-11,4.3,9.5))
        if station=='frente':
            # A cantilever from the guide bed leaves the entire front toggle recess free.
            seat_name='Asiento_Y_'+('I' if sign<0 else 'D')
            idx=next(j for j,u in enumerate(parts) if u[0]==seat_name)
            name,group,colour,seat,printed=parts[idx]
            xr=CX+sign*RAIL
            ledge=rounded((xx2+xr)/2,yy-1.5,80,abs(xr-xx2)+8,11,4,2)
            # Transfer front idler load into the outer base, outside the screen and switch.
            xi=sign*xr+6;xo=94.6
            outline=[(xi-1,80),(xi+1,85),(xo,63),(xo,3),(xo-4.2,3),(xo-4.2,57)]
            brace=xz([(sign*x,z) for x,z in outline],20,29)
            seat=seat.fuse(ledge,stand,brace).clean()
            assert len(seat.solids())==1 and seat.is_valid,seat_name
            seat.label=name;seat.color=Color(PALETTE[colour]);parts[idx]=(name,group,colour,seat,printed)
        else:
            add('Poste_'+station+'_'+t,'driveFix','secondary',stand,True)
        add('Eje_'+station+'_'+t,'driveFix','steel',cylinder(xx2,yy,A_Z-10,5,B_Z-A_Z+14))
        for k,z0 in enumerate((A_Z,B_Z)):
            add(f'Polea_{station}_{t}_{k}','driveFix','steel',cylinder(xx2,yy,z0-3.2,14,6.4).cut(cylinder(xx2,yy,z0-4,5.1,8)))
    # Each pair of travelling idlers follows Y, not X. The axles attach to the moving bridge.
    ear=box(min(xx-5,xx+5),max(xx-5,xx+5),CY+12,CY+24,117,119.5)
    add('Oreja_idler_'+t,'movingY','print',ear,True)
    add('Eje_idler_'+t,'movingY','steel',cylinder(xx,CY+18,100.8,5,18.4))
    for k,z0 in enumerate((A_Z,B_Z)):
        add(f'Polea_puente_{t}_{k}','movingY','steel',cylinder(xx,CY+18,z0-3.2,14,6.4).cut(cylinder(xx,CY+18,z0-4,5.1,8)))
# Belt guide lanes: two distinct levels, represented as straight reference lengths.
# Terminal return arcs, clamp, teeth and tensioner require a detailed transmission release.
for z0,sign,t in [(A_Z,-1,'A'),(B_Z,1,'B')]:
    xx=CX+sign*65.
    add('Ramal_lateral_'+t,'belt','belt',box(xx-.75,xx+.75,11.5,279.5,z0-3,z0+3))
    add('Ramal_retorno_'+t,'belt','belt',box(CX-57.25,CX+57.25,285.75,287.25,z0-3,z0+3))
# Side webs support the optical bridge from outside both Y lanes. The thicker parts begin
# above the carriage. The fixed bridge is behind the long axis of the folded C922.
pillars=[]
for sign,tag in [(-1,'I'),(1,'D')]:
    a,b=sorted((sign*95,sign*98))
    pillar=yz([(177,58.10),(216,58.10),(213,148),(211,199),(185,199),(183,149)],a,b)
    xo,xi=sorted((sign*95.5,sign*85))
    pillar=pillar.fuse(yz([(184.6,148),(212.5,150),(211,199),(185,199)],xo,xi))
    for yc in (186,206):
        xlo,xhi=sorted((sign*91.5,sign*94.8)); xt0,xt1=sorted((sign*92.8,sign*95.6))
        ear=box(xlo,xhi,yc-5,yc+5,45,61).fuse(box(xt0,xt1,yc-5,yc+5,58,63))
        ear=ear.cut(cylinder(sign*99,yc,50,3.4,9,(-sign,0,0)))
        pillar=pillar.fuse(ear)
    pillars.append(pillar.clean())
bridge=rounded(0,198,184,191,18,15,3).cut(box(-84,84,195,201,187,195))
# Side-walls form the end cheeks. Stop the transverse beam flush at their inner faces.
bridge=bridge & box(-86,86,181,213,179,202)
# Vertical slide: common pair of slots, lifts camera/pod together -5 to +10 mm.
holder=box(20.6,24.6,132,200,183,192).fuse(box(20.6,24.6,130,157,172,202))
for yy in (136.,151.):
    holder=holder.cut(box(18,25,yy-1.75,yy+1.75,178,193),
        cylinder(18,yy,178,3.5,8,(1,0,0)),cylinder(18,yy,193,3.5,8,(1,0,0)))
# Mechanical shoulder bolts attach the slide to the front face of the beam.
holder=holder.cut(box(18,25,189,202,183.95,192.2))
holder=holder.fuse(box(11,34,186,201,181.5,184))
arch_part=add('Portico_camara_una_pieza','arch','print',
    joined([bridge,*pillars,holder,box(12,33,190,194,182.6,185.2)]),True)
# C922 mesh is schematic, bounded by the manufacturer's assembled dimensions with folded clip.
add('C922_cara','camera','graphite',rounded(CX,CY,LENS+.4,38,94,20,7))
add('C922_lente','camera','blue',cylinder(CX,CY,LENS,13,1))
add('C922_pie_plegado','camera','black',box(CX+10,CX+17,CY-19,CY+20,LENS+19.7,LENS+56))
pod=rounded(CX,CY,LENS+73,50,102,3,5)
for side in (-1,1):
    x=CX+side*24
    arm=box(x-1,x+1,CY-44,CY+44,LENS+.1,LENS+74)
    for dy in (-22,0,22):
        arm=arm.cut(yz([(CY+dy-6,LENS+25),(CY+dy+2,LENS+25),(CY+dy+8,LENS+49),(CY+dy,LENS+49)],x-2,x+2))
    pod=pod.fuse(arm)
# Foot interface carries the camera independently of the cosmetic printed cap.
shoe=box(CX+17,CX+23.5,CY-18,CY+20,LENS+22,LENS+53)
shoe=shoe.cut(cylinder(CX+16,CY,LENS+35,6.65,10,(1,0,0)))
pod=pod.fuse(shoe,box(16.5,20,130,157,LENS+20,LENS+42))
for yy in (136.,151.):
    pod=pod.cut(cylinder(16.8,yy,183,3.5,5,(1,0,0)))
for x in (-15,-8,-1,6):
    pod=pod.cut(rounded(x,CY+13,LENS+72,3.3,37,5,1.5))
add('Capota_y_soporte_C922','pod','shell',pod.clean(),True)
cable('USB_camara_fijo',[(24,189,180),(46,192,180),(80,172,178),(90.5,173,161),(90.5,173,70),(90.5,172,63),(88.7,164,43)],1.45,'black','harness')
# Front and rear circuit boards share the space underneath the phone.
def carrier(label,cx,cy,w,d,holes):
    plate=rounded(cx,cy,3,w+4,d+4,2.5,3)
    for x,y in holes:plate=plate.fuse(cylinder(x,y,5.4,6.2,3.6)).cut(cylinder(x,y,4,2.6,6))
    add(label,'electronics','secondary',plate.clean(),True)
x,y=39,118
ph=[(x+u,y+v) for u in (-24.5,24.5) for v in (-39,19)]
carrier('Bandeja_Pi',x,y,56,85,ph)
add('Raspberry_Pi_5','electronics','board',rounded(x,y,9,56,85,1.6,2.4))
for j,xc in enumerate((x-18,x,x+18)):
    add('Puerto_Pi_'+str(j),'electronics','steel',box(xc-6,xc+6,y+28,y+44,10.6,26))
add('Disipador_CanaKit','electronics','steel',rounded(x,y-4,10.6,48,60,18,2.5))
add('Ventilador_CanaKit','electronics','black',rounded(x,y-4,28.6,40,40,10,3).cut(cylinder(x,y-4,28.4,32,11)))
add('Buje_ventilador','electronics','graphite',cylinder(x,y-4,33,13,5))
for a in range(0,360,60):
    add('Aspa_'+str(a),'electronics','graphite',rounded(9,0,34,15,5,2,2).rotate(Axis.Z,a).translate((x,y-4,0)))
x,y=-32,190
mh=[(x+u,y+v) for u in (-41,41) for v in (-31,31)]
carrier('Bandeja_MKS',x,y,90,70,mh)
add('MKS_DLC32_V22','electronics','black',rounded(x,y,9,90,70,1.6,2.5))
for k,xi in enumerate((x-26,x)):
    add('TMC2209_'+str(k),'electronics','blue',box(xi-8,xi+8,y-26,y-5,10.6,20))
    for j in (-5,-2,1,4):add(f'Disipador_driver_{k}_{j}','electronics','steel',box(xi+j,xi+j+1.35,y-25,y-6,20,29))
for nm,xx in [('USB_B',x+8),('Entrada_DC',x+23)]:
    add(nm+'_MKS','electronics','steel',box(xx-5.8,xx+5.8,y-36,y-24,10.6,22))
ADA_X,ADA_Y=50.,224.
ada=rounded(ADA_X,ADA_Y,3,36.4,24.4,13.2,2)
for tip,di in [(ADA_X-19.8,1),(ADA_X+19.8,-1)]:
    ada=ada.fuse(cylinder(tip,ADA_Y,9.6,9,2.,(di,0,0))).cut(cylinder(tip-di*.05,ADA_Y,9.6,6,2.5,(di,0,0)))
add('Caja_Adafruit_5648','electronics','print',ada.clean())
add('Portafusible','electronics','edge',rounded(-25,45,3,34,22,26,2.5))
add('Entrada_CC_trasera','electronics','edge',cylinder(48,D-16,26,11,15.6,(0,1,0)))
power=box(-76,-8,69,119,5,32)
add('Reserva_convertidor_CC','power','reserved',power)
# The rear Kycon inlet is schematic. The reserved volume represents the selected Geekworm and DFRobot modules; connector fit and thermal load await a physical test.
cable('Trayecto_USB_a_Pi',[(39,162,19),(39,183,19),(17,188,35),(15,142,34),
                           (10,129,32),(-14,129,27),(-24,136,22),(-24,154,19)],1.8,'black','harness')
# Cable duct lies to the right of BOTH the shaft and the Y block, full travel.
duct=box(85,94.6,45,236,61,74).cut(box(87,93,44,237,64,75))
duct=duct.cut(box(87,93,164,175,60,65))
add('Canal_cables_exterior_Y','rails','secondary',duct,True)
# End shrouds and side trim stay below all carriage bodies. Removable front door below the work plane.
for sign,tag in ((-1,'I'),(1,'D')):
    xa,xb=sorted((sign*95,sign*98))
    for index,(ya,yb) in enumerate(((9,177),(216,293))):
        add('Borde_lateral_'+tag+str(index),'arch','graphite',box(xa,xb,ya,yb,58,85),True)

from tornilleria import estandarizar
hardware_design=estandarizar(globals())

def volume(shape):
    return sum(b.volume for b in shape.solids()) if shape is not None else 0.
def overlap(a,b):
    return volume(a & b)
def ranges(sh):
    b=sh.bounding_box()
    return (b.min.X,b.max.X,b.min.Y,b.max.Y,b.min.Z,b.max.Z)
def boxes_intersect(a,b,eps=.00001):
    return all(min(a[k+1],b[k+1])-max(a[k],b[k])>eps for k in (0,2,4))
def sweep_slabs(sh,dx,dy):
    # Project Z-separated chunks to rectangles. Translating these rectangles over both axes
    # covers EVERY pose, including diagonals, and overestimates rounded corners and holes.
    cuts=(0,55,57,64,75,80,83,90,92,96.5,100,101.8,104,108,112,117,118.3,119.5,122,130.5,136.99,140.5,143.5,145.9,147.55,150)
    bounds=ranges(sh)
    for a,b in zip(cuts,cuts[1:]):
        lo=max(a,bounds[4]);hi=min(b,bounds[5])
        if hi-lo<.0001:continue
        chunk=sh & box(bounds[0]-1,bounds[1]+1,bounds[2]-1,bounds[3]+1,lo,hi)
        if chunk is None:continue
        for solid in chunk.solids():
            x0,x1,y0,y1,z0,z1=ranges(solid)
            if min(x1-x0,y1-y0,z1-z0)<.0001:continue
            yield (x0-dx,x1+dx,y0-dy,y1+dy,z0,z1)
def run_sweeps(movable,targets,dx,dy,allowed):
    tests,hits=0,[]
    boxes={k:ranges(sh) for k,sh in targets}
    for name,sh in movable:
        for bounds in sweep_slabs(sh,dx,dy):
            swept=None
            for target,solid in targets:
                if (name,target) in allowed:continue
                tests+=1
                if not boxes_intersect(bounds,boxes[target]):continue
                if swept is None:swept=box(*bounds)
                vol=overlap(swept,solid)
                if vol>.015:hits.append([name,target,round(vol,3),[round(i,1) for i in bounds]])
    return {'intervalos_comparados':tests,'choques':hits}
def mates(group,other):
    return [(k,sh) for k,g,c,sh,p in parts if g in group and k not in other]
fixed=mates({'base','front','deck','toggle','switchmount','camera','pod','arch','driveFix','rails',
             'electronics','power','mechanism','phone','harness','belt'},set())
my=mates({'movingY'},set());mx=mates({'movingX'},set())
dx=(L_X-PATIN)/2;dy=(L_Y-PATIN)/2
mating={(f'Patin_Y_{s}',f'MGN9_Y_{s}') for s in ('I','D')}
qa={'patines_Y_puente_contra_fijos':run_sweeps(my,fixed,0,dy,mating),
    'patin_X_y_cabezal_contra_fijos':run_sweeps(mx,fixed,dx,dy,set()),
    'patin_X_y_cabezal_contra_puente':run_sweeps(mx,my,dx,0,{('Patin_X','MGN9_X')})}
# Screw bodies travel with the stage they belong to. A rail screw fits entirely
# inside its own unchanged channel; only its corresponding block/rail joint is excluded.
hardware_f=mates({'herrajesFijos','herrajesOptica'},set())
hardware_y=mates({'herrajesY'},set());hardware_x=mates({'herrajesX'},set())
allowed_y={(block,t) for block in ('Patin_Y_I','Patin_Y_D') for t,_ in hardware_f
    if t.startswith('T_7219_Guias_Y_') and
    ((int(t.rsplit('_',1)[-1])<=13)==(block=='Patin_Y_I'))}
allowed_x={('Patin_X',t) for t,_ in hardware_y if t.startswith('T_7219_Guia_X_')}
qa['patines_y_herrajes_fijos']=run_sweeps(my+mx,hardware_f,0,dy,allowed_y)
qa['cabezal_frente_a_herrajes_fijos_XY']=run_sweeps(mx,hardware_f,dx,dy,set())
qa['cabezal_frente_a_herrajes_del_puente']=run_sweeps(mx,hardware_y,dx,0,allowed_x)
qa['tornillos_del_puente_frente_a_la_maquina']=run_sweeps(hardware_y,fixed+hardware_f,0,dy,set())
qa['tornillos_del_cabezal_frente_a_la_maquina']=run_sweeps(hardware_x,fixed+hardware_f,dx,dy,set())
qa['tornillos_del_cabezal_frente_al_puente']=run_sweeps(hardware_x,my+hardware_y,dx,0,set())
assert 6.5-3.3-1.65>1.5 and (6-5.70)/2>.14
# For each excluded track/block joint, test against a solid rectangular rail longer than
# the carriage's full travel including both stroke ends. No mounting holes may mask a clash.
rail_checks={}
for name,rail in [('Patin_Y_I',box(CX-RAIL-4.5,CX-RAIL+4.5,0,D,REF,REF+6.5)),
                  ('Patin_Y_D',box(CX+RAIL-4.5,CX+RAIL+4.5,0,D,REF,REF+6.5)),
                  ('Patin_X',box(-98,98,CY+BEAM_OFFSET-4.5,CY+BEAM_OFFSET+4.5,XRAILZ,XRAILZ+6.5))]:
    rail_checks[name]=round(overlap(lookup(name),rail),5)
    assert rail_checks[name]==0
# Also check the lowest camera setting against the complete moving head/guide envelope.
opt_min=[(n,s.translate((0,0,-5))) for n,g,c,s,p in parts if g in ('camera','pod')]
qa['optica_95_frente_a_todo_el_movimiento']=run_sweeps(mx,opt_min,dx,dy,set())
qa['cabezas_de_tornillo_a_optica_minima']=run_sweeps(hardware_x,opt_min,dx,dy,set())
qa['optica_95_frente_al_puente']=run_sweeps(my,opt_min,0,dy,set())
(HERE/'.revision').mkdir(exist_ok=True)
(HERE/'.revision'/'barrido.json').write_text(json.dumps(qa,indent=2))
for label,ch in qa.items():
    if ch['choques']: print(label, *ch['choques'][:10],sep='\n',flush=True)
assert not any(ch['choques'] for ch in qa.values()),'Revisar interferencias del barrido'
# Allow full switch travel; neutral is the farthest forward position. A 16 mm finger probe
# reaches both positions without hitting the front edge. Both insulated wires exit behind the terminals.
toggle_depth={}
for angle in range(-16,17,2):
    toggle_sh=toggle(angle)
    assert overlap(toggle_sh,mount)<.01
    z=SZ+(17.5-3.05)*sin(radians(angle))
    fingertip=cylinder(SX,-2,z,16,20,(0,1,0))
    for n,obstacle in [('cazoleta',mount)]+mates({'rails','driveFix','electronics','base','arch','deck'},set()):
        if boxes_intersect(ranges(fingertip),ranges(obstacle)):
            assert overlap(fingertip,obstacle)<.01,('acceso al interruptor',n)
    for n,obstacle in mates({'driveFix','rails','electronics','deck'},set()):
        if boxes_intersect(ranges(toggle_sh),ranges(obstacle)):
            assert overlap(toggle_sh,obstacle)<.01,('accionamiento',n)
    toggle_depth[str(angle)]=round(ranges(toggle_sh)[2],2)
assert min(toggle_depth.values())>=0
plug_zones={'USB_B_MKS':box(-30,-18,119,154,11,22),'USB_A_Pi_MKS':box(32,46,162,202,12,26),
    'USB_A_Pi_camara':box(50,64,162,202,12,26),'USB_C_Pi':box(67,92,80,91,11,19),
    'bornas_S301T':back_wiring}
# Exhaustive checks against the other devices, shrouds and feet. Matching port faces may touch.
for label,sh in plug_zones.items():
    errs=[]
    for n,s in mates({'front','switchmount','toggle','base','deck','electronics','power','rails'},set()):
        if boxes_intersect(ranges(sh),ranges(s)) and overlap(sh,s)>.03:errs.append(n)
    if errs: print('Conector',label,errs,flush=True)
    assert not errs,(label,errs)
# Independent checks on the face/foot carriage throughout its 15 mm manual adjustment.
for delta in range(-5,11):
    cap=lookup('Capota_y_soporte_C922').translate((0,0,delta))
    assert overlap(cap,holder)<.01 and overlap(cap,bridge)<.01
for a in ('NEMA17_A','NEMA17_B'):
    assert overlap(lookup(a),lookup('Carcasa_detras'))<.01
cable_s=lookup('USB_camara_fijo')
for target in ('Canal_cables_exterior_Y','Tabique_sobre_electronica','Portico_camara_una_pieza'):
    assert overlap(cable_s,lookup(target))<.03,target
for key,hardware in mates({'toggle','switchmount'},set()):
    for name,obstacle in mates({'rails','driveFix','electronics','deck'},set()):
        if boxes_intersect(ranges(hardware),ranges(obstacle)):
            assert overlap(hardware,obstacle)<.02,(key,name)
# Check the two removable seams and the actual neighbouring solids at rest.
# Designed thread contact is not a collision; unrelated fasteners always remain separate.
assembly_clearances={}
def check_pair(first,second):
    a=lookup(first);b=lookup(second)
    value=round(overlap(a,b),5) if boxes_intersect(ranges(a),ranges(b)) else 0.
    assembly_clearances[first+' / '+second]=value
    if value>=.01: print('Interferencia estática',first,second,value,flush=True)

for left,right in [
    ('Carcasa_delante','Carcasa_detras'),
    ('Carcasa_delante','Tabique_sobre_electronica'),('Carcasa_detras','Tabique_sobre_electronica'),
    ('Carcasa_delante','Raspberry_Pi_5'),('Carcasa_delante','Disipador_CanaKit'),
    ('Carcasa_detras','Caja_Adafruit_5648'),('Carcasa_detras','MKS_DLC32_V22'),
    ('Carcasa_detras','Portico_camara_una_pieza'),
    ('Carcasa_delante','Asiento_Y_I'),('Carcasa_delante','Asiento_Y_D'),
    ('Carcasa_detras','Asiento_Y_I'),('Carcasa_detras','Asiento_Y_D')]:
    check_pair(left,right)
for name,_ in mates({'herrajesFijos'},set()):
    if 'LCD_' in name:
        for panel in ('Carcasa_delante','Vidrio_TS24_62x45','PCB_pantalla_TS24'):
            check_pair(name,panel)
    if 'MKS_' in name or 'Placa_MKS' in name:
        for panel in ('Carcasa_detras','MKS_DLC32_V22'):
            check_pair(name,panel)
for sign in (-1,1):
    keepout=cylinder(ADA_X+sign*18.2,ADA_Y,9.6,6,14,(sign,0,0))
    assert overlap(keepout,lookup('Carcasa_detras'))<.01
for delta in range(-5,11):
    for n,s in mates({'herrajesOptica'},set()):
        assert overlap(s.translate((0,0,delta)),arch_part)<.01,(n,delta)
assert max(assembly_clearances.values())<.01,'Revisar interferencias de ensamble'
# In the X rail, 3.2 mm of recess leaves 1.55 mm above the highest permitted button head.
# Across the complete Y stroke, both side belts also miss the inboard screws of the Y saddles.
gap_belt_head=(RAIL-7.5-5.7/2)-(65+.75)
gap_belt_solenoid=(65-.75)-((L_X-PATIN)/2+7.55)
assert gap_belt_head>1.39 and gap_belt_solenoid>1.64
# Body height at the nominal and both end settings of the optical slider.
bounds_by_height={}
for offset in (-5.,0.,10.):
    bb=Compound(children=[s.translate((0,0,offset)) if g in ('pod','camera') else s for n,g,c,s,p in parts]).bounding_box()
    dims=[round(i,2) for i in (bb.size.X,bb.size.Y,bb.size.Z)]
    assert all(abs(a-b)<.04 for a,b in zip(dims,(W,D,H+offset))),(offset,dims)
    bounds_by_height[str(int(OPTICAL+offset))]=dims
# Solid reimport and flat-print footprint for each printed part, including a 5 mm brim all round.
def bed_fit(sh):
    b=sh.bounding_box()
    for deg in range(91):
        a=radians(deg);x=b.size.X*cos(a)+b.size.Y*sin(a);y=b.size.X*sin(a)+b.size.Y*cos(a)
        if max(x,y)<=246.01 and b.size.Z<=250.01:return [deg,round(x,1),round(y,1),round(b.size.Z,1)]
    raise ValueError(('Bambu X2D',sh.label,b.size))
fits={n:bed_fit(s) for n,g,c,s,p in parts if p}
model=Compound(label='FT412 V2 compacta - CAD de distribucion',
    children=[Compound(label=group,children=[s for n,g,c,s,p in parts if g==group])
              for group in dict.fromkeys(g for n,g,c,s,p in parts)])
assert export_step(model,HERE/'FT412-V2.step')
back=import_step(HERE/'FT412-V2.step')
assert len(back.solids())==len(model.solids()) and all(b.is_valid for b in back.solids())
report={'herrajes':hardware_design['resumen'],'unidades':'mm','fase':'Diseño de distribución; validación física pendiente','dimensiones_a_distancia_lente_vidrio':bounds_by_height,
    'ensamble':{'intersecciones_mm3':assembly_clearances,'holgura_banda_a_tornillo_patin_Y_mm':round(gap_belt_head,2),'holgura_banda_a_solenoide_mm':round(gap_belt_solenoid,2),'cabezas_de_riel_bajo_la_guia_mm':1.55},
    'cotas_usuario':{'vidrio_a_lente':100,'borde_superior_previo_a_lente':65,'vidrio_bajo_el_borde_por_diferencia':35},
    'exterior_litros_nominal':round(W*D*H/1e6,3),'exterior_anterior_mm':[324,398,354],
    'reduccion_exterior_por_ciento':round(100*(1-W*D*H/(324*398*354)),2),
    'movimiento':{'guia_X':150,'guias_Y':[250,250],'patin_MGN9H':[39.9,20,10],
      'campo_con_bloque_entero_sobre_el_riel':[round(2*dx,2),round(2*dy,2)],
      'campo_con_margen_de_2_por_extremo':[round(2*dx-4,2),round(2*dy-4,2)],
      'recorrido_de_referencia_V1':[85,180],'margen_por_lado_sobre_cuerpo_iPhone14_CON_reserva_de_2_mm':[17.3,29.7],'envolvente_sin_choques':qa,'union_patin_riel_interseccion_mm3':rail_checks,
      'hueco_lateral_del_canal_en_bloque_esquematico':.18,'hueco_superior_del_canal':.2,
      'hueco_entre_punta_retraida_y_vidrio':2,'ejes_Y_separados_mm':2*RAIL,'separacion_silla_Y_a_pared_izquierda':1.5,
      'holgura_vertical_cabezal_a_cara_inferior_de_pod_a_95mm':round(LENS-5+.1-hardware_design['techo_cabezal'],2)},
    'interruptor':{'referencia':'NKK S301T','funcion':'I / O general de corriente continua',
      'dos_bornes_de_tornillo':True,'palanca_diametro':6.1,'longitud':17.5,'recorrido_total_grados':32,
      'taladro':12.5,'antigiro':[3,9],'panel':3,'frente_libre_según_posicion':toggle_depth},
    'conexion_exterior':'MEAN WELL GST160A12-R7B externa de 12 V, 11,5 A y 138 W. Entrada Kycon KPJX-PM-4S, MKS a 12 V, Geekworm Pi5-5V5APD para la Pi y DFRobot DFR0758 para el iPhone. El CAD reserva espacio; quedan por validar el montaje de las placas y las fichas, la protección de entrada y la temperatura bajo carga.',
    'electricos':{'reserva_convertidor':[68,50,27],'pi5_nominal':[85,56],'mks_nominal':[90,70],
       'enchufes_nominales':{k:[round(x,1) for x in ranges(s)] for k,s in plug_zones.items()}},
    'piezas_impresas_caben_X2D_con_brim_de_5':fits,'solidos_STEP_reimportados':len(back.solids()),
    'alcance':['El barrido continuo incluye los tres bloques completos, sus sillas, riel transversal, puente, cabezal y poleas móviles. El contacto nominal con cada guía se revisó por separado.',
       'Se modelan dos ramales de correa y sus planos. Los retornos finales, la mordaza, el tensor y la curva dinámica de los cables quedan por detallar y verificar físicamente.',
       'Pendientes la rigidez bajo tensión, el cierre de las interfaces especiales y la longitud real de los conectores, encuadre real de la cámara, encaje de la toma y de los módulos de alimentación y disipación bajo carga. El modelo no está liberado para imprimir toda la máquina.']}
(HERE/'verificacion.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
meshes=[]
def pack(fmt,values):
    return base64.b64encode(struct.pack('<'+str(len(values))+fmt,*values)).decode()
for name,group,col,sh,_ in [*parts,('Detalle_cazoleta_integrada','detalleSwitch','graphite',mount,False)]:
    vv,ff=sh.tessellate(.15,.22)
    meshes.append(dict(n=name,g=group,c=PALETTE[col],v=pack('f',[round(a,3) for pt in vv for a in pt]),
                  i=pack('I',[i for tri in ff for i in tri])))
(HERE/'.geometria.gz').write_bytes(gzip.compress(json.dumps(meshes,separators=(',',':')).encode()))
print('Piezas',len(parts),'Sólidos',len(back.solids()),'Exterior',bounds_by_height,'Carrera libre',2*dx,2*dy,flush=True)
