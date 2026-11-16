"""Instruction plates: verified STL geometry plus explicitly schematic hardware.

Run in the assembly-guide Python environment, then rasterize SVGs for the PDF.
This renderer never regenerates CAD or reads printer/commerce state.
"""
from pathlib import Path
import base64, hashlib, html, io, json, re
import numpy as np
import trimesh
import matplotlib
matplotlib.use('Agg')
from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.collections import PolyCollection
from matplotlib.colors import to_rgb

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'public/assets/assembly'
OUT.mkdir(parents=True,exist_ok=True)
INK='#173d39'; TEAL='#078578'; PALE='#e4f1ec'; GRAY='#b5c4c7'; DARK='#526b73'; ORANGE='#ce602e'; PAPER='#faf8f2'; BLUE='#3d78a0'
parts={p['part']:p for p in json.loads((ROOT/'hardware/ft412/qa/print-manifest.json').read_text())['parts']}
for p in parts.values():
    assert hashlib.sha256((ROOT/'hardware/ft412'/p['stl']).read_bytes()).hexdigest()==p['stl_sha256']

def mesh(name,rot=None,center=None):
    m=trimesh.load_mesh(ROOT/'hardware/ft412'/parts[name]['stl'])
    if rot is not None:m.vertices=m.vertices@np.array(rot).T
    m.vertices-=m.bounds.mean(axis=0)
    if center is not None:m.vertices+=center
    return m
def box(d,c):
    m=trimesh.creation.box(d);m.vertices+=c;return m
def cyl(r,h,c):
    m=trimesh.creation.cylinder(r,h,sections=40);m.vertices+=c;return m
def shifted(m,c):
    q=m.copy();q.vertices+=c;return q

