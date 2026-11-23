"""Render operation cards from ASSEMBLY-ES.md: BOM first, figure, actions, check.
Every assembly operation occupies one landscape A4 workbench card. Supplemental
stack tables and reference appendices follow without dropping source content.
"""
from pathlib import Path
import html, re, json, subprocess, tempfile, hashlib, io
import matplotlib, pymupdf as fitz
from PIL import Image as PILImage
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph,Table,TableStyle,SimpleDocTemplate,PageBreak,Spacer,Image,KeepTogether
from reportlab.lib.utils import ImageReader
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'public/downloads/guia-ensamblaje-ft412-es.pdf'
QA=ROOT/'private/assembly-guide-v3-qa';QA.mkdir(parents=True,exist_ok=True)
TOK=json.loads(subprocess.check_output(['node','--input-type=module','-e',"import fs from 'node:fs';import {marked} from 'marked';process.stdout.write(JSON.stringify(marked.lexer(fs.readFileSync('docs/ASSEMBLY-ES.md','utf8'))));"],cwd=ROOT,text=True))
FD=Path(matplotlib.get_data_path())/'fonts/ttf'
for n,f in [('G','DejaVuSans.ttf'),('GB','DejaVuSans-Bold.ttf'),('GI','DejaVuSans-Oblique.ttf')]:pdfmetrics.registerFont(TTFont(n,str(FD/f)))
pdfmetrics.registerFontFamily('G',normal='G',bold='GB',italic='GI',boldItalic='GB')
INK=colors.HexColor('#173d39');TEAL=colors.HexColor('#087f79');PALE=colors.HexColor('#e4f1ec');ORANGE=colors.HexColor('#cf5b27');PAPER=colors.HexColor('#faf8f2')
W,H=841.89,595.276; M=31;CW=W-2*M
S={n:ParagraphStyle(n,fontName='G',fontSize=sz,leading=lead,textColor=INK,spaceAfter=5) for n,sz,lead in [('body',9.7,13),('small',8.7,11.4),('actions',10,13.2),('h',22,26),('sub',12,16)]}
S['h'].fontName='GB';S['sub'].fontName='GB'
def safe(s):return html.escape(s).replace('–','-').replace('—','-')
def inline(ts):
 out=''
 for t in ts:
  k=t['type'];v=t.get('text','')
  if k in ('text','escape'):out+=inline(t['tokens']) if t.get('tokens') else safe(v)
  elif k in ('strong','em'):out+=('<b>' if k=='strong' else '<i>')+inline(t['tokens'])+('</b>' if k=='strong' else '</i>')
  elif k=='codespan':out+=safe(v)
  elif k=='link':
   url=t['href']
   if url.startswith('#'):url='https://livinginacat.world/documentation/assembly/'+url
   elif url.startswith('/'):url='https://livinginacat.world'+url
   elif not url.startswith('http'):url='https://github.com/ealfaro29/livinginacat-world/blob/main/'+('docs/'+url if not url.startswith('../') else url[3:])
   out+=f'<a href="{html.escape(url,quote=True)}" color="#087f79">'+inline(t['tokens'])+'</a>'
  elif k=='br':out+='<br/>'
  elif k not in ('image','space'):out+=safe(v)
 return out

def par(text,style='body'):return Paragraph(text,S[style])
def drawp(c,text,x,top,width,style='body'):
 p=par(text,style);_,h=p.wrap(width,1000);p.drawOn(c,x,top-h);return h

def table(t,width,compact=False):
 rows=[t['header']]+t['rows'];n=len(rows[0]);frac={2:[.74,.26],3:[.46,.13,.41],4:[.26,.12,.37,.25]}[n]
 cells=[[par(('<b>' if i==0 else '')+inline(v['tokens'])+('</b>' if i==0 else ''),'small') for v in row] for i,row in enumerate(rows)]
 obj=Table(cells,colWidths=[width*f for f in frac],repeatRows=1,hAlign='LEFT')
 obj.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),PALE),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),5),('RIGHTPADDING',(0,0),(-1,-1),5),('TOPPADDING',(0,0),(-1,-1),4 if compact else 6),('BOTTOMPADDING',(0,0),(-1,-1),4 if compact else 6),('LINEBELOW',(0,0),(-1,0),.6,TEAL),('LINEBELOW',(0,1),(-1,-1),.3,colors.HexColor('#cbdad6'))]));return obj

