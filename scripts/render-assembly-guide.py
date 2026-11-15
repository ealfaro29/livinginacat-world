"""Render Spanish assembly illustrations from released meshes and the guide PDF.

Run with scripts/assembly-guide-requirements.txt installed. Does not alter CAD,
print progress, the original release archive, or printer state.
"""
from pathlib import Path
import hashlib
import html
import json
import subprocess
import re
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import trimesh
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak, KeepTogether
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT/'public/assets/assembly'
ASSETS.mkdir(parents=True, exist_ok=True)
OUT = ROOT/'public/downloads/guia-ensamblaje-ft412-es.pdf'
OUT.parent.mkdir(parents=True, exist_ok=True)
INK, TEAL, MINT, PAPER, ORANGE = '#153b37', '#087f79', '#dceee4', '#faf8f2', '#b96926'
plt.rcParams.update({'font.family':'DejaVu Sans','svg.fonttype':'none','text.color':INK,'font.size':10})
manifest = json.loads((ROOT/'hardware/ft412/qa/print-manifest.json').read_text())
parts = {p['part']:p for p in manifest['parts']}
labels = {
 'fdm_motor_mount_A_x1':('Motor A · patas de 8 mm','Lado izquierdo'),
 'fdm_motor_mount_B_x1':('Motor B · patas de 12 mm','Lado derecho'),
 'fdm_idler_mount_front_x2':('Bloque delantero','Una pieza en cada costado'),
 'fdm_idler_mount_motor_x2':('Bloque trasero','Dos ejes por bloque'),
 'fdm_xy_joint_right_x1':('Unión del lado izquierdo','Archivo: xy_joint_right'),
 'fdm_xy_joint_left_x1':('Unión del lado derecho','Archivo: xy_joint_left'),
 'fdm_belt_clamp_x1':('Abrazadera de correa','Sobre el carro del riel corto'),
 'fdm_tube_holder_x1':('Soporte largo del tubo','La pieza larga de la tanda de ocho'),
 'fdm_phone_bed_x1':('Cama del teléfono','Apoyo fijo'),
 'ft_foot_x4':('Pata','Una en cada esquina'),
 'ft412_solenoid_cradle':('Cuna del actuador','Sostiene el Adafruit 412'),
 'ft412_clamp_bar_x2':('Barra de sujeción','Presiona los bordes metálicos'),
 'ft412_coupler_rear':('Acoplador · mitad trasera','Retiene el capuchón y el collar'),
 'ft412_coupler_front':('Acoplador · mitad delantera','Incluye el contacto del conductor'),
 'fdm_pcb_holder_electronics_x1':('Soporte de electrónica','En impresión al cierre de esta edición'),
 'fdm_5648_retainer_x1':('Retén del módulo 5648','La pieza pequeña de la tanda de ocho'),
}
groups = [list(labels)[:8], list(labels)[8:]]
for gi, names in enumerate(groups):
    fig=plt.figure(figsize=(8.1,10.8),facecolor=PAPER)
    fig.text(.06,.97,'PIEZAS  /  '+('ESTRUCTURA Y TRANSMISIÓN' if gi==0 else 'CAMA, CABEZAL Y ELECTRÓNICA'),fontsize=15,weight='bold',color=INK)
    fig.text(.06,.944,'Vistas de los STL originales · ampliación individual, sin escala común',fontsize=9)
    for i,name in enumerate(names):
        p=parts[name]; f=ROOT/'hardware/ft412'/p['stl']
        assert hashlib.sha256(f.read_bytes()).hexdigest()==p['stl_sha256'],name
        mesh=trimesh.load_mesh(f)
        ax=fig.add_subplot(4,2,i+1,projection='3d',facecolor=PAPER)
        mesh.vertices-=mesh.bounds.mean(axis=0)
        coll=Poly3DCollection(mesh.triangles,facecolors=TEAL,edgecolors=TEAL,linewidths=0,shade=True,lightsource=matplotlib.colors.LightSource(azdeg=315,altdeg=45))
        ax.add_collection3d(coll)
        radius=mesh.extents.max()*.72
        for fn in (ax.set_xlim,ax.set_ylim,ax.set_zlim):fn(-radius,radius)
        ax.set_box_aspect((1,1,1));ax.view_init(32,-58);ax.set_axis_off()
        title,desc=labels[name]
        ax.text2D(.03,.99,f'{title}  ×{p["quantity"]}',transform=ax.transAxes,fontsize=10,weight='bold',va='top')
        ax.text2D(.03,.90,desc,transform=ax.transAxes,fontsize=7.5,va='top')
        dims=' × '.join(f'{v:.1f}'.replace('.',',') for v in p['print_bbox_mm'])
        ax.text2D(.03,.04,dims+' mm · archivo',transform=ax.transAxes,fontsize=8)
    fig.subplots_adjust(left=.02,right=.98,bottom=.035,top=.925,hspace=.04,wspace=.01)
    fig.text(.06,.016,'La forma impresa se comprueba físicamente. Estas vistas no certifican el encaje.',fontsize=8)
    fig.savefig(ASSETS/('piezas-estructura.png' if gi==0 else 'piezas-cabezal.png'),dpi=190,facecolor=PAPER)
    plt.close(fig)