class Plate:
    def __init__(self,num,title,subtitle):
        self.name=num
        title=re.sub(r"^\d+ / ", "", title)
        self.s=[f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="1200" height="1000" viewBox="0 0 1200 1000" role="img"><title>{html.escape(title)}</title><desc>{html.escape(subtitle)}</desc><defs><marker id="arrow" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6" fill="{ORANGE}"/></marker></defs><rect width="1200" height="1000" fill="{PAPER}"/>']
        self.text(50,50,'FT412  /  MONTAJE VISUAL',19,TEAL,bold=True)
        self.text(50,100,title,37,bold=True)
        self.text(50,140,subtitle,23)
        self.line(50,164,1150,164,'#cedbd5',1)
    def text(self,x,y,t,size=25,col=INK,bold=False,anchor='start'):
        for i,line in enumerate(t.split('\n')):
            self.s.append(f'<text x="{x}" y="{y+i*size*1.35}" font-family="DejaVu Sans,Arial,sans-serif" font-size="{size}" font-weight="{700 if bold else 400}" fill="{col}" text-anchor="{anchor}">{html.escape(line)}</text>')
    def line(self,x,y,x2,y2,col=INK,w=2,dash=None,arrow=False):
        self.s.append(f'<line x1="{x}" y1="{y}" x2="{x2}" y2="{y2}" stroke="{col}" stroke-width="{w}"'+(f' stroke-dasharray="{dash}"' if dash else '')+(' marker-end="url(#arrow)"' if arrow else '')+'/>')
    def arrow(self,a,b):self.line(*a,*b,ORANGE,4,arrow=True)
    def rect(self,x,y,w,h,fill=PALE,stroke=INK,r=0):self.s.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{fill}" stroke="{stroke}" stroke-width="2"/>')
    def circle(self,x,y,r,fill=PAPER,stroke=TEAL):self.s.append(f'<circle cx="{x}" cy="{y}" r="{r}" fill="{fill}" stroke="{stroke}" stroke-width="3"/>')
    def poly(self,pts,fill=PALE,stroke=INK):self.s.append('<polygon points="'+' '.join(f'{x},{y}' for x,y in pts)+f'" fill="{fill}" stroke="{stroke}" stroke-width="2"/>')
    def label(self,n,x,y,t):
        self.circle(x,y-8,18,TEAL,TEAL);self.text(x,y-1,str(n),20,PAPER,True,'middle');self.text(x+30,y,t,24,bold=True)
    def note(self,t):
        self.rect(50,884,1100,65,PALE,'none',10);self.text(75,923,t,24,bold=True)
        self.text(50,978,'Piezas impresas: geometría STL real. Herrajes y flechas: esquema de montaje, sin escala.',16,DARK)
    def save(self):
        (OUT/(self.name+'.svg')).write_text(''.join(self.s)+'</svg>')
    def image(self,data,x,y,w,h):self.s.append(f'<image x="{x}" y="{y}" width="{w}" height="{h}" xlink:href="data:image/png;base64,{data}"/>')

def render(p,objects,rect,view='iso',margin=.07):
    # Orthographic triangle rasterization; all part meshes retain scale relative
    # to each other within one scene. Commercial shapes are labeled schematics.
    right=np.array([.866,.5,0.]);up=np.array([-.30,.52,.8])
    if view=='front':right=np.array([1.,0,0]);up=np.array([0.,0,1.])
    if view=='top':right=np.array([1.,0,0]);up=np.array([0.,1.,0])
    if view=='inside':right=np.array([-.866,.5,0]);up=np.array([-.30,-.52,.8])
    depth=np.cross(right,up);depth/=np.linalg.norm(depth)
    tris=[];cols=[];norms=[]
    for m,c in objects:
        tris.extend(m.triangles);cols.extend([to_rgb(c)]*len(m.faces));norms.extend(m.face_normals)
    t=np.array(tris);n=np.array(norms);col=np.array(cols)
    xy=np.stack((t@right,t@up),axis=-1)
    lo=xy.reshape(-1,2).min(0);hi=xy.reshape(-1,2).max(0)
    x,y,w,h=rect;cx,cy=(lo+hi)/2;span=hi-lo
    scale=min(w/(span[0]*(1+margin*2)),h/(span[1]*(1+margin*2)))
    half=np.array([w,h])/scale/2;limlo=np.array([cx,cy])-half;limhi=np.array([cx,cy])+half
    order=np.argsort(t.mean(1)@depth)
    light=np.array([-.3,-.5,1.]);light/=np.linalg.norm(light)
    shade=.58+.42*np.maximum(0,n@light)
    col=np.clip(col*shade[:,None],0,1)
    fig=Figure(figsize=(w/100,h/100),dpi=160);FigureCanvasAgg(fig)
    ax=fig.add_axes([0,0,1,1]);ax.set_xlim(limlo[0],limhi[0]);ax.set_ylim(limlo[1],limhi[1]);ax.axis('off')
    ax.add_collection(PolyCollection(xy[order],facecolors=col[order],edgecolors='none',antialiased=False))
    buf=io.BytesIO();fig.savefig(buf,format='png',transparent=True,dpi=160)
    p.image(base64.b64encode(buf.getvalue()).decode(),x,y,w,h)
    def point(v):
        v=np.array(v);return (x+w/2+(v@right-cx)*scale,y+h/2-(v@up-cy)*scale)
    return point

def frame(explode=0):
    a=[]
    for sx in (-1,1):a.append((box([20,355,40],[sx*(105+explode),177.5,20]),GRAY))
    for sy in (0,1):a.append((box([190,20,40],[0,10+335*sy+(2*sy-1)*explode,20]),GRAY))
    return a
def profile_top(p,x,y,w,h):
    p.rect(x,y,w,h,'#dce3e2');p.line(x+6,y+h*.45,x+w-6,y+h*.45,DARK,3);p.line(x+6,y+h*.6,x+w-6,y+h*.6,DARK,2)
def bolt(p,x,y,length=92,fh=False,col=DARK):
    p.rect(x-7,y,14,length,col,col)
    if fh:p.poly([(x-22,y-14),(x+22,y-14),(x+7,y+4),(x-7,y+4)],col,col)
    else:p.rect(x-21,y-16,42,20,col,col,6)
    for yy in range(int(y+10),int(y+length),9):p.line(x-6,yy,x+6,yy-4,PAPER,1)
    p.line(x-8,y-8,x+8,y-8,PAPER,2)

# 01: the first operations, real proportions, explanatory hardware diagram.
p=Plate('paso-01-marco','01 / Cerrá el rectángulo','Dos costados largos y dos extremos cortos. Dejá las uniones ajustables.')
p.label('A',75,215,'Separá y acercá');p.label('B',680,215,'Escuadrá antes de apretar')
q=render(p,frame(35),(35,240,550,455));r=render(p,frame(),(620,250,540,440))
for sy in (0,1):p.arrow(q([0,10+335*sy+(2*sy-1)*35,45]),q([0,10+335*sy,45]))
p.text(75,730,'2 × 355 mm',27,TEAL,True);p.text(75,770,'2 × 190 mm, entre los largos',24)
p.line(*r([-115,0,43]),*r([115,355,43]),ORANGE,3,'9 7')
p.line(*r([115,0,43]),*r([-115,355,43]),TEAL,3,'9 7')
p.text(680,730,'Diagonal A = diagonal B',25,TEAL,True);p.text(680,770,'Exterior: 230 × 355 mm',25)
p.text(75,829,'20 mm de ancho; 40 mm en vertical. Las cuatro esquinas apoyan planas.',24)
p.note('Comprobá otra vez las diagonales después del apriete.');p.save()

p=Plate('paso-02-esquinas','02 / Sujetá las cuatro esquinas','Una escuadra interior por esquina, en la mitad inferior del perfil.')
p.label('A',75,215,'Ubicación');p.label('B',680,215,'Unión a la ranura')
# Orthogonal corner with correctly lower gusset, enlarged schematic.
q=render(p,[(box([20,110,40],[-10,55,20]),GRAY),(box([90,20,40],[45,10,20]),GRAY),(box([18,3,18],[9,21.5,10]),TEAL),(box([3,18,18],[1.5,30,10]),TEAL)],(35,265,530,390),'inside')
p.text(70,700,'Cara superior libre',25,bold=True);p.arrow((300,680),q([-10,50,40]))
p.text(70,757,'4 escuadras GS20-05W',24);p.text(70,795,'8 M4×8 + 8 SQN05M4',24,TEAL,True)
# Section through one leg, horizontal fastener axis drawn as vertical for clarity.
profile_top(p,700,540,390,155);p.rect(860,540,70,70,PAPER,PAPER)
p.rect(820,610,150,35,ORANGE,INK);p.text(700,738,'Tuerca detrás de los labios',23)
p.rect(780,495,230,25,TEAL);bolt(p,895,375,174)
p.arrow((1030,390),(1030,487));p.text(700,310,'M4×8',26,bold=True);p.text(700,472,'Ala de escuadra',23)
p.line(840,460,840,495,TEAL,2);p.text(700,793,'Esquema en corte de una ranura',21,DARK)
p.note('La tuerca apoya detrás de la ranura. No taladrés los perfiles.');p.save()

p=Plate('paso-03-patas','03 / Montá las cuatro patas','La cara plana toca el aluminio; el alojamiento profundo mira hacia la mesa.')
p.label('A',75,215,'Reconocé la pieza');p.label('B',650,215,'Orden de montaje, en corte')
render(p,[(mesh('ft_foot_x4'),TEAL)],(70,270,430,380))
p.text(90,735,'4 patas + 4 M5×16',26,TEAL,True);p.text(90,780,'4 tuercas RN05BM5',24)
profile_top(p,695,285,375,120);p.rect(840,365,90,35,ORANGE);p.text(680,262,'Ranura inferior del perfil',23)
# Foot cutaway, roof adjacent profile, open counterbore below.
p.rect(775,460,220,230,TEAL);p.rect(810,565,150,126,PAPER,PAPER);p.rect(875,459,20,111,PAPER,PAPER)
p.s.append('<g transform="rotate(180 885 765)">');bolt(p,885,765,75);p.s.append('</g>');p.arrow((1040,760),(1040,485))
p.text(670,440,'Cara plana arriba',23);p.text(690,785,'M5×16',23);p.text(690,816,'desde abajo',21)
p.rect(775,850,220,8,ORANGE,ORANGE);p.text(1015,857,'EVA 1 mm',20)
p.note('Centros a 10 mm de los extremos largos. Las cuatro patas deben apoyar.');p.save()

p=Plate('paso-04-cama','04 / Bajá la cama sobre sus travesaños','Los dos perfiles delgados de 190 mm quedan por debajo del marco.')
a=frame()
for y in (107.5,207.5):a.append((box([190,20,10],[0,y,-5]),ORANGE))
# Phone bed print Z is installation up. Center top envelope at nominal location.
bed=mesh('fdm_phone_bed_x1',center=[0,157.5,85])
q=render(p,a+[(bed,TEAL)],(55,215,725,600))
p.arrow(q([-45,157.5,70]),q([-45,157.5,10]))
p.text(810,285,'CAMA FIJA',26,TEAL,True)
p.text(810,332,'4 avellanados\nM3×8\n+ 4 RN05BM3',25)
p.text(810,495,'TRAVESAÑOS',26,ORANGE,True)
p.text(810,540,'2 × 190 mm\nRanura arriba\n10 mm de alto',25)
p.text(75,830,'Centros desde el frente: 107,5 y 207,5 mm. Cuatro escuadras adicionales.',23)
p.note('La cama queda fija y sin torsión; las cuatro cabezas quedan al ras.');p.save()

p=Plate('paso-05-rieles','05 / Alineá los rieles largos','Primero fijá un lado; dejá el otro ajustable hasta presentar el puente.')
# Large plan with a separate bolt/rail close-up.
for x in (110,450):p.rect(x,300,40,480,'#dce3e2')
for y in (300,753):p.rect(150,y,300,27,'#dce3e2')
for x in (120,460):
    p.rect(x,386,20,338,TEAL)
    for y in range(399,720,27):p.circle(x+10,y,3,PAPER,TEAL)
    p.rect(x-13,535,46,58,DARK)
p.text(300,270,'FONDO',23,bold=True,anchor='middle');p.text(300,856,'FRENTE',23,bold=True,anchor='middle')
p.line(80,780,80,724,ORANGE,2);p.line(70,780,95,780,ORANGE);p.line(70,724,95,724,ORANGE)
p.text(170,816,'41,5 mm desde el frente',22,TEAL)
p.text(715,270,'Riel → tornillo → tuerca',25,bold=True)
profile_top(p,700,650,370,100);p.rect(790,550,190,35,TEAL)
for x in (830,940):bolt(p,x,420,88);p.arrow((x,515),(x,545))
p.rect(805,720,65,22,ORANGE);p.rect(915,720,65,22,ORANGE)
p.text(710,345,'M3×8 en los agujeros reales',22);p.text(710,802,'RN05BM3 dentro del perfil',23)
p.note('Mantené los carros en sus rieles. No los saqués por el extremo.');p.save()

p=Plate('paso-06-puente','06 / Uní los dos carros con el puente','Las bocas avellanadas miran hacia arriba. Los nombres de archivo están invertidos.')
# Invert print rotation X180, then native Z spin180 to installed XY orientation.
R=[[-1,0,0],[0,1,0],[0,0,-1]]
left=mesh('fdm_xy_joint_right_x1',R,[-96,0,36]);right=mesh('fdm_xy_joint_left_x1',R,[96,0,36])
objs=[(box([185,20,10],[0,0,0]),GRAY),(left,TEAL),(right,TEAL),(box([150,9,7],[0,0,66]),DARK)]
for x in (-105,105):
    objs.extend([(box([20,39.9,8],[x,0,0]),DARK),(box([9,82,7],[x,0,-9]),GRAY)])
q=render(p,objs,(75,300,1050,370),'iso')
for x in (-96,96):p.arrow(q([x,0,28]),q([x,0,7]))
p.text(75,235,'LADO IZQUIERDO',25,TEAL,True);p.text(75,274,'Archivo: xy_joint_right',21)
p.text(790,235,'LADO DERECHO',25,TEAL,True);p.text(790,274,'Archivo: xy_joint_left',21)
p.text(75,727,'4 M3×10 avellanados\npor unión al carro',25)
p.text(665,727,'1 M5×12 avellanado + RN05BM5\npor unión al perfil',25)
p.text(75,830,'Puente: 185 mm. Riel corto: 150 mm, con 17,5 mm libres a cada extremo.',23)
p.note('El puente debe deslizar a mano sin torcerse ni trabarse.');p.save()

p=Plate('paso-07-motores','07 / Armá A y B por separado','Los cuerpos quedan hacia dentro del marco y los ejes apuntan hacia arriba.')
Rx=[[1,0,0],[0,-1,0],[0,0,-1]]
for i,letter in enumerate(('A','B')):
    ox=40+590*i
    mount=mesh(f'fdm_motor_mount_{letter}_x1',Rx,center=[0,0,28])
    q=render(p,[(box([42,42,40],[0,0,-25]),DARK),(cyl(2.5,55,[0,0,20]),GRAY),(mount,TEAL),(cyl(8,14,[0,0,80]),ORANGE)],(ox,265,530,425))
    p.text(ox+25,220,f'{letter} · '+('IZQUIERDO' if i==0 else 'DERECHO'),28,TEAL,True)
    p.arrow(q([27,0,40]),q([27,0,0]))
    p.text(ox+25,735,'4 M3×6 al motor',25)
    p.text(ox+25,777,'2 '+('M5×16' if i==0 else 'M5×20')+' al marco',25,TEAL,True)
    p.text(ox+25,818,'Patas integradas: '+('8 mm' if i==0 else '12 mm'),23)
p.note('A y B no llevan los mismos M5. No agregués separadores bajo sus patas.');p.save()

p=Plate('paso-08-mapa-poleas','08 / Ubicá los diez ejes','Plano visto desde tu posición al frente. Dos columnas dobles van al fondo.')
# diagram large enough all ten nodes named and side pockets distinguish
p.rect(295,270,610,525,'none','#b5c4c7')
positions=[(325,310,'D'),(325,380,'B'),(875,310,'D'),(875,380,'A'),(325,755,'B'),(875,755,'A'),(410,550,'A'),(485,610,'T↓'),(790,550,'B'),(715,610,'T↑')]
for x,y,t in positions:p.circle(x,y,24,PALE);p.text(x,y+8,t,22,TEAL,True,'middle')
p.rect(420,518,360,15,GRAY,INK)
p.text(600,238,'FONDO · MOTORES',25,bold=True,anchor='middle');p.text(600,841,'FRENTE',25,bold=True,anchor='middle')
p.text(55,325,'EXTERIOR\ntrasero',22);p.line(190,326,298,310)
p.text(55,405,'INTERIOR\ntrasero',22);p.line(190,400,298,380)
p.text(55,570,'LJ1 · frontal',22);p.line(213,567,383,550)
p.text(55,641,'LJ2 · inclinada',22);p.line(240,635,458,610)
p.text(950,566,'RJ1',23);p.line(925,562,817,550)
p.text(950,633,'RJ2',23);p.line(925,627,742,610)
p.text(60,710,'D: doble\nA: lisa alta\nB: lisa baja',22)
p.text(970,710,'T↑: dentada alta\nT↓: dentada baja',19)
p.note('10 ejes: 4 hombros de 10 mm y 6 de 20 mm. Doce poleas en total.');p.save()

p=Plate('paso-09-arandelas','09 / Armá cada columna en este orden','Leé de abajo hacia arriba: plástico → arandelas → polea(s) → cabeza del eje.')
for x,title,kind in [(240,'BAJA','low'),(600,'ALTA','high'),(960,'DOBLE','double')]:
    p.text(x,223,title,27,TEAL,True,'middle')
    p.rect(x-72,730,144,55,TEAL);p.text(x,820,'Soporte impreso',21,anchor='middle')
    p.line(x,285,x,730,DARK,10)
    # Levels are intentionally exploded; ring symbol keeps axial order clear.
    levels=([(705,'0,5',ORANGE),(595,'POLEA',GRAY),(425,'superiores',ORANGE)] if kind=='low' else [(688,'9 mm',PALE),(570,'0,5',ORANGE),(465,'POLEA',GRAY),(340,'superiores',ORANGE)] if kind=='high' else [(705,'0,5',ORANGE),(600,'POLEA',GRAY),(520,'0,5',ORANGE),(425,'POLEA',GRAY),(315,'superiores',ORANGE)])
    for yy,lab,c in levels:
        hh=45 if lab=='POLEA' else 58 if lab=='9 mm' else 10
        p.rect(x-55,yy-hh/2,110,hh,c,INK,3)
        p.text(x+75,yy+7,lab,20)
    p.rect(x-32,260,64,22,DARK,DARK,7)
    p.text(x,865,'Hombro '+('10' if kind=='low' else '20')+' mm',23,bold=True,anchor='middle')
p.note('Las arandelas apoyan en el aro interior del rodamiento; cada polea gira libre.');p.save()

p=Plate('paso-10-ejes','10 / Separá los cuatro ejes móviles','Solo esos cuatro requieren revisar y ajustar la punta roscada. No el hombro liso.')
p.text(70,232,'6 EJES EN BLOQUES FIJOS',26,TEAL,True)
p.rect(100,290,72,70,DARK);p.rect(172,310,380,30,GRAY);p.rect(552,315,150,20,ORANGE)
p.text(810,335,'Rosca: 8 mm',27,bold=True)
p.text(70,442,'4 EJES EN UNIONES MÓVILES',26,TEAL,True)
p.rect(100,510,72,70,DARK);p.rect(172,530,380,30,GRAY);p.rect(552,535,140,20,ORANGE)
p.line(692,509,692,581,ORANGE,4,'6 5');p.text(765,551,'Rosca: 7,2–7,5 mm',26,bold=True)
p.line(552,590,692,590,ORANGE,2);p.line(552,580,552,603,ORANGE);p.line(692,580,692,603,ORANGE)
p.text(205,395,'Hombro liso: se conserva completo',23)
p.arrow((560,670),(560,605));p.text(70,715,'Medí desde el final del hombro hasta la punta.',25)
p.text(70,765,'Arandelas superiores nominales:',25,bold=True)
p.text(70,805,'Corto fijo: 0,5 + 0,3  /  Corto móvil: 0,3 + 0,3 + 0,2 mm',24)
p.text(70,845,'Largo: 0,5 + 0,5 + 0,5 + 0,3 mm. Juego final: 0,1–0,3 mm.',24)
p.note('Punta retraída ≥0,5 mm en las uniones. Medí y quitá toda rebaba fuera del riel.');p.save()

p=Plate('paso-11-cuna','11 / Sujetá el actuador en la cuna','Las dos barras apoyan en los bordes metálicos, sin apretar la bobina.')
# Recover source-native orientations from print rotations, then Z-down→up.
inv_cradle=[[1,0,0],[0,0,-1],[0,1,0]]
cr=mesh('ft412_solenoid_cradle',inv_cradle,[0,0,23])
bar=mesh('ft412_clamp_bar_x2',inv_cradle,[0,32.5,0])
objs=[(cr,TEAL),(box([14,17,29.7],[0,38,19.35]),GRAY)]
for z in (7,31.7):objs.append((shifted(bar,[0,36,z]),TEAL))
# Native Z points toward tip. Mirror to physical vertical for this illustration.
for m,c in objs:
    m.vertices[:,2]*=-1;m.invert()
q=render(p,objs,(75,260,720,540),'iso')
p.text(825,280,'1  CUNA',25,TEAL,True)
p.text(825,325,'Tuercas M3 en\nlos canales traseros',23)
p.text(825,447,'2  ACTUADOR',25,bold=True);p.text(825,493,'Cuerpo metálico:\nesquema nominal',22)
p.text(825,615,'3  DOS BARRAS',25,TEAL,True);p.text(825,662,'4 M3×25\n+ 4 tuercas M3',23)
p.arrow(q([0,65,-7]),q([0,40,-7]));p.arrow(q([0,65,-31.7]),q([0,40,-31.7]))
p.text(75,838,'La cuna al carro: 4 M3×8 en la base + 2 avellanados M3×10 en la pared.',23)
p.note('Vástago, resorte y cables libres. Probá el retorno a mano, sin corriente.');p.save()

p=Plate('paso-12-acoplador','12 / Cerrá el acoplador alrededor de la punta','La rosca de la punta entra en una cavidad lisa. No se enrosca en el plástico.')
rr=mesh('ft412_coupler_rear',[[1,0,0],[0,0,1],[0,-1,0]],[0,-23,9.4])
ff=mesh('ft412_coupler_front',inv_cradle,[0,23,9.4])
objs=[(rr,TEAL),(ff,TEAL),(cyl(2.5,10,[0,0,1]),GRAY),(cyl(2.5,4.9,[0,0,10.85]),GRAY),(cyl(4.45,4.5,[0,0,15.55]),ORANGE),(cyl(3.5,6,[0,0,20.8]),GRAY)]
for m,c in objs:
    m.vertices[:,2]*=-1;m.invert()
q=render(p,objs,(65,265,740,480),'iso')
p.arrow(q([0,-20,-9]),q([0,-6,-9]));p.arrow(q([0,20,-9]),q([0,6,-9]))
p.text(830,280,'DOS MITADES',25,TEAL,True);p.text(830,325,'2 M3×16\n+ 2 tuercas M3',24)
p.text(830,460,'COLLAR RETENIDO',24,ORANGE,True);p.text(830,507,'Malla libre\ny sin comprimir',24)
p.text(830,630,'M3×6 LATERAL',25,bold=True);p.text(830,676,'Sujeta el conductor\nde referencia',22)
p.text(70,819,'Dejá la separación entre mitades; no las juntés apretando de más.',24)
p.note('Capuchón y collar quedan sujetos; el vástago vuelve completo y sin carga lateral.');p.save()

p=Plate('paso-13-electronica','13 / Presentá la electrónica sin conectar','Usá el soporte terminado, frío y limpio en las zonas de montaje.')
q=render(p,[(mesh('fdm_pcb_holder_electronics_x1'),TEAL)],(65,250,760,530),'top')
p.text(70,240,'VISTA SUPERIOR DE LA PIEZA',22,TEAL,True)
render(p,[(mesh('fdm_5648_retainer_x1'),ORANGE)],(825,600,250,170),'iso')
p.text(825,270,'DLC32',26,bold=True);p.text(825,312,'4 M3×10\nPlaca sin doblar',24)
p.text(825,445,'MÓDULO 5648',25,bold=True);p.text(825,488,'Sobre sus apoyos;\nretén sobre las orejas',22)
p.line(805,315,*q([30,-2,-15]),ORANGE,2)
p.line(805,460,*q([-50.3,19.89,-15.7]),ORANGE,2)
for pt in ([30,-2,-15],[-50.3,19.89,-15.7]):p.circle(*q(pt),7,ORANGE,ORANGE)
p.text(825,803,'Retén pequeño',23,ORANGE,True)
p.text(70,820,'El ala y el protector del interruptor miran hacia fuera del marco trasero.',24)
p.note('2 M5×12 avellanados + 2 RN05BM5 fijan el soporte. Todavía sin alimentación.');p.save()

p=Plate('paso-14-interruptor','14 / Revisá el interruptor en la pieza','Esta prueba se hace ahora, con el primer soporte impreso y sin corriente.')
p.label('A',75,225,'Pasá la rosca por el agujero');p.label('B',675,225,'Mirá por detrás')
# Deliberately diagrammatic S301T: no CAD fit claimed for screw terminal model.
p.rect(210,385,220,28,TEAL);p.rect(280,420,80,115,DARK);p.rect(303,290,34,130,GRAY)
p.line(320,290,345,255,DARK,12);p.rect(282,330,76,15,ORANGE);p.rect(282,365,76,12,GRAY)
p.arrow((460,480),(460,395));p.text(75,630,'Arandela y tuerca\nsujetan el cuerpo al soporte.',25)
p.rect(735,355,350,250,'none',TEAL);p.rect(835,390,150,140,DARK)
for x in (860,960):
    p.rect(x-12,530,24,58,GRAY);p.circle(x,558,8,PAPER,INK)
    p.line(x,590,x,705,ORANGE,9)
p.text(690,755,'Dos terminales con tornillo',25,bold=True)
p.text(690,800,'Dejá espacio para cable aislado.',23)
p.text(75,780,'Esquema del S301T recibido.\nEl encaje real sigue por comprobar.',22,DARK)
p.note('Si un terminal toca plástico, placa o aluminio: retiralo y revisamos la holgura.');p.save()

p=Plate('paso-15-tubo','15 / Dejá holgura para los cables','El soporte largo del tubo va junto al soporte electrónico, en el fondo.')
render(p,[(mesh('fdm_tube_holder_x1'),TEAL)],(70,260,450,450),'iso')
p.text(75,770,'2 M5×12 avellanados\n+ 2 RN05BM5',25,TEAL,True)
p.rect(690,345,380,310,'none',GRAY);p.rect(730,485,300,20,GRAY);p.rect(845,465,70,60,TEAL)
p.s.append(f'<path d="M1030 350 C1150 190 650 165 880 465" fill="none" stroke="{ORANGE}" stroke-width="13"/>')
p.arrow((875,570),(745,570));p.arrow((890,570),(1020,570))
p.text(690,725,'Recorré el espacio a mano.',25,bold=True)
p.text(690,771,'El tubo no tira del cabezal\nni entra en las correas.',24)
p.note('Alojamiento del tubo hacia arriba. Conservá la curva y el retorno del actuador.');p.save()

p=Plate('paso-16-tornillos','16 / No confundás las cabezas','La medida de largo empieza en un lugar distinto según el tornillo.')
for x,fh,title in [(250,False,'REDONDEADA · BHCS'),(850,True,'AVELLANADA · FHCS')]:
    p.text(x,245,title,26,TEAL,True,'middle');bolt(p,x,355,300,fh)
    top=341 if fh else 359
    p.line(x+100,top,x+100,655,ORANGE,3)
    p.line(x+84,top,x+120,top,ORANGE,3);p.line(x+84,655,x+120,655,ORANGE,3)
    p.text(x+140,505,'L',32,ORANGE,True)
    p.text(x,760,'Incluye la cabeza' if fh else 'Desde debajo de la cabeza',25,bold=True,anchor='middle')
    p.text(x,813,'Cabeza al ras del avellanado' if fh else 'Cabeza sobre su asiento',22,anchor='middle')
p.note('Separá las longitudes en bandejas. Un tornillo no debe hacer fondo antes de sujetar.');p.save()

print(json.dumps({'newInstructionPlates':16,'verifiedSTLDesigns':len(parts),'geometryModified':False}))
