"""Resumen del mismo STEP mostrado por el visor más una sección acotada."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont,ImageOps
import json
here=Path(__file__).resolve().parent
q=json.loads((here/'verificacion.json').read_text())
assert q['dimensiones_a_distancia_lente_vidrio']['100']==[196,302,231]
bg='#f4f3eb';ink='#1c312d';gray='#49605a';green='#156c5e';line='#bfcac1'
sheet=Image.new('RGB',(1640,936),bg);p=ImageDraw.Draw(sheet)
fonts='/System/Library/Fonts/HelveticaNeue.ttc'
def font(z,b=False):return ImageFont.truetype(fonts,z,index=1 if b else 0)
def txt(x,y,t,z,fill=ink,b=False,anchor=None):p.text((x,y),t,font=font(z,b),fill=fill,anchor=anchor)
def segment(a,b,c=line,w=2):p.line((a,b),fill=c,width=w)
def pic(name,x,y,w,h):
    im=Image.open(here/'.revision'/(name+'.png')).convert('RGB')
    # The viewport is clean and labelled externally. Crop whitespace only.
    pix=im.load(); background=pix[1,1]
    mask=Image.new('L',im.size,0)
    import PIL.ImageChops
    diff=PIL.ImageChops.difference(im,Image.new('RGB',im.size,background)).convert('L')
    rect=diff.point(lambda k:255 if k>52 else 0).getbbox()
    if rect:
        x0,y0,x1,y1=rect
        im=im.crop((max(x0-18,0),max(y0-18,0),min(im.width,x1+18),min(im.height,y1+18)))
    im=ImageOps.contain(im,(w,h),Image.Resampling.LANCZOS)
    sheet.paste(im,(int(x+(w-im.width)/2),int(y+(h-im.height)/2)))
def dim(x,a,b,t):
    segment((x,a),(x,b),green,2)
    for yy,dd in ((a,1),(b,-1)):
        p.polygon([(x,yy),(x-4,yy+dd*8),(x+4,yy+dd*8)],fill=green)
    txt(x+8,(a+b)/2,t,20,green,True,'lm')
txt(45,25,'FT412',27,ink,True);txt(138,26,'/  V2',25,green,True)
txt(43,67,'Consola compacta',51,ink,True)
txt(1593,39,'196 × 302 × 231 mm',35,ink,True,'ra')
txt(1593,91,'Tamaño exterior con el lente a 100 mm del vidrio',20,gray,False,'ra')
segment((45,147),(1595,147))
pic('outside-iso',43,167,745,586)
txt(49,776,'Vista de conjunto',29,ink,True)
txt(49,823,'El pórtico impreso sostiene la cámara desde los costados.',21,gray)
txt(49,858,'La pantalla y el interruptor quedan al frente.',21,gray)
segment((808,178),(808,892));segment((836,537),(1591,537))
pic('travel-top',830,171,345,345)
txt(1178,205,'Recorrido libre',30,ink,True)
txt(1178,263,'106,1 mm en X',26,green,True)
txt(1178,301,'206,1 mm en Y',26,green,True)
txt(1178,372,'Con 2 mm de reserva en',20,gray)
txt(1178,400,'cada extremo de cada riel.',20,gray)
segment((1178,455),(1213,455),'#167765',5);txt(1224,442,'Patines laterales',19,gray)
segment((1178,485),(1213,485),'#bd6a16',5);txt(1224,472,'Patín del puente',19,gray)
pic('switch-iso',835,559,358,224)
txt(852,807,'Interruptor frontal',24,ink,True)
txt(852,852,'Palanca NKK S301T · I / O',18,gray)
segment((1205,564),(1205,879))
txt(1232,563,'Altura de la cámara',24,ink,True)
z0,zr,zl=824,754,624
for y,t in [(zl,'Lente'),(zr,'Asiento del riel'),(z0,'Vidrio')]:
    segment((1236,y),(1356,y),gray,2);txt(1237,y-25,t,17,gray)
dim(1362,zl,z0,'100 mm');dim(1484,zl,zr,'65 mm');dim(1484,zr,z0,'35 mm')
sheet.save(here/'FT412-V2-Vista.png',optimize=True)