def save_diagram(fig,name):
    fig.savefig(ASSETS/(name+'.svg'),bbox_inches='tight',facecolor=PAPER)
    fig.savefig(ASSETS/(name+'.png'),dpi=180,bbox_inches='tight',facecolor=PAPER)
    plt.close(fig)

fig,ax=plt.subplots(figsize=(9,8.4),facecolor=PAPER);ax.set_facecolor(PAPER)
for x in (-115,95):ax.add_patch(Rectangle((x,0),20,355,facecolor=MINT,edgecolor=INK,lw=1.5))
for z in (0,335):ax.add_patch(Rectangle((-95,z),190,20,facecolor=MINT,edgecolor=INK,lw=1.5))
for z in (107.5,207.5):
    ax.add_patch(Rectangle((-95,z-5),190,10,fill=False,edgecolor=ORANGE,lw=1.8,ls='--'))
    ax.annotate(f'Travesaño bajo la cama\ncentro a {str(z).replace(".",",")} mm',xy=(70,z),xytext=(155,z),ha='left',va='center',fontsize=9,arrowprops={'arrowstyle':'-','color':ORANGE},color=ORANGE)
for x in (-105,105):
    ax.add_patch(Rectangle((x-4.5,41.5),9,250,facecolor=TEAL,edgecolor=INK,lw=.6))
    for z in (10,345):ax.add_patch(Circle((x,z),12,fill=False,edgecolor=ORANGE,ls=':'))
for x,t in [(-47.5,'A'),(47.5,'B')]:
    ax.add_patch(Rectangle((x-21,292),42,42,facecolor='#dce4e4',edgecolor=INK));ax.text(x,313,t,ha='center',va='center',fontsize=16,weight='bold')
ax.annotate('',xy=(-115,-30),xytext=(115,-30),arrowprops={'arrowstyle':'<->','color':INK})
ax.text(0,-43,'230 mm exteriores',ha='center',fontsize=11)
ax.annotate('',xy=(-145,0),xytext=(-145,355),arrowprops={'arrowstyle':'<->','color':INK})
ax.text(-160,177.5,'355 mm exteriores',ha='center',va='center',rotation=90,fontsize=11)
ax.text(0,380,'FONDO · MOTORES',ha='center',weight='bold',fontsize=13)
ax.text(0,-70,'FRENTE · vos estás aquí',ha='center',weight='bold',fontsize=12)
ax.text(0,252,'Cama fija debajo\ndel puente móvil',ha='center',fontsize=11)
ax.text(0,165,'El riel de cada costado va\nde 41,5 a 291,5 mm\ndesde el frente exterior',ha='center',fontsize=10,color=TEAL)
ax.annotate('Patas: centro a 10 mm\nde los extremos largos',xy=(105,10),xytext=(155,35),fontsize=9,ha='left',arrowprops={'arrowstyle':'-','color':ORANGE},color=ORANGE)
ax.text(150,320,'2 costados: 20×40 ×355\n2 extremos: 20×40 ×190\n2 travesaños: 10×20 ×190\nPuente móvil: 10×20 ×185\n(no dibujado)',fontsize=9,va='top')
ax.set_xlim(-180,315);ax.set_ylim(-90,400);ax.set_aspect('equal');ax.axis('off')
fig.suptitle('Marco FT412 · vista superior nominal',fontsize=17,weight='bold',x=.5,y=.98)
save_diagram(fig,'marco')

