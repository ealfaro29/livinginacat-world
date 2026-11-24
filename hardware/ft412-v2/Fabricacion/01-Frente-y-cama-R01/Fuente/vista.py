"""Two orthographic illustrations projected from the actual print STLs."""
from pathlib import Path

import numpy as np
import trimesh
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
S = 2
W, H = 1440, 690
PAPER, INK, MUTED, RULE = "#f8f8f4", "#202c2d", "#526362", "#c8d1ca"
canvas = Image.new("RGB", (W*S,H*S), PAPER)
draw = ImageDraw.Draw(canvas)
font_dir = Path("/System/Library/Fonts/Supplemental")


def label(x, y, content, size=20, bold=False, fill=INK, anchor="la"):
    font = ImageFont.truetype(str(font_dir/("Arial Bold.ttf" if bold else "Arial.ttf")), size*S)
    draw.text((x*S,y*S),content,font=font,fill=fill,anchor=anchor)


def unit(vector):
    a = np.asarray(vector, dtype=float)
    return a/np.linalg.norm(a)


def view(name, eye, bounds, color):
    mesh = trimesh.load_mesh(ROOT/"Piezas"/(name+".stl"))
    eye = unit(eye)
    right = unit(np.cross([0,0,1],eye))
    up = np.cross(eye,right)
    matrix = np.stack((right,-up,eye),axis=1)
    projected = mesh.vertices @ matrix
    low, high = projected[:,:2].min(axis=0), projected[:,:2].max(axis=0)
    x0,y0,x1,y1=bounds
    scale=min((x1-x0)/(high[0]-low[0]),(y1-y0)/(high[1]-low[1]))
    center=(np.array([x0+x1,y0+y1])/2-(low+high)*scale/2)
    d2 = (projected[:,:2]*scale+center)*S
    light = unit([-.5,-.7,1.1])
    faces = mesh.faces
    depths=projected[faces,2].mean(axis=1)
    for i in np.argsort(depths):
        n = mesh.face_normals[i]
        if np.dot(n,eye) < -.00001:
            continue
        brightness = .59+.41*max(0,np.dot(n,light))
        shade = tuple(np.rint(np.array(color)*brightness).astype(int))
        draw.polygon([tuple(v) for v in d2[faces[i]]],fill=shade)
    return lambda p: (np.asarray(p)@matrix)[:2]*scale+center


label(54,29,"FT412 V2",19,True,MUTED)
label(54,64,"Primera tanda de impresión",42,True)
label(54,123,"First print batch",20,False,MUTED)
draw.line((54*S,169*S,1386*S,169*S),fill=RULE,width=2*S)
draw.line((720*S,191*S,720*S,637*S),fill=RULE,width=1*S)
label(54,192,"01   Cama del iPhone 14",26,True)
label(54,231,"Removable iPhone bed",17,False,MUTED)
label(755,192,"02   Frente de la consola",26,True)
label(755,231,"Console front shell",17,False,MUTED)
deck=view("01_Cama_iPhone14",(.55,-1,1.9),(113,272,601,543),(126,164,159))
front=view("02_Frente_consola",(.74,-1.48,1.0),(798,269,1342,550),(129,146,157))


def pointer(point, elbow, end):
    points=[tuple(np.rint(np.asarray(v)*S).astype(int)) for v in (point,elbow,end)]
    draw.line(points,fill=INK,width=2*S)
    x,y=points[0]; radius=4*S
    draw.ellipse((x-radius,y-radius,x+radius,y+radius),fill="#ead77f",outline=INK,width=S)


pointer(deck((17,54,2.5)),(532,300),(656,300))
label(656,272,"Cámaras / Cameras",15,True,anchor="ra")
pointer(front((48,-48.5,29)),(1253,526),(1362,526))
label(1362,536,"Interruptor / Switch",15,True,anchor="ra")
label(54,593,"130 × 226 × 8,7 mm",22,True)
label(54,629,"Sin soportes / No supports",17,False,MUTED)
label(755,593,"196 × 157 × 85 mm",22,True)
label(755,629,"Soportes de árbol / Tree supports",17,False,MUTED)
canvas.resize((W,H),Image.Resampling.LANCZOS).save(ROOT/"Vista-tanda-01.png")
