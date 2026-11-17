export const VERSION = 1;
export const SOURCES = {
  pi: 'https://pip.raspberrypi.com/documents/RP-008347-DS-1-raspberry-pi-5-mechanical-drawing.pdf',
  mks: 'https://github.com/Macrobase-tech/MKS-DLC32/tree/main/MKS%20DLC32%2BTS24/Hardware',
  mosfet: 'https://learn.adafruit.com/adafruit-mosfet-driver/downloads',
};
// Dimensions describe planning envelopes, not fabrication-ready connector cutouts.
export const LIBRARY = {
  pi: { name: 'Raspberry Pi 5', short: 'Raspberry Pi', size: [85,56,20], color:'#38846d', measured:true, note:'PCB nominal 85 × 56; volumen con conectores reservado a 20 mm. Confirmar alturas.', holes:[[ -39,-24.5],[19,-24.5],[-39,24.5],[19,24.5]], source:SOURCES.pi,
    ports:[{name:'USB + Ethernet',at:[43,0,8],n:[1,0,0],w:53,h:17,space:40},{name:'USB-C / micro HDMI',at:[-12,-28,5],n:[0,-1,0],w:45,h:10,space:25}] },
  cooler: {name:'Disipador CanaKit',short:'Disipador',size:[60,48,18],color:'#65717d',measured:false,note:'Volumen provisional. Medí el disipador que trae tu kit.'},
  fan: {name:'Ventilador CanaKit',short:'Ventilador',size:[40,40,10],color:'#6b7f8c',measured:false,note:'40 × 40 × 10 es una reserva editable; falta medir marco y agujeros.',aperture:32},
  mks: {name:'MKS DLC32 V2.1',short:'MKS DLC32',size:[90,70,20],color:'#296c68',measured:true,note:'PCB 90 × 70; cuatro fijaciones a 82 × 62. Conectores esquemáticos.',holes:[[-41,-31],[-41,31],[41,-31],[41,31]],source:SOURCES.mks,
    ports:[{name:'USB-B',at:[-8,-35,6],n:[0,-1,0],w:13,h:13,space:35},{name:'Entrada 12 V',at:[-23,-35,6],n:[0,-1,0],w:11,h:12,space:25},{name:'Reserva salida de mazo',at:[-10,27,12],n:[0,0,1],w:58,h:12,space:20}]},
  driver: {name:'TMC2209 + disipador',short:'TMC2209',size:[15.24,20.32,16],color:'#b98846',measured:false,note:'Envolvente nominal; verificar altura del disipador y asiento en la MKS.'},
  lcd: {name:'Pantalla TS24-R V2.1',short:'Pantalla TS24-R',size:[80,50,15],color:'#477b97',measured:false,note:'Modelo confirmado en foto. 80 × 50 y ventana 56 × 42 son reservas: verificar medidas y agujeros.',aperture:[56,42]},
  mosfet: {name:'Adafruit 5648',short:'MOSFET 5648',size:[25.4,17.78,13],color:'#566f9b',measured:true,note:'Contorno nominal 25,4 × 17,78. Altura y espacio de cables por comprobar.',source:SOURCES.mosfet},
  switch: {name:'Interruptor NKK S301T',short:'Interruptor 12 V',size:[17,17,32],color:'#bb7745',measured:false,note:'Abertura propuesta Ø12,7. Confirmar cuerpo y terminales de tornillo reales.',aperture:12.7},
  fuse: {name:'Portafusible ATO + 3 A',short:'Portafusible',size:[34,22,26],color:'#817255',measured:false,note:'Reserva para FHAS101; incluir salida y curvas de ambos cables.'},
  custom:{name:'Pieza libre',short:'Pieza libre',size:[30,25,20],color:'#8b7198',measured:false,note:'Volumen libre: ajustá sus medidas.'},
};
export const clone = v => JSON.parse(JSON.stringify(v));
const rad = n => n*Math.PI/180;
const dot = (a,b) => a.reduce((s,x,i)=>s+x*b[i],0);
const cross = (a,b) => [a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]];
const add = (a,b) => a.map((x,i)=>x+b[i]);
const mul = (a,s) => a.map(x=>x*s);
export const round = n => Math.round(n*10)/10;