fig,axes=plt.subplots(1,2,figsize=(11,7.5),facecolor=PAPER)
for bi,ax in enumerate(axes):
    ax.set_facecolor(PAPER)
    ax.add_patch(Rectangle((0,0),100,150,fill=False,edgecolor='#b7c7c4',lw=7))
    # Route waypoints in source order; schematic only, no wraps/tangencies.
    points=np.array([(42,70),(15,64),(6,12),(6,124),(29,124),(6,142),(94,142),(85,76),(58,70)],dtype=float)
    if bi:points[:,0]=100-points[:,0]
    col=TEAL if bi==0 else ORANGE
    ax.plot(points[:,0],points[:,1],color=col,lw=2.6,zorder=2)
    for i,(x,y) in enumerate(points):
        ax.add_patch(Circle((x,y),3.8,facecolor=PAPER,edgecolor=col,lw=1.5,zorder=3))
        ax.text(x,y,str(i+1),ha='center',va='center',fontsize=8,weight='bold',zorder=4)
    if not bi:
        labs=[(15,54,'2 LJ2 dentada'),(7,2,'3 Del. izq.'),(6,113,'4 Tras. izq. interior'),(43,114,'Motor A'),(5,154,'6 Tras. izq. exterior'),(78,154,'7 Tras. der. exterior'),(63,87,'8 RJ1 lisa')]
    else:
        labs=[(76,54,'2 RJ2 dentada'),(86,2,'3 Del. der.'),(75,113,'4 Tras. der. interior'),(57,114,'Motor B'),(80,154,'6 Tras. der. exterior'),(3,154,'7 Tras. izq. exterior'),(28,87,'8 LJ1 lisa')]
    for x,y,label in labs:ax.text(x,y,label,fontsize=7.8,ha='center',color=INK)
    ax.text(50,60,'CARRO',ha='center',fontsize=8,weight='bold')
    ax.text(50,-13,'FRENTE',ha='center',fontsize=10,weight='bold')
    ax.set_title(('A · PLANO BAJO' if bi==0 else 'B · PLANO ALTO'),fontsize=15,weight='bold',color=col,pad=14)
    ax.text(50,-29,'1 y 9: extremos retenidos en el carro\n6 y 7: '+('poleas bajas' if bi==0 else 'poleas altas')+' de las columnas dobles',ha='center',fontsize=8.5)
    ax.set_xlim(-18,118);ax.set_ylim(-35,168);ax.set_aspect('equal');ax.axis('off')
fig.suptitle('Dos correas independientes · planos separados 9 mm nominales',fontsize=15,weight='bold',y=.985)
fig.text(.5,.025,'Esquema de secuencia, sin escala. Las líneas unen centros: no representan envolturas ni longitud de corte.',ha='center',fontsize=8.5)
fig.subplots_adjust(top=.88,bottom=.09,wspace=.20,left=.03,right=.97)
save_diagram(fig,'correas')

# Single source for web and PDF: the Markdown token stream from the site's parser.
tokens=json.loads(subprocess.check_output(['node','--input-type=module','-e',
    "import fs from 'node:fs'; import { marked } from 'marked'; process.stdout.write(JSON.stringify(marked.lexer(fs.readFileSync('docs/ASSEMBLY-ES.md','utf8'))));"],cwd=ROOT,text=True))
fontdir=Path(matplotlib.get_data_path())/'fonts/ttf'
for face,file in [('Guide','DejaVuSans.ttf'),('Guide-Bold','DejaVuSans-Bold.ttf'),('Guide-Oblique','DejaVuSans-Oblique.ttf')]:pdfmetrics.registerFont(TTFont(face,str(fontdir/file)))
pdfmetrics.registerFontFamily('Guide',normal='Guide',bold='Guide-Bold',italic='Guide-Oblique',boldItalic='Guide-Bold')
S={
 'body':ParagraphStyle('body',fontName='Guide',fontSize=9.4,leading=14,textColor=colors.HexColor(INK),spaceAfter=8),
 'small':ParagraphStyle('small',fontName='Guide',fontSize=7.7,leading=10.4,textColor=colors.HexColor(INK),spaceAfter=0),
 'h1':ParagraphStyle('h1',fontName='Guide-Bold',fontSize=29,leading=34,textColor=colors.HexColor(INK),spaceAfter=16),
 'h2':ParagraphStyle('h2',fontName='Guide-Bold',fontSize=21,leading=26,textColor=colors.HexColor(INK),spaceAfter=15,keepWithNext=True),
 'h3':ParagraphStyle('h3',fontName='Guide-Bold',fontSize=12,leading=16,textColor=colors.HexColor(TEAL),spaceBefore=9,spaceAfter=8,keepWithNext=True),
 'list':ParagraphStyle('list',fontName='Guide',fontSize=9.4,leading=14,textColor=colors.HexColor(INK),leftIndent=17,firstLineIndent=-15,spaceAfter=8),
}
def safe(s):return html.escape(s).replace('–','-').replace('—','-').replace('→',' > ')
def inline(ts):
    out=''
    for t in ts:
        kind=t['type'];val=t.get('text','')
        if kind in ('text','escape'):out+=inline(t['tokens']) if t.get('tokens') else safe(val)
        elif kind=='strong':out+='<b>'+inline(t['tokens'])+'</b>'
        elif kind=='em':out+='<i>'+inline(t['tokens'])+'</i>'
        elif kind=='codespan':out+='<font size="8.3">'+safe(val)+'</font>'
        elif kind=='link':
            href=t['href']
            if href.startswith('/'):href='https://livinginacat.world'+href
            elif not href.startswith(('http:','https:','#')):
                from posixpath import normpath
                href='https://github.com/ealfaro29/livinginacat-world/blob/main/'+normpath('docs/'+href)
            out+='<link href="'+html.escape(href,quote=True)+'" color="'+TEAL+'">'+inline(t['tokens'])+'</link>'
        elif kind=='br':out+='<br/>'
        elif kind not in ('image','space'):out+=safe(val)
    return out