def figdata(token):
 p=ROOT/'public'/token['href'].lstrip('/')
 if p.suffix=='.svg':p=p.with_suffix('.png')
 im=PILImage.open(p).convert('RGB')
 # Remove a legacy plate's repeated title/footer; the operation card supplies them.
 if p.stem.startswith('paso-'):
  sx=im.width/1200;sy=im.height/1000;im=im.crop((35*sx,180*sy,1165*sx,872*sy))
 if p.stem.startswith('inicio-'):
  sx=im.width/1200;sy=im.height/760;im=im.crop((35*sx,115*sy,1165*sx,680*sy))
 return im

def head(c,title,page):
 c.setFillColor(PAPER);c.rect(0,0,W,H,fill=1,stroke=0)
 c.setFillColor(TEAL);c.setFont('GB',8);c.drawString(M,H-22,'FT412 / MANUAL DE ENSAMBLAJE / EDICIÓN 3.3')
 drawp(c,safe(title),M,H-38,CW,'h')
 c.setStrokeColor(colors.HexColor('#ccdad5'));c.line(M,24,W-M,24)
 c.setFillColor(INK);c.setFont('G',7.3);c.drawString(M,12,'22 NOV 2026 · Montaje FramingTech 355/250 · comprobar las piezas reales')
 c.drawRightString(W-M,12,str(page))

# Group the Markdown sections; the guide remains the single public source.
intro=[];groups=[];current=None
for tok in TOK:
 if tok['type']=='heading' and tok['depth']==2:
  current={'title':tok['text'],'tokens':[]};groups.append(current)
 elif current is None:intro.append(tok)
 else:current['tokens'].append(tok)
stepgroups=[g for g in groups if g['title'].startswith('Paso ')]
appendix=[g for g in groups if not g['title'].startswith('Paso ')]
assert len(stepgroups)==30
c=canvas.Canvas(str(QA/'cards.pdf'),pagesize=(W,H),pageCompression=1)
page=1;head(c,'Tu guía para armar, una operación a la vez',page)
y=H-92
for t in intro:
 if t['type']=='paragraph':y-=drawp(c,inline(t['tokens']),M,y,CW,'actions')+12
assert y>32
c.bookmarkPage('inicio');c.addOutlineEntry('Cómo usar esta guía','inicio',level=0);c.showPage();page+=1
report=[]
for group in stepgroups:
 ts=group['tokens'];tables=[t for t in ts if t['type']=='table'];assert tables
 bom=tables[0];paras=[t for t in ts if t['type']=='paragraph']
 def field(prefix):
  matches=[t for t in paras if t.get('text','').startswith('**'+prefix)]
  return inline(matches[0]['tokens']) if matches else ''
 tools=field('Herramientas:');before=field('Antes de montar:');check=field('Comprobá antes de seguir:');note=field('Detalle importante:')
 pics=[t['tokens'][0] for t in paras if len(t.get('tokens',[]))==1 and t['tokens'][0]['type']=='image']
 actions=[t for t in ts if t['type']=='list' and t['ordered']];assert len(actions)==1 and pics and before and check and tools
 head(c,group['title'],page);key='paso'+re.search(r'\d+',group['title'])[0];c.bookmarkPage(key);c.addOutlineEntry(group['title'],key,level=0)
 top=H-88; leftw=292;gap=18;rightx=M+leftw+gap;rightw=CW-leftw-gap
 drawp(c,'NECESITÁS PARA ESTE PASO',M,top,leftw,'sub')
 obj=table(bom,leftw,True);_,th=obj.wrap(leftw,1000);obj.drawOn(c,M,top-23-th)
 ly=top-23-th-10;ly-=drawp(c,tools,M,ly,leftw,'small')+8
 by=top-drawp(c,before,rightx,top,rightw,'body')-8
 im=figdata(pics[0]);maxh=240 if group['title'].startswith(('Paso 23.','Paso 25.')) else 267
 scale=min(rightw/im.width,maxh/im.height);iw,ih=im.width*scale,im.height*scale
 c.drawImage(ImageReader(im),rightx+(rightw-iw)/2,by-ih,width=iw,height=ih)
 mainbottom=min(ly,by-ih)
 y=mainbottom-11
 for i,item in enumerate(actions[0]['items']):
  contents=' '.join(inline(t.get('tokens',[])) or safe(t.get('text','')) for t in item['tokens'] if t['type']!='space')
  y-=drawp(c,f'<b>{i+1}.</b> '+contents,M,y,CW,'actions')+4
 # Put the pass criterion in its own colored strip, sized from actual text.
 chk=par(check,'body');_,ch=chk.wrap(CW-18,1000)
 c.setFillColor(PALE);c.roundRect(M,y-ch-15,CW,ch+12,5,fill=1,stroke=0);chk.drawOn(c,M+9,y-ch-9);y-=ch+23
 if note:y-=drawp(c,note,M,y,CW,'small')+3
 report.append({'step':group['title'],'page':page,'lowestContentY':round(y,2),'materialsHeight':round(th,1),'figureWidth':round(iw,1),'figureHeight':round(ih,1)})
 if y<29:raise RuntimeError(f'Overflow at {group["title"]}: y={y:.1f}')
 c.showPage();page+=1
 # Additional nominal stack table: a dedicated continuation sheet with repeated context.
 for t in tables[1:]:
  head(c,group['title']+' · orden de montaje',page)
  yy=H-90;yy-=drawp(c,'Reutilizá las piezas separadas para este paso. Leé cada columna desde el plástico hacia la cabeza del eje.',M,yy,CW,'actions')+16
  obj=table(t,CW);_,th=obj.wrap(CW,1000);obj.drawOn(c,M,yy-th);yy-=th+22
  yy-=drawp(c,'<b>Arandelas en milímetros.</b> El hombro liso asienta en el soporte y la rosca entra en la tuerca cautiva. Comprobá giro libre y juego real de 0,1–0,3 mm después de apretar.',M,yy,CW,'actions')
  assert yy>30;c.showPage();page+=1
