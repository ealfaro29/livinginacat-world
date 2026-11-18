import {
  enclosurePanel, frontProfile, innerVentOpenings, insideRoofHeight, openingFits,
  panelCoordinates, panelPoint, rampAxes, rampMountHeight,
} from './enclosure.mjs';

export const VERSION = 2;
export const LAYOUT_VIEWS = ['top','front','side','inner','back','3d'];
export const DESIGN_FACES = ['floor','front','back','inner','outer','lid','ramp'];
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
  mks: {name:'MKS DLC32',short:'MKS DLC32',size:[90,70,20],color:'#296c68',measured:true,note:'El plano V2.1 sirve de referencia para los 90 × 70 mm. Confirmá las medidas y fijaciones en tu placa antes de fabricar.',holes:[[-41,-31],[-41,31],[41,-31],[41,31]],source:SOURCES.mks,
    ports:[{name:'USB-B',at:[-8,-35,6],n:[0,-1,0],w:13,h:13,space:35},{name:'Entrada 12 V',at:[-23,-35,6],n:[0,-1,0],w:11,h:12,space:25},{name:'Reserva salida de mazo',at:[-10,27,12],n:[0,0,1],w:58,h:12,space:20}]},
  driver: {name:'TMC2209 + disipador',short:'TMC2209',size:[15.24,20.32,16],color:'#b98846',measured:false,note:'Envolvente nominal; verificar altura del disipador y asiento en la MKS.'},
  lcd: {name:'Pantalla TS24-R V2.1',short:'Pantalla TS24-R',size:[80,50,15],color:'#477b97',measured:false,note:'Modelo confirmado en foto. 80 × 50 y ventana 56 × 42 son reservas: verificar medidas y agujeros.',aperture:[56,42]},
  mosfet: {name:'Adafruit 5648',short:'MOSFET 5648',size:[25.4,17.78,13],color:'#566f9b',measured:true,note:'Contorno nominal 25,4 × 17,78. Altura y espacio de cables por comprobar.',source:SOURCES.mosfet},
  switch: {name:'Interruptor NKK S301T',short:'Interruptor 12 V',size:[17,17,32],color:'#bb7745',measured:false,note:'Abertura propuesta Ø12,7. Confirmar cuerpo y terminales de tornillo reales.',aperture:12.7},
  fuse: {name:'Portafusible ATO + 3 A',short:'Portafusible',size:[34,22,26],color:'#817255',measured:false,note:'Reserva para FHAS101; incluir salida y curvas de ambos cables.'},
  clip: {name:'Clip para cables',short:'Clip',size:[14,16,10],color:'#bd8951',note:'Clip abierto. Ajustá su ancho al mazo que va a sujetar.'},
  custom:{name:'Pieza libre',short:'Pieza libre',size:[30,25,20],color:'#8b7198',measured:false,note:'Volumen libre: ajustá sus medidas.'},
};
export const clone = v => JSON.parse(JSON.stringify(v));
const rad = n => n*Math.PI/180;
const dot = (a,b) => a.reduce((s,x,i)=>s+x*b[i],0);
const cross = (a,b) => [a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]];
const add = (a,b) => a.map((x,i)=>x+b[i]);
const mul = (a,s) => a.map(x=>x*s);
export const round = n => Math.round(n*10)/10;