PAGE_W,PAGE_H=595.276,841.89
WIDTH=PAGE_W-92
story=[];h2seen=0;current_section=''
def table(tok):
    rows=[tok['header']]+tok['rows']
    cells=[[Paragraph(('<b>' if i==0 else '')+inline(c['tokens'])+('</b>' if i==0 else ''),S['small']) for c in row] for i,row in enumerate(rows)]
    n=len(rows[0]);fractions={2:[.71,.29],3:[.28,.18,.54],4:[.23,.27,.23,.27]}[n]
    obj=Table(cells,colWidths=[WIDTH*f for f in fractions],repeatRows=1,hAlign='LEFT')
    obj.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor(MINT)),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7),('LINEBELOW',(0,0),(-1,0),.7,colors.HexColor(TEAL)),('LINEBELOW',(0,1),(-1,-1),.3,colors.HexColor('#d5dfdc'))]))
    return obj
def add_image(t):
    p=ROOT/'public'/t['href'].lstrip('/')
    if p.suffix=='.svg':p=p.with_suffix('.png')
    from PIL import Image as PILImage
    with PILImage.open(p) as im:w,h=im.size
    max_height=385 if p.stem=='marco' else 610
    scale=min(WIDTH/w,max_height/h)
    story.append(Image(str(p),w*scale,h*scale));story.append(Spacer(1,12))
for tok in tokens:
    kind=tok['type']
    if kind=='heading':
        depth=tok['depth']
        if depth==2:
            if h2seen:story.append(PageBreak())
            h2seen+=1
            current_section=tok['text']
        if depth==3 and tok['text']=='Pasar y ajustar las correas':
            story.append(PageBreak())
        p=Paragraph(inline(tok['tokens']),S['h'+str(min(depth,3))]);p._guide_heading=(depth,tok['text']);story.append(p)
    elif kind=='paragraph':
        if len(tok.get('tokens',[]))==1 and tok['tokens'][0]['type']=='image':add_image(tok['tokens'][0])
        else:story.append(Paragraph(inline(tok['tokens']),S['body']))
    elif kind=='table':story+=[KeepTogether([table(tok),Spacer(1,12)])]
    elif kind=='list':
        for i,item in enumerate(tok['items']):
            prefix=f'{i+tok.get("start",1)}.' if tok['ordered'] else ('[ ]' if item.get('task') else '•')
            inner=' '.join(inline(t.get('tokens',[])) or safe(t.get('text','')) for t in item['tokens'] if t['type']!='space')
            story.append(KeepTogether([Paragraph(prefix+' '+inner,S['list'])]))
    elif kind=='space':pass
    else:
        if tok.get('text'):story.append(Paragraph(safe(tok['text']),S['body']))

class GuideDoc(SimpleDocTemplate):
    def afterFlowable(self,f):
        if hasattr(f,'_guide_heading'):
            depth,title=f._guide_heading
            if depth<=2:
                # Unique stable bookmark using the title rather than internal outline state.
                key=hashlib.sha256(title.encode()).hexdigest()[:16]
                self.canv.bookmarkPage(key);self.canv.addOutlineEntry(title,key,level=0,closed=False)
def furniture(c,doc):
    c.setFillColor(colors.HexColor(INK));c.setFont('Guide-Bold',8)
    c.drawString(46,PAGE_H-29,'LIVING IN A CAT WORLD  /  FT412')
    c.setFont('Guide',7.5);c.drawRightString(PAGE_W-46,PAGE_H-29,'GUÍA DE ENSAMBLAJE · EDICIÓN 1')
    c.setStrokeColor(colors.HexColor('#c7d8d1'));c.setLineWidth(.5);c.line(46,40,PAGE_W-46,40)
    c.setFont('Guide',7.3);c.drawString(46,27,'15 NOV 2026 · Medidas nominales; comprobar el montaje físico')
    c.drawRightString(PAGE_W-46,27,str(doc.page))
doc=GuideDoc(str(OUT),pagesize=(PAGE_W,PAGE_H),leftMargin=46,rightMargin=46,topMargin=57,bottomMargin=57,title='Guía de ensamblaje FT412',author='Living in a Cat World',subject='Montaje FramingTech 355/250 y Adafruit 412; edición 1',pageCompression=1)
doc.build(story,onFirstPage=furniture,onLaterPages=furniture)
print(json.dumps({'pdf':str(OUT.relative_to(ROOT)),'bytes':OUT.stat().st_size,'figures':len(list(ASSETS.iterdir())),'stlHashesVerified':len(parts),'installedPieces':sum(p['quantity'] for p in parts.values())}))