export function axes(p) {
  const c=Math.cos(rad(p.rotation)),s=Math.sin(rad(p.rotation));
  let u=[1,0,0],v=[0,1,0],w=[0,0,1];
  if(p.face==='front'){u=[0,1,0];v=[0,0,1];w=[1,0,0];}
  if(p.face==='back'){u=[0,-1,0];v=[0,0,1];w=[-1,0,0];}
  if(p.face==='outer'){u=[1,0,0];v=[0,0,1];w=[0,-1,0];}
  if(p.face==='inner'){u=[-1,0,0];v=[0,0,1];w=[0,1,0];}
  if(p.face==='lid'){u=[1,0,0];v=[0,-1,0];w=[0,0,-1];}
  return [add(mul(u,c),mul(v,s)),add(mul(u,-s),mul(v,c)),w];
}
export function point(p,q) {const a=axes(p);return [p.x,p.y,p.z].map((v,i)=>v+q.reduce((s,x,j)=>s+x*a[j][i],0));}
export function vector(p,q){const a=axes(p);return a[0].map((_,i)=>q.reduce((s,x,j)=>s+x*a[j][i],0));}
export function corners(p) {const [w,d,h]=p.size;return [-w/2,w/2].flatMap(x=>[-d/2,d/2].flatMap(y=>[0,h].map(z=>point(p,[x,y,z]))));}
export function bounds(p){const c=corners(p);return {min:[0,1,2].map(i=>Math.min(...c.map(p=>p[i]))),max:[0,1,2].map(i=>Math.max(...c.map(p=>p[i])))};}
export function obb(p){return {c:point(p,[0,0,p.size[2]/2]),a:axes(p),h:p.size.map(n=>n/2)};}
export function intersects(p,q,gap=0) {
  const A=obb(p),B=obb(q),t=B.c.map((v,i)=>v-A.c[i]);
  for(const ax of [...A.a,...B.a,...A.a.flatMap(a=>B.a.map(b=>cross(a,b)))]){
    if(dot(ax,ax)<1e-9)continue;
    const a=A.a.reduce((s,u,i)=>s+Math.abs(dot(ax,u))*A.h[i],0);
    const b=B.a.reduce((s,u,i)=>s+Math.abs(dot(ax,u))*B.h[i],0);
    if(Math.abs(dot(t,ax))>=a+b+gap-1e-5)return false;
  }return true;
}
function part(type,id,x,y,z,extra={}) {return {id,type,name:LIBRARY[type].name,size:[...LIBRARY[type].size],x,y,z,rotation:0,face:'floor',visible:true,locked:false,parent:null,verified:false,...extra};}
export function initialState(){return {schema:'ft412-control-layout',version:VERSION,units:'mm',box:{length:355,width:140,height:75,wall:3,offset:15,profileBase:0,split:177.5,bed:256,anchors:[75,280]},parts:[
  part('pi','pi',312,93,8,{rotation:90}),
  part('cooler','cooler',312,93,11,{rotation:90,parent:'pi'}),
  part('fan','fan',312,93,72,{face:'lid',parent:'pi'}),
  part('mks','mks',125,99,8,{rotation:180}),
  part('driver','driver-x',154,87,18,{parent:'mks',rotation:180,name:'TMC2209 · X'}),
  part('driver','driver-y',136,87,18,{parent:'mks',rotation:180,name:'TMC2209 · Y'}),
  part('lcd','lcd',3,88,39,{face:'front'}),
  part('switch','switch',3,22,38,{face:'front'}),
  part('mosfet','mosfet',211,88,8),part('fuse','fuse',237,30,8)
],ui:{selected:'pi',view:'top',grid:true,snap:1,ports:true,lid:false,robot:true},cutouts:[]};}
export function familyRoot(state,p){let n=p;const seen=new Set();while(n.parent&&!seen.has(n.id)){seen.add(n.id);const v=state.parts.find(x=>x.id===n.parent);if(!v)break;n=v;}return n.id;}
function intendedAssemblyOverlap(a,b){
  const pairs=[[a,b],[b,a]];
  return pairs.some(([board,child])=>child.parent===board.id&&((board.type==='pi'&&child.type==='cooler')||(board.type==='mks'&&child.type==='driver')));
}
export function descendants(state,id){const ids=new Set([id]);for(let i=0;i<state.parts.length;i++)for(const p of state.parts)if(ids.has(p.parent))ids.add(p.id);return state.parts.filter(p=>ids.has(p.id));}
export function movePart(state,id,delta,group=true){const p=state.parts.find(p=>p.id===id);if(!p||p.locked)return;for(const q of (group?descendants(state,id):[p])){q.x=round(q.x+delta[0]);q.y=round(q.y+delta[1]);if(q===p||q.face!=='lid')q.z=round(q.z+delta[2]);}}
export function rotatePart(state,id,deg){const p=state.parts.find(p=>p.id===id);if(!p||p.locked)return;const a=axes(p),normal=a[2],r=rad(deg);for(const q of descendants(state,id).filter(q=>q!==p)){
    const v=[q.x-p.x,q.y-p.y,q.z-p.z];const vr=add(add(mul(v,Math.cos(r)),mul(cross(normal,v),Math.sin(r))),mul(normal,dot(normal,v)*(1-Math.cos(r))));
    [q.x,q.y,q.z]=add([p.x,p.y,p.z],vr).map(round);
    q.rotation=(q.rotation+(q.face===p.face?deg:(p.face==='floor'&&q.face==='lid'?-deg:0))+360)%360;
  }p.rotation=(p.rotation+deg+360)%360;}