export function axes(p, box) {
  const c=Math.cos(rad(p.rotation)),s=Math.sin(rad(p.rotation));
  let u=[1,0,0],v=[0,1,0],w=[0,0,1];
  if(p.face==='front'){u=[0,1,0];v=[0,0,1];w=[1,0,0];}
  if(p.face==='back'){u=[0,-1,0];v=[0,0,1];w=[-1,0,0];}
  if(p.face==='outer'){u=[1,0,0];v=[0,0,1];w=[0,-1,0];}
  if(p.face==='inner'){u=[-1,0,0];v=[0,0,1];w=[0,1,0];}
  if(p.face==='lid'){u=[1,0,0];v=[0,-1,0];w=[0,0,-1];}
  if (p.face === 'ramp') [u,v,w] = rampAxes(box);
  return [add(mul(u,c),mul(v,s)),add(mul(u,-s),mul(v,c)),w];
}
export function point(p,q,box) {const a=axes(p,box);return [p.x,p.y,p.z].map((v,i)=>v+q.reduce((s,x,j)=>s+x*a[j][i],0));}
export function vector(p,q,box){const a=axes(p,box);return a[0].map((_,i)=>q.reduce((s,x,j)=>s+x*a[j][i],0));}
export function corners(p, box) {
  const [w,d,h] = p.size;
  return [-w/2,w/2].flatMap(x => [-d/2,d/2].flatMap(y => [0,h].map(z => point(p, [x,y,z], box))));
}
export function bounds(p, box) {
  const vertices = corners(p, box);
  return {
    min:[0,1,2].map(i => Math.min(...vertices.map(v => v[i]))),
    max:[0,1,2].map(i => Math.max(...vertices.map(v => v[i]))),
  };
}
export function obb(p,box){return {c:point(p,[0,0,p.size[2]/2],box),a:axes(p,box),h:p.size.map(n=>n/2)};}
export function intersects(p,q,gap=0,box) {
  const A=obb(p,box),B=obb(q,box),t=B.c.map((v,i)=>v-A.c[i]);
  for(const ax of [...A.a,...B.a,...A.a.flatMap(a=>B.a.map(b=>cross(a,b)))]){
    if(dot(ax,ax)<1e-9)continue;
    const a=A.a.reduce((s,u,i)=>s+Math.abs(dot(ax,u))*A.h[i],0);
    const b=B.a.reduce((s,u,i)=>s+Math.abs(dot(ax,u))*B.h[i],0);
    if(Math.abs(dot(t,ax))>=a+b+gap-1e-5)return false;
  }return true;
}
function part(type,id,x,y,z,extra={}) {return {id,type,name:LIBRARY[type].name,size:[...LIBRARY[type].size],x,y,z,rotation:0,face:'floor',visible:true,locked:false,parent:null,verified:false,...extra};}
function previousLayout(){return {schema:'ft412-control-layout',version:1,units:'mm',box:{length:355,width:140,height:75,wall:3,offset:15,profileBase:0,split:177.5,bed:256,anchors:[75,280]},parts:[
  part('pi','pi',312,93,8,{rotation:90}),
  part('cooler','cooler',312,93,11,{rotation:90,parent:'pi'}),
  part('fan','fan',312,93,72,{face:'lid',parent:'pi'}),
  part('mks','mks',125,99,8,{rotation:180,name:'MKS DLC32 V2.1'}),
  part('driver','driver-x',154,87,18,{parent:'mks',rotation:180,name:'TMC2209 · X'}),
  part('driver','driver-y',136,87,18,{parent:'mks',rotation:180,name:'TMC2209 · Y'}),
  part('lcd','lcd',3,88,39,{face:'front'}),
  part('switch','switch',3,22,38,{face:'front'}),
  part('mosfet','mosfet',211,88,8),part('fuse','fuse',237,30,8)
],ui:{selected:'pi',view:'top',grid:true,snap:1,ports:true,lid:false,robot:true},cutouts:[]};}

