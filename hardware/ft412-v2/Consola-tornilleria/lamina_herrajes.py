"""Sección de los dos asientos M3, a la misma escala. Genera una lámina del CAD."""
from pathlib import Path
import json
from PIL import Image, ImageDraw, ImageFont
root=Path(__file__).resolve().parent
data=json.loads((root/'verificacion.json').read_text())['herrajes']
s=2; im=Image.new('RGB',(1260*s,610*s),'#f3f3ec'); d=ImageDraw.Draw(im)
ink='#203a36';muted='#4b615b';paper='#fbfbf5';border='#c9d0c2'
plastic='#bcd6c7';steel='#b5c1c3';nut='#b27a48';blue='#416992';gold='#d69b46'
f='/System/Library/Fonts/HelveticaNeue.ttc'
def text(x,y,words,z,color=ink,bold=False):
    d.text((x*s,y*s),words,font=ImageFont.truetype(f,z*s,index=1 if bold else 0),fill=color,stroke_width=0)
def ln(points,c=ink,w=1):
    d.line([(round(x*s),round(y*s)) for x,y in points],fill=c,width=round(w*s),joint='curve')
def poly(points,fill,line=ink):
    q=[(round(x*s),round(y*s)) for x,y in points];d.polygon(q,fill=fill)
    if line:ln(points+[points[0]],line,1.15)
def rect(x0,y0,x1,y1,fill):
    d.rectangle((round(x0*s),round(y0*s),round(x1*s),round(y1*s)),fill=fill)
def card(x):
    d.rounded_rectangle((x*s,117*s,(x+588)*s,526*s),radius=20*s,fill=paper,outline=border,width=s)
def dim(x,y0,y1):
    ln([(x,y0),(x,y1)],muted,1)
    for y,sgn in ((y0,1),(y1,-1)):
        ln([(x-6,y),(x+6,y)],muted);poly([(x,y),(x-3.2,y+sgn*7),(x+3.2,y+sgn*7)],muted,None)
    text(x+10,(y0+y1)/2-11,'8 mm',15,muted,True)
def labels(x,y,txt):
    text(x,y,txt,17,muted)
text(38,19,'FT412  /  V2',18,muted,True)
text(36,47,'Los dos tornillos M3 de la consola',44,ink,True)
card(32);card(640)
def diagram(card_x,flat):
    c=card_x+152; scale=17.; yy=223
    def q(x,z):return (c+x*scale,yy+z*scale)
    def region(points,fill,line=ink):poly([q(a,b) for a,b in points],fill,line)
    def section(z0,z1,outer,cut,color):
        for sg in (-1,1):
            region([(sg*outer,z0),(sg*cut,z0),(sg*cut,z1),(sg*outer,z1)],color)
    title='#7213   Avellanado' if flat else '#7219   Cabeza de botón'
    text(card_x+22,135,title,27,ink,True)
    text(card_x+23,178,'M3 × 8 mm  ·  90°' if flat else 'M3 × 8 mm  ·  base plana',18,muted)
    # The countersunk screw is referenced at its top. The button screw is referenced under its head.
    if flat:
        for sg in (-1,1):
            region([(sg*6,0),(sg*3.5,0),(sg*1.7,1.8),(sg*1.7,3),(sg*6,3)],plastic)
        section(3,4.6,6,1.7,plastic); section(4.6,7.3,6,2.9,plastic)
        section(7.3,9.1,6,1.7,plastic)
        region([(-3.25,.25),(3.25,.25),(1.5,2),(1.5,8.25),(-1.5,8.25),(-1.5,2)],gold)
        for sg in (-1,1):region([(sg*1.5,4.75),(sg*2.7,4.75),(sg*2.7,7.15),(sg*1.5,7.15)],nut)
        region([(-.95,.25),(.95,.25),(.95,1.25),(-.95,1.25)],paper)
        dim(c+126,yy+.25*scale,yy+8.25*scale)
        labels(card_x+343,242,'Caja y pórtico');labels(card_x+343,270,'El cono apoya sobre')
        labels(card_x+343,294,'el plástico impreso.')
        labels(card_x+343,352,'Tuerca cuadrada M3')
        labels(card_x+343,376,'cargada de costado.')
        start,end=4.76,7.14
    else:
        section(0,3.2,4.5,3,steel);section(3.2,6.5,4.5,1.75,steel)
        section(6.5,8.25,6,1.7,plastic);section(8.25,10.95,6,2.9,plastic)
        section(10.95,12.2,6,1.7,plastic)
        region([(-2.85,3.2),(-2.85,2.65),(-2.25,1.85),(-1.5,1.55),(1.5,1.55),(2.25,1.85),(2.85,2.65),(2.85,3.2)],blue)
        region([(-1.5,3.2),(1.5,3.2),(1.5,11.2),(-1.5,11.2)],blue)
        for sg in (-1,1):region([(sg*1.5,8.4),(sg*2.7,8.4),(sg*2.7,10.8),(sg*1.5,10.8)],nut)
        region([(-.95,1.55),(.95,1.55),(.95,2.6),(-.95,2.6)],paper)
        dim(c+126,yy+3.2*scale,yy+11.2*scale)
        labels(card_x+343,241,'Riel de acero');labels(card_x+343,269,'La cabeza queda 1,55 mm');labels(card_x+343,293,'bajo la cara del riel.')
        labels(card_x+343,350,'La rosca la recibe')
        labels(card_x+343,374,'la misma tuerca M3.')
        start,end=8.4,10.8
    for j in range(5):
        z=start+(end-start)*j/5
        ln([q(-1.45,z+.22),q(1.45,z-.12)],'#334442',.9)
    ln([(card_x+24,464),(card_x+564,464)],border)
    text(card_x+23,479,'Los 8 mm incluyen la cabeza.' if flat else 'Los 8 mm se miden debajo de la cabeza.',17,ink,True)
diagram(32,True);diagram(640,False)
text(38,550,'Una llave Allen de 2 mm para ambos.',22,ink,True)
text(562,554,'La pantalla, los ejes de polea y la cámara conservan sus fijaciones propias.',16,muted)
im.resize((1575,762),Image.Resampling.LANCZOS).save(root/'FT412-V2-Herrajes.png',optimize=True)