export function setBox(state,key,value){state.box[key]=value;if(key==='height'||key==='wall')for(const p of state.parts)if(p.face==='lid')p.z=state.box.height-state.box.wall;}
export function portBoxes(p){return (LIBRARY[p.type]?.ports||[]).map(port=>{
  const n=vector(p,port.n),a=point(p,port.at);const face=Math.abs(n[2])>.7?(n[2]>0?'lid':'floor'):Math.abs(n[0])>.7?(n[0]>0?'back':'front'):(n[1]>0?'outer':'inner');
  return {id:`${p.id}-${port.name}`,name:port.name,owner:p.id,origin:a,normal:n,face,w:port.w,h:port.h,space:port.space};
});}
export function apertures(state){const b=state.box,all=[];
  for(const p of state.parts.filter(p=>p.visible)){
    if(p.type==='lcd'&&p.face!=='floor'){const a=axes(p)[0],indices=['front','back'].includes(p.face)?[1,2]:p.face==='lid'?[0,1]:[0,2];all.push({owner:p.id,name:'Ventana pantalla',face:p.face,center:[p.x,p.y,p.z],size:p.aperture||LIBRARY.lcd.aperture,rotation:Math.atan2(a[indices[1]],a[indices[0]])*180/Math.PI,kind:'rect',draft:!p.verified});}
    if(p.type==='switch'&&p.face!=='floor')all.push({owner:p.id,name:'Interruptor',face:p.face,center:[p.x,p.y,p.z],size:[p.aperture||12.7,p.aperture||12.7],kind:'circle',draft:!p.verified});
    if(p.type==='fan'&&p.face!=='floor')all.push({owner:p.id,name:'Abertura ventilador',face:p.face,center:[p.x,p.y,p.face==='lid'?b.height:p.z],size:[p.aperture||32,p.aperture||32],kind:'circle',draft:!p.verified});
    for(const port of portBoxes(p)){
      const axis=port.face==='lid'||port.face==='floor'?2:port.face==='front'||port.face==='back'?0:1;
      const wall=['front','inner','floor'].includes(port.face)?0:axis===0?b.length:axis===1?b.width:b.height;
      const center=[...port.origin];const recess=(wall-port.origin[axis])/port.normal[axis];center[axis]=wall;
      all.push({owner:p.id,name:port.name,face:port.face,center,size:[port.w,port.h],kind:'rect',draft:true,recess:round(recess)});
    }
  }return [...all,...state.cutouts];}