export function initialState() {
  const box = {
    length:280, width:120, height:90, wall:3, offset:15, profileBase:0,
    frontRun:60, frontAngle:45, screenZone:55,
    split:135, bed:256, anchors:[78,231], innerVent:true, automaticPortOpenings:false,
    mountSide:'left', floorMounts:true,
  };
  const front = frontProfile(box);
  const screenX = box.screenZone / 2 + box.wall * front.sin;
  return {
    schema:'ft412-control-layout', version:VERSION, units:'mm', box,
    parts:[
      part('lcd','lcd',screenX,60,rampMountHeight(box,screenX),{face:'ramp'}),
      part('pi','pi',96,62,8,{rotation:90}),
      part('cooler','cooler',96,62,11,{rotation:90,parent:'pi'}),
      part('fan','fan',96,62,29,{parent:'pi'}),
      part('mks','mks',191,77,8,{rotation:180,name:'MKS DLC32 V2.2'}),
      part('driver','driver-x',220,65,18,{parent:'mks',rotation:180,name:'TMC2209 · X'}),
      part('driver','driver-y',202,65,18,{parent:'mks',rotation:180,name:'TMC2209 · Y'}),
      part('mosfet','mosfet',159,19,8),
      part('fuse','fuse',219,21,8,{size:[48,28,26]}),
      part('switch','switch',277,84,35,{face:'back'}),
      part('clip','clip-inner-1',78,3,53,{face:'inner',name:'Clip · pared del perfil 1'}),
      part('clip','clip-inner-2',231,3,53,{face:'inner',name:'Clip · pared del perfil 2'}),
      part('clip','clip-outer-1',108,117,52,{face:'outer',name:'Clip · pared exterior 1'}),
      part('clip','clip-outer-2',216,117,52,{face:'outer',name:'Clip · pared exterior 2'}),
      part('clip','clip-lid-1',110,25,87,{face:'lid',name:'Clip · tapa 1'}),
      part('clip','clip-lid-2',199,27,87,{face:'lid',name:'Clip · tapa 2'}),
    ],
    ui:{selected:'lcd',view:'3d',grid:true,snap:1,ports:false,lid:true,robot:true,electronics:true},
    cutouts:[{
      id:'rear-power',name:'Paso de corriente',face:'back',center:[box.length,30,23],
      size:[16,12],kind:'rect',draft:true,
    }],
  };
}

export function restoreLayout(value, {upgradeStock = false} = {}) {
  const saved = sanitize(value);
  if (!upgradeStock || value.version !== 1) return saved;
  const stock = sanitize(previousLayout());
  const footprint = layout => JSON.stringify([layout.box, layout.parts, layout.cutouts]);
  return footprint(saved) === footprint(stock) ? initialState() : saved;
}
export function familyRoot(state,p){let n=p;const seen=new Set();while(n.parent&&!seen.has(n.id)){seen.add(n.id);const v=state.parts.find(x=>x.id===n.parent);if(!v)break;n=v;}return n.id;}
function intendedAssemblyOverlap(a,b){
  const pairs=[[a,b],[b,a]];
  return pairs.some(([board,child])=>child.parent===board.id&&((board.type==='pi'&&child.type==='cooler')||(board.type==='mks'&&child.type==='driver')));
}
export function descendants(state,id){const ids=new Set([id]);for(let i=0;i<state.parts.length;i++)for(const p of state.parts)if(ids.has(p.parent))ids.add(p.id);return state.parts.filter(p=>ids.has(p.id));}
export function movePart(state, id, delta, group = true) {
  const part = state.parts.find(p => p.id === id);
  if (!part || part.locked) return;
  for (const child of group ? descendants(state, id) : [part]) {
    child.x = round(child.x + delta[0]);
    child.y = round(child.y + delta[1]);
    if (child.face === 'ramp') {
      child.z = rampMountHeight(state.box, child.x);
    } else if (child === part || child.face !== 'lid') {
      child.z = round(child.z + delta[2]);
    }
    if (child.type === 'clip') alignClip(state.box, child);
  }
}
export function rotatePart(state,id,deg){const p=state.parts.find(p=>p.id===id);if(!p||p.locked)return;const a=axes(p,state.box),normal=a[2],r=rad(deg);for(const q of descendants(state,id).filter(q=>q!==p)){
    const v=[q.x-p.x,q.y-p.y,q.z-p.z];const vr=add(add(mul(v,Math.cos(r)),mul(cross(normal,v),Math.sin(r))),mul(normal,dot(normal,v)*(1-Math.cos(r))));
    [q.x,q.y,q.z]=add([p.x,p.y,p.z],vr).map(round);
    q.rotation=(q.rotation+(q.face===p.face?deg:(p.face==='floor'&&q.face==='lid'?-deg:0))+360)%360;
  }p.rotation=(p.rotation+deg+360)%360;}
