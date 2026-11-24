"""Pliego del producto con tres vistas procedentes del propio CAD."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageOps

root=Path(__file__).resolve().parent
w,h=1680,788
out=Image.new('RGB',(w,h),'#f4f3eb')
p=ImageDraw.Draw(out)
font='/System/Library/Fonts/HelveticaNeue.ttc'
def face(size,bold=False):
    return ImageFont.truetype(font,size,index=1 if bold else 0)
def txt(x,y,t,size,fill='#20322e',bold=False):
    p.text((x,y),t,font=face(size,bold),fill=fill,stroke_width=0)
def rule(x0,y0,x1,y1,color='#c8cbc0'):
    p.line((x0,y0,x1,y1),fill=color,width=2)
txt(45,27,'FT412',29,bold=True)
txt(145,29,'/ V2',26,fill='#287168',bold=True)
txt(45,68,'Consola integrada',52,bold=True)
measure='324 × 398 × 354 mm'
txt(w-46-p.textlength(measure,font=face(29,True)),47,measure,29,bold=True)
sub='Ancho, fondo y altura con cubierta · medidas propuestas'
txt(w-46-p.textlength(sub,font=face(18)),91,sub,18,fill='#52615a')
rule(45,145,w-45,145)
cols=[
 ('outside-iso','Exterior','La pantalla MKS al frente.','La cubierta se levanta por encima del arco.'),
 ('mechanics-iso','Zona de trabajo','Los perfiles y el arco son impresos.','Se conservan los tres rieles de acero.'),
 ('electronics-iso','Piso de electrónica','Pi, MKS, Adafruit y fusible bajo el teléfono.','El volumen ámbar queda para alimentación.'),
]
width=530
for n,(img,title,a,b) in enumerate(cols):
    x=45+n*width
    im=Image.open(root/'.revision'/(img+'.png')).convert('RGB')
    im=ImageOps.contain(im,(width-16,440),method=Image.Resampling.LANCZOS)
    out.paste(im,(x+(width-im.width)//2,166+(440-im.height)//2))
    rule(x,631,x+width-16,631)
    txt(x,648,title,29,bold=True);txt(x,704,a,20);txt(x,736,b,19,fill='#53635c')
out.save(root/'FT412-V2-Vista.png',optimize=True)