c.save()
# Reference appendices, kept as readable portrait pages.
PW,PH=595.276,841.89;WIDTH=PW-72;story=[]
for group in appendix:
 if story:story.append(PageBreak())
 story.append(par(safe(group['title']),'h'))
 for t in group['tokens']:
  k=t['type']
  if k=='paragraph':
   if len(t.get('tokens',[]))==1 and t['tokens'][0]['type']=='image':
    im=figdata(t['tokens'][0]);buf=io.BytesIO();im.save(buf,format='PNG');buf.seek(0);scale=min(WIDTH/im.width,565/im.height);story.append(Image(buf,im.width*scale,im.height*scale));story.append(Spacer(1,10))
   else:story.append(par(inline(t['tokens'])))
  elif k=='table':story.append(table(t,WIDTH));story.append(Spacer(1,12))
  elif k=='heading':
   if t['text'] in ('Secuencia posterior de puesta en marcha','Tornillos: cantidades por uso'):story.append(PageBreak())
   story.append(par(inline(t['tokens']),'sub'))
  elif k=='list':
   for i,item in enumerate(t['items']):
    contents=' '.join(inline(q.get('tokens',[])) or safe(q.get('text','')) for q in item['tokens'] if q['type']!='space');prefix=f'{i+1}.' if t['ordered'] else ('[ ]' if item.get('task') else '•');story.append(par(prefix+' '+contents))
def furniture(c,d):
 c.setFont('GB',8);c.setFillColor(TEAL);c.drawString(36,PH-24,'FT412 / REFERENCIAS Y COMPROBACIONES / EDICIÓN 3.3');c.setFont('G',7.5);c.drawRightString(PW-36,18,str(page+d.page-1))
doc=SimpleDocTemplate(str(QA/'appendices.pdf'),pagesize=(PW,PH),leftMargin=36,rightMargin=36,topMargin=48,bottomMargin=36)
doc.build(story,onFirstPage=furniture,onLaterPages=furniture)
a=fitz.open(QA/'cards.pdf');b=fitz.open(QA/'appendices.pdf');a.insert_pdf(b);a.set_metadata({'title':'FT412 · Manual de ensamblaje · edición 3.3','author':'Living in a Cat World','subject':'30 operaciones, correcciones REV01 y referencia táctil al marco'});a.save(OUT,garbage=4,deflate=True)
(QA/'layout-check.json').write_text(json.dumps({'stepCount':30,'pages':len(a),'cards':report},ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'pages':len(a),'operationCards':30,'minimumContentY':min(r['lowestContentY'] for r in report),'pdf':str(OUT)}))