export function setBox(state, key, value) {
  const box = state.box;
  const prev = box[key];
  const front = frontProfile(box);
  box[key] = value;
  const next = frontProfile(box);
  for (const part of state.parts) {
    if (part.face === 'lid' && (key === 'height' || key === 'wall')) part.z = box.height - box.wall;
    if (part.face === 'back' && key === 'length') part.x += value - prev;
    if (part.face === 'outer' && key === 'width') part.y += value - prev;
    if (key === 'wall') {
      if (part.face === 'back') part.x -= value - prev;
      if (part.face === 'front') part.x += value - prev;
      if (part.face === 'outer') part.y -= value - prev;
      if (part.face === 'inner') part.y += value - prev;
    }
    if (part.type === 'clip') alignClip(box, part);
    if (part.face !== 'ramp' || !['height','wall','frontAngle','frontRun'].includes(key)) continue;
    if (key === 'frontRun' && next.enabled) {
      const fraction = front.enabled ? (part.x - box.wall * front.sin) / front.run : 0.5;
      part.x = round(next.run * fraction + box.wall * next.sin);
    }
    part.z = rampMountHeight(box, part.x);
  }
}

function alignClip(box, part) {
  if (part.face === 'inner') part.y = box.wall;
  if (part.face === 'outer') part.y = box.width - box.wall;
  if (part.face === 'lid') part.z = box.height - box.wall;
}

export function setMountingFace(state, part, face) {
  const box = state.box;
  const front = frontProfile(box);
  part.face = face;
  part.rotation = 0;
  switch (face) {
    case 'ramp':
      part.x = front.run / 2 + box.wall * front.sin;
      part.z = rampMountHeight(box, part.x);
      break;
    case 'lid': part.z = box.height - box.wall; break;
    case 'front': part.x = box.wall; break;
    case 'back': part.x = box.length - box.wall; break;
    case 'outer': part.y = box.width - box.wall; break;
    case 'inner': part.y = box.wall; break;
    default: part.z = 8;
  }
}

export function portBoxes(p, box){return (LIBRARY[p.type]?.ports||[]).map(port=>{
  const n=vector(p,port.n,box),a=point(p,port.at,box);const face=Math.abs(n[2])>.7?(n[2]>0?'lid':'floor'):Math.abs(n[0])>.7?(n[0]>0?'back':'front'):(n[1]>0?'outer':'inner');
  return {id:`${p.id}-${port.name}`,name:port.name,owner:p.id,origin:a,normal:n,face,w:port.w,h:port.h,space:port.space};
});}
function onPanel(panel, center) {
  return panel ? panelPoint(panel, panelCoordinates(panel, center)) : center;
}

function partOpening(box, part, name, face, size, kind) {
  const panel = enclosurePanel(box, face);
  const widthAxis = axes(part, box)[0];
  const rotation = panel && kind === 'rect'
    ? Math.atan2(dot(widthAxis, panel.axes[1]), dot(widthAxis, panel.axes[0])) * 180 / Math.PI
    : 0;
  return {
    owner:part.id, name, face, size, kind, rotation, draft:!part.verified,
    center:onPanel(panel, [part.x,part.y,part.z]),
  };
}

const pcbMounts = {
  pi: {holes:LIBRARY.pi.holes, outside:7.6, bore:2.7},
  mks: {holes:LIBRARY.mks.holes, outside:9, bore:3.2},
  mosfet: {holes:[[10.16,-6.35],[10.16,6.35]], outside:6.4, bore:2.5},
};

