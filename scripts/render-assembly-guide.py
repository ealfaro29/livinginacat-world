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
import unicodedata
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
 'fdm_pcb_holder_electronics_x1':('Soporte de electrónica','Impresión terminada según el dueño'),
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
    ax.add_patch(Rectangle((-95,z-10),190,20,fill=False,edgecolor=ORANGE,lw=1.8,ls='--'))
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

# Operation-first workbench cards use the same Markdown as the website.
import sys
subprocess.run([sys.executable, str(ROOT/'scripts/render-assembly-book.py')], cwd=ROOT, check=True)