export function validate(state){const b=state.box,issues=[];const ps=state.parts.filter(p=>p.visible);
  for(const p of ps){const bb=bounds(p),min=[b.wall,b.wall,b.wall],max=[b.length-b.wall,b.width-b.wall,b.height-b.wall];
    if(p.face==='front')min[0]=0;if(p.face==='back')max[0]=b.length;if(p.face==='inner')min[1]=0;if(p.face==='outer')max[1]=b.width;
    if(p.face==='lid')max[2]=b.height;
    if(bb.min.some((v,i)=>v<min[i]-.1)||bb.max.some((v,i)=>v>max[i]+.1))issues.push({severity:'error',ids:[p.id],text:`${p.name}: sobresale del espacio interior.`});
    if(p.type==='fan'&&(p.aperture||32)>=Math.min(p.size[0],p.size[1])-1)issues.push({severity:'error',ids:[p.id],text:'La abertura del ventilador no deja margen dentro de su marco.'});
    if(p.type==='lcd'&&(p.aperture||LIBRARY.lcd.aperture).some((n,i)=>n>=p.size[i]))issues.push({severity:'error',ids:[p.id],text:'La ventana de la pantalla supera su placa.'});
  }
  for(let i=0;i<ps.length;i++)for(let j=i+1;j<ps.length;j++)if(!intendedAssemblyOverlap(ps[i],ps[j])&&intersects(ps[i],ps[j]))issues.push({severity:'error',ids:[ps[i].id,ps[j].id],text:`Choque: ${ps[i].name} / ${ps[j].name}.`});
  if(b.length>b.bed-10){const a=b.split,c=b.length-a;if(Math.max(a,c)>b.bed-10||Math.min(a,c)<30)issues.push({severity:'error',ids:[],text:'La división deja una sección demasiado larga para la cama, incluyendo 10 mm de margen.'});
    for(const p of ps.filter(p=>!p.parent)){const bb=bounds(p);if(bb.min[0]<a-2&&bb.max[0]>a+2)issues.push({severity:'info',ids:[p.id],text:`${p.name}: cruza la unión entre secciones; revisar al diseñar la base.`});}}
  if(b.width>b.bed-10)issues.push({severity:'error',ids:[],text:'El ancho supera el espacio de impresión reservado.'});
  if(b.anchors.some(x=>x<10||x>Math.min(b.length,355)-10))issues.push({severity:'error',ids:[],text:'Un apoyo queda fuera del tramo disponible del perfil o demasiado cerca del extremo.'});
  for(const hole of apertures(state)){const faces=hole.face==='front'||hole.face==='back'?[b.width,b.height]:hole.face==='lid'?[b.length,b.width]:[b.length,b.height];const c=hole.face==='front'||hole.face==='back'?[hole.center[1],hole.center[2]]:hole.face==='lid'?[hole.center[0],hole.center[1]]:[hole.center[0],hole.center[2]];
    const co=Math.abs(Math.cos(rad(hole.rotation||0))),si=Math.abs(Math.sin(rad(hole.rotation||0))),span=[co*hole.size[0]+si*hole.size[1],si*hole.size[0]+co*hole.size[1]];
    if(c.some((v,i)=>v-span[i]/2<0||v+span[i]/2>faces[i]))issues.push({severity:'error',ids:hole.owner?[hole.owner]:[],text:`Abertura ${hole.name}: sale de su panel.`});
    if(hole.recess>15)issues.push({severity:'info',ids:[hole.owner],text:`${hole.name}: queda a ${hole.recess} mm de la pared; revisar acceso del enchufe.`});
  }
  const pending=ps.filter(p=>!p.verified);if(pending.length)issues.push({severity:'measure',ids:pending.map(p=>p.id),text:`${pending.length} piezas tienen medidas por comprobar.`});
  return issues;
}
function number(n,lo,hi,fallback){const v=Number(n);return Number.isFinite(v)&&v>=lo&&v<=hi?v:fallback;}
export function sanitize(value){if(!value||value.schema!=='ft412-control-layout'||value.version!==VERSION||!Array.isArray(value.parts))throw new Error('Este archivo no es un diseño FT412 compatible.');
  const d=initialState(),b=value.box||{};for(const [k,min,max] of [['length',80,600],['width',60,300],['height',30,250],['wall',1.2,10],['offset',0,60],['profileBase',-80,120],['split',20,580],['bed',100,500]])d.box[k]=number(b[k],min,max,d.box[k]);
  d.box.anchors=Array.isArray(b.anchors)&&b.anchors.length===2?b.anchors.map((v,i)=>number(v,0,600,d.box.anchors[i])):d.box.anchors;
  const ids=new Set();d.parts=value.parts.slice(0,60).map((v,i)=>{const type=Object.hasOwn(LIBRARY,v.type)?v.type:'custom';const id=String(v.id||`p-${i}`).replace(/[^a-zA-Z0-9_-]/g,'').slice(0,50);if(!id||ids.has(id))throw new Error('Hay identificadores de pieza repetidos.');ids.add(id);
    const p=part(type,id,number(v.x,-500,1000,50),number(v.y,-300,600,50),number(v.z,-300,600,8));p.name=String(v.name||p.name).slice(0,100);p.rotation=number(v.rotation,-3600,3600,0);p.face=['floor','front','back','inner','outer','lid'].includes(v.face)?v.face:'floor';p.visible=v.visible!==false;p.locked=v.locked===true;p.verified=v.verified===true;
    p.parent=typeof v.parent==='string'?v.parent.slice(0,50):null;p.size=p.size.map((n,j)=>number(v.size?.[j],.5,500,n));if(Array.isArray(v.aperture))p.aperture=v.aperture.slice(0,2).map(n=>number(n,1,200,40));else if(v.aperture)p.aperture=number(v.aperture,1,200,32);return p;});
  for(const p of d.parts){if(!ids.has(p.parent))p.parent=null;const seen=new Set([p.id]);let n=p;while(n.parent){if(seen.has(n.parent))throw new Error('El diseño contiene un grupo circular.');seen.add(n.parent);n=d.parts.find(p=>p.id===n.parent);}}
  d.cutouts=(Array.isArray(value.cutouts)?value.cutouts:[]).slice(0,60).filter(v=>['front','back','inner','outer','lid'].includes(v.face)).map((v,i)=>({id:`cut-${i}`,name:String(v.name||'Abertura libre').slice(0,70),face:v.face,center:[0,1,2].map(j=>number(v.center?.[j],-500,1000,0)),size:[0,1].map(j=>number(v.size?.[j],1,500,20)),kind:v.kind==='circle'?'circle':'rect',draft:true}));
  const u=value.ui||{};d.ui={...d.ui,selected:ids.has(u.selected)?u.selected:d.parts[0]?.id,view:['top','front','side','3d'].includes(u.view)?u.view:'top',grid:u.grid!==false,snap:number(u.snap,0,10,1),ports:u.ports!==false,lid:u.lid===true,robot:u.robot!==false};return d;
}
export function exportLayout(state){const d=clone(state);d.exportedAt=new Date().toISOString();d.fabricationReady=false;d.cadNote='Distribución editable. Contornos y aberturas son reservas para revisar antes de fabricar; no es un pinout.';d.apertureSchedule=apertures(state);d.issues=validate(state);return d;}