export function mountingBases(state) {
  if (!state.box.floorMounts) return [];
  const bases = [];
  for (const part of state.parts.filter(p => p.visible && p.face === 'floor')) {
    const pattern = pcbMounts[part.type];
    if (!pattern && part.type !== 'fuse') continue;
    const height = part.z - state.box.wall;
    if (height <= 0) continue;
    const mountingPlane = point(part, [0,0,-height], state.box);
    const saddle = part.type === 'fuse' ? [part.size[0] + 15, part.size[1] + 5] : null;
    const holes = pattern?.holes ?? [[-part.size[0]/2-4,0],[part.size[0]/2+4,0]];
    const seats = holes.map(([u,v]) => ({
      center:point(part,[u,v,-height],state.box),
      outsideDiameterMM:pattern?.outside ?? 7,
      boreDiameterMM:pattern?.bore ?? 3.2,
    }));
    bases.push({
      owner:part.id, kind:saddle ? 'cradle' : 'standoffs', rotation:part.rotation,
      center:mountingPlane, cradleSizeMM:saddle, heightMM:height,
      seats, draft:true,
    });
  }
  return bases;
}

export function apertures(state, {ventilation = true} = {}) {
  const box = state.box;
  const openings = [];
  for (const part of state.parts.filter(p => p.visible)) {
    if (part.type === 'lcd' && part.face !== 'floor') {
      openings.push(partOpening(box, part, 'Ventana pantalla', part.face, part.aperture ?? LIBRARY.lcd.aperture, 'rect'));
    }
    if (part.type === 'switch' && part.face !== 'floor') {
      const diameter = part.aperture ?? LIBRARY.switch.aperture;
      openings.push(partOpening(box, part, 'Interruptor', part.face, [diameter,diameter], 'circle'));
    }
    if (part.type === 'fan') {
      const diameter = part.aperture ?? LIBRARY.fan.aperture;
      const face = part.face === 'floor' ? 'lid' : part.face;
      openings.push(partOpening(box, part, 'Abertura ventilador', face, [diameter,diameter], 'circle'));
    }
    if (!box.automaticPortOpenings) continue;
    for (const port of portBoxes(part, box)) {
      const panel = enclosurePanel(box, port.face);
      const axis = panel.axes[2];
      const distance = dot(panel.origin.map((value, i) => value - port.origin[i]), axis) / dot(port.normal, axis);
      const center = port.origin.map((value, i) => value + port.normal[i] * distance);
      openings.push({
        owner:part.id, name:port.name, face:port.face, center,
        size:[port.w,port.h], kind:'rect', draft:true, recess:round(distance),
      });
    }
  }
  for (const opening of state.cutouts) {
    const panel = enclosurePanel(box, opening.face);
    openings.push({...opening, center:onPanel(panel, opening.center)});
  }
  if (ventilation) {
    const clipBases = state.parts.filter(part => part.visible && part.type === 'clip' && part.face === 'inner')
      .map(part => partOpening(box, part, '', 'inner', part.size.slice(0,2), 'rect'));
    openings.push(...innerVentOpenings(box, clipBases));
  }
  return openings;
}

export function validate(state) {
  const box = state.box;
  const front = frontProfile(box);
  const issues = [];
  const visibleParts = state.parts.filter(part => part.visible);
  const issue = (text, ids = [], severity = 'error') => issues.push({text, ids, severity});
  if (!front.valid) issue('Ajustá la altura, el largo o el ángulo del frente inclinado.');
  for (const part of visibleParts) {
    const min = [box.wall,box.wall,box.wall];
    const max = [box.length-box.wall,box.width-box.wall,box.height-box.wall];
    if (part.face === 'front') min[0] = 0;
    if (part.face === 'back') max[0] = box.length;
    if (part.face === 'inner') min[1] = 0;
    if (part.face === 'outer') max[1] = box.width;
    if (part.face === 'lid') max[2] = box.height;
    const vertices = corners(part, box);
    const crossesWalls = vertices.some(vertex => vertex.some((n, i) => n < min[i] - 0.1 || n > max[i] + 0.1));
    const crossesRamp = front.valid && front.enabled && vertices.some(([x,,z]) => x < front.run && z > insideRoofHeight(box, x) + 0.1);
    if (crossesWalls || crossesRamp) issue(`${part.name}: sobresale del espacio interior.`, [part.id]);
    if (part.face === 'ramp') {
      const base = partOpening(box, part, '', 'ramp', part.size.slice(0,2), 'rect');
      if (!openingFits(enclosurePanel(box, 'ramp'), base)) issue(`${part.name}: la placa sale del panel inclinado.`, [part.id]);
    }
    if (part.type === 'fan' && (part.aperture ?? LIBRARY.fan.aperture) >= Math.min(...part.size.slice(0,2)) - 1) {
      issue('La abertura del ventilador no deja margen dentro de su marco.', [part.id]);
    }
    if (part.type === 'lcd' && (part.aperture ?? LIBRARY.lcd.aperture).some((n,i) => n >= part.size[i])) {
      issue('La ventana de la pantalla supera su placa.', [part.id]);
    }
  }
  visibleParts.forEach((part, i) => {
    for (const other of visibleParts.slice(i + 1)) {
      if (!intendedAssemblyOverlap(part, other) && intersects(part, other, 0, box)) {
        issue(`Choque: ${part.name} / ${other.name}.`, [part.id,other.id]);
      }
    }
  });
  if (box.length > box.bed - 10) {
    const lengths = [box.split, box.length - box.split];
    if (Math.max(...lengths) > box.bed - 10 || Math.min(...lengths) < 30) {
      issue('La división deja una sección fuera de los límites de impresión.');
    }
    for (const part of visibleParts.filter(p => !p.parent)) {
      const {min,max} = bounds(part, box);
      if (min[0] < box.split - 2 && max[0] > box.split + 2) {
        issue(`${part.name}: cruza la unión entre secciones.`, [part.id], 'info');
      }
    }
  }
  if (box.width > box.bed - 10) issue('El ancho supera el espacio de impresión reservado.');
  if (box.anchors.some(x => x < 10 || x > Math.min(box.length, 355) - 10)) {
    issue('Un apoyo queda fuera del tramo disponible del perfil o demasiado cerca del extremo.');
  }
  for (const opening of apertures(state, {ventilation:false})) {
    const ids = opening.owner ? [opening.owner] : [];
    if (!openingFits(enclosurePanel(box, opening.face), opening)) issue(`Abertura ${opening.name}: sale de su panel.`, ids);
    if (opening.recess > 15) issue(`${opening.name}: queda a ${opening.recess} mm de la pared.`, ids, 'info');
  }
  const pending = visibleParts.filter(part => !part.verified);
  if (pending.length) issue(`${pending.length} piezas tienen medidas por comprobar.`, pending.map(part => part.id), 'measure');
  return issues;
}
function number(n, lo, hi, fallback) {
  const value = Number(n);
  return Number.isFinite(value) && value >= lo && value <= hi ? value : fallback;
}

export function sanitize(value) {
  if (!value || value.schema !== 'ft412-control-layout' || ![1, VERSION].includes(value.version) || !Array.isArray(value.parts)) {
    throw new Error('Este archivo no es un diseño FT412 compatible.');
  }
  const legacy = value.version === 1;
  const draft = legacy ? previousLayout() : initialState();
  const box = draft.box;
  const imported = value.box ?? {};
  const fields = [
    ['length',80,600],['width',60,300],['height',30,250],['wall',1.2,10],['offset',0,60],
    ['profileBase',-80,120],['split',20,580],['bed',100,500],
  ];
  for (const [key,min,max] of fields) box[key] = number(imported[key], min, max, box[key]);
  box.frontRun = legacy ? 0 : number(imported.frontRun, 0, 300, box.frontRun);
  box.frontAngle = legacy ? 0 : number(imported.frontAngle, 0, 70, box.frontAngle);
  box.screenZone = legacy ? 0 : number(imported.screenZone, 0, 300, box.screenZone);
  box.innerVent = !legacy && imported.innerVent !== false;
  box.automaticPortOpenings = legacy || imported.automaticPortOpenings === true;
  box.mountSide = legacy || imported.mountSide === 'right' ? 'right' : 'left';
  box.floorMounts = !legacy && imported.floorMounts !== false;
  if (Array.isArray(imported.anchors) && imported.anchors.length === 2) {
    box.anchors = imported.anchors.map((n, i) => number(n, 0, 600, box.anchors[i]));
  }
  const ids = new Set();
  draft.parts = value.parts.slice(0,60).map((entry, i) => {
    const type = Object.hasOwn(LIBRARY, entry.type) ? entry.type : 'custom';
    const id = String(entry.id || `p-${i}`).replace(/[^a-zA-Z0-9_-]/g, '').slice(0,50);
    if (!id || ids.has(id)) throw new Error('Hay identificadores de pieza repetidos.');
    ids.add(id);
    const item = part(type, id, number(entry.x,-500,1000,50), number(entry.y,-300,600,50), number(entry.z,-300,600,8));
    item.name = String(entry.name || item.name).slice(0,100);
    item.rotation = number(entry.rotation,-3600,3600,0);
    item.face = DESIGN_FACES.includes(entry.face) ? entry.face : 'floor';
    item.visible = entry.visible !== false;
    item.locked = entry.locked === true;
    item.verified = entry.verified === true;
    item.parent = typeof entry.parent === 'string' ? entry.parent.slice(0,50) : null;
    item.size = item.size.map((n, j) => number(entry.size?.[j], 0.5, 500, n));
    if (type === 'lcd' && Array.isArray(entry.aperture)) {
      item.aperture = LIBRARY.lcd.aperture.map((n, j) => number(entry.aperture[j], 1, 200, n));
    } else if (['fan','switch'].includes(type) && typeof entry.aperture === 'number') {
      item.aperture = number(entry.aperture, 1, 200, LIBRARY[type].aperture);
    }
    if (item.face === 'ramp') item.z = rampMountHeight(box, item.x);
    return item;
  });
  for (const item of draft.parts) {
    if (!ids.has(item.parent)) item.parent = null;
    const seen = new Set([item.id]);
    let next = draft.parts.find(p => p.id === item.parent);
    while (next) {
      if (seen.has(next.id)) throw new Error('El diseño contiene un grupo circular.');
      seen.add(next.id);
      next = draft.parts.find(p => p.id === next.parent);
    }
  }
  const cutouts = Array.isArray(value.cutouts) ? value.cutouts : [];
  draft.cutouts = cutouts.slice(0,60)
    .filter(opening => DESIGN_FACES.includes(opening.face) && opening.face !== 'floor')
    .map((opening, i) => ({
      id:String(opening.id || `cut-${i}`).slice(0,60),
      name:String(opening.name || 'Abertura libre').slice(0,70),
      face:opening.face,
      center:[0,1,2].map(j => number(opening.center?.[j], -500, 1000, 0)),
      size:[0,1].map(j => number(opening.size?.[j], 1, 500, 20)),
      kind:opening.kind === 'circle' ? 'circle' : 'rect', draft:true,
    }));
  const ui = value.ui ?? {};
  draft.ui = {
    ...draft.ui, selected:ids.has(ui.selected) ? ui.selected : draft.parts[0]?.id,
    view:LAYOUT_VIEWS.includes(ui.view) ? ui.view : 'top',
    grid:ui.grid !== false, snap:number(ui.snap,0,10,1), ports:ui.ports === true,
    lid:ui.lid === true, robot:ui.robot !== false, electronics:ui.electronics !== false,
  };
  draft.version = VERSION;
  return draft;
}

export function exportLayout(state) {
  const draft = clone(state);
  const front = frontProfile(state.box);
  draft.exportedAt = new Date().toISOString();
  draft.fabricationReady = false;
  draft.cadNote = 'Distribución editable. Verificar las medidas, los cables y las fijaciones antes de fabricar.';
  draft.frontDimensions = {
    lipMM:round(front.frontHeight), projectedRunMM:round(front.run),
    angleDegrees:front.angle, rampSurfaceLengthMM:round(front.surfaceLength),
    screenZoneMM:state.box.screenZone,
  };
  draft.apertureSchedule = apertures(state);
  draft.floorBases = mountingBases(state);
  draft.issues = validate(state);
  return draft;
}
