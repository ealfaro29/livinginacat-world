import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import {
  LIBRARY, VERSION, clone, initialState, restoreLayout, point, axes, bounds, validate, movePart,
  rotatePart, setBox, setMountingFace, apertures, portBoxes, mountingBases, sanitize, exportLayout, round, descendants,
} from './model.mjs';
import {enclosurePanel, frontProfile, openingFits, openingOutline, panelPoint, sideOutline} from './enclosure.mjs';

const $=id=>document.getElementById(id), NS='http://www.w3.org/2000/svg';
const embedded=JSON.parse($('saved-layout').textContent||'null');
const ownerPreset = new URLSearchParams(location.search).get('boceto') === '280';
const documentId = embedded?.documentId || (ownerPreset ? 'boceto-280' : 'default');
const storageKey = `ft412-control-layout-v1-${documentId}`;
let state=initialState(),history=[],future=[],svgMap=null,drag=null,toastTimer;
try {
  const saved = localStorage.getItem(storageKey);
  if (saved) {
    state = restoreLayout(JSON.parse(saved), {upgradeStock:!embedded});
  } else if (embedded) {
    state = sanitize(embedded);
  }
} catch {
  if (embedded) {
    try { state = sanitize(embedded); } catch {}
  }
}
let selected=()=>state.parts.find(p=>p.id===state.ui.selected),groupMoves=()=>$('move-group').checked;
const boxFields = ['length','width','height','wall','frontRun','frontAngle','offset','split','bed','profileBase'];
function toast(t){$('toast').textContent=t;$('toast').hidden=false;clearTimeout(toastTimer);toastTimer=setTimeout(()=>$('toast').hidden=true,3200);}
function remember(){history.push(clone(state));if(history.length>70)history.shift();future=[];}
function save(){try{localStorage.setItem(storageKey,JSON.stringify(state));$('save-status').textContent='Guardado en este navegador';}catch{$('save-status').textContent='Usá Guardar HTML o Exportar JSON para conservar el diseño';}}
function commit(fn){remember();fn();save();render();}
function el(tag,attrs={},text){const e=document.createElementNS(NS,tag);for(const[k,v]of Object.entries(attrs))e.setAttribute(k,v);if(text!==undefined)e.textContent=text;return e;}
function html(tag,cls,text){const e=document.createElement(tag);if(cls)e.className=cls;if(text!==undefined)e.textContent=text;return e;}
function num(id,value){if(document.activeElement!==$(id))$(id).value=round(value);}
function sizeText(p){return p.size.map(round).join(' × ')+' mm';}
function downloads(name,text,type='application/json'){const url=URL.createObjectURL(new Blob([text],{type})),a=document.createElement('a');a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),1500);}
const endView = view => view === 'front' || view === 'back';
const sideView = view => view === 'side' || view === 'inner';
const leftMount = () => state.box.mountSide === 'left';
const flipEnd = view => (leftMount() && view === 'front') || (!leftMount() && view === 'back');
const plotY = y => leftMount() ? -y : y;
const endX = (y, view) => flipEnd(view) ? state.box.width-y : y;
const drawnParts = () => state.parts.filter(part => part.visible && (state.ui.electronics !== false || part.type === 'clip'));

function project([x, y, z], view = state.ui.view) {
  if (endView(view)) return [endX(y,view), -z];
  if (sideView(view)) return [x, -z];
  return [x, plotY(y)];
}
function inclinedDistance(part, heightDelta) {
  const {slope} = frontProfile(state.box);
  return part.face === 'ramp' && slope > 0 ? heightDelta / slope : 0;
}
function unproject([u, v], part) {
  if (endView(state.ui.view)) return [part.x + inclinedDistance(part, -v - part.z), endX(u,state.ui.view), -v];
  if (sideView(state.ui.view)) return [u, part.y, -v];
  return [u, plotY(v), part.z];
}

function renderList(){const list=$('parts-list');list.replaceChildren();for(const p of state.parts){const row=html('div',`part-row${p.parent?' part-child':''}${p.id===state.ui.selected?' selected':''}`);row.tabIndex=0;row.setAttribute('role','button');row.setAttribute('aria-label',`Seleccionar ${p.name}`);row.dataset.part=p.id;const eye=document.createElement('input');eye.type='checkbox';eye.checked=p.visible;eye.setAttribute('aria-label',`Mostrar ${p.name}`);eye.addEventListener('click',e=>e.stopPropagation());eye.addEventListener('change',()=>commit(()=>p.visible=eye.checked));const sw=html('span','part-swatch');sw.style.background=LIBRARY[p.type].color;const text=html('span','part-text');text.append(html('strong','',p.name),html('small','',sizeText(p)));row.append(eye,sw,text);if(!p.verified)row.append(html('span','measure-dot','·'));if(p.locked)row.append(html('span','','⊙'));row.onclick=()=>{state.ui.selected=p.id;render();};row.onkeydown=e=>{if(e.key==='Enter'){state.ui.selected=p.id;render();}};list.append(row);}}
function renderInspector(){const p=selected();$('inspector').hidden=!p;$('inspector-empty').hidden=!!p;if(!p)return;const def=LIBRARY[p.type];$('part-title').textContent=p.name;$('part-dimensions').textContent=sizeText(p);$('selected-badge').classList.toggle('ok',p.verified);$('part-name').value=p.name;$('part-face').value=p.face;for(const key of ['x','y','z','rotation'])num(`part-${key}`,p[key]);['w','d','h'].forEach((key,i)=>num(`part-${key}`,p.size[i]));$('part-locked').checked=p.locked;$('part-verified').checked=p.verified;$('measure-note').textContent=def.note;$('measure-note').classList.toggle('verified',p.verified);$('part-source').hidden=!def.source;if(def.source)$('part-source').href=def.source;
  $('part-face').querySelector('[value="ramp"]').disabled = !frontProfile(state.box).enabled;
  $('part-z').disabled = p.face === 'ramp';
  $('part-z').title = p.face === 'ramp' ? 'La altura sigue el plano inclinado.' : '';
  const parent=$('part-parent');parent.replaceChildren(new Option('Independiente',''));const desc=new Set(descendants(state,p.id).map(p=>p.id));for(const q of state.parts)if(!desc.has(q.id))parent.add(new Option(q.name,q.id));parent.value=p.parent||'';
  const fields=$('aperture-fields');fields.replaceChildren();if(['lcd','fan','switch'].includes(p.type)){const label=html('label','field',p.type==='lcd'?'Ventana visible · ancho × alto':'Abertura · diámetro mm');const vals=p.aperture||def.aperture;for(const [i,value]of (Array.isArray(vals)?vals:[vals]).entries()){const input=document.createElement('input');input.type='number';input.min='1';input.max='200';input.step='.5';input.value=value;input.setAttribute('aria-label',p.type==='lcd'?`Ventana pantalla ${i===0?'ancho':'alto'}`:'Diámetro abertura');input.onchange=()=>commit(()=>{if(Array.isArray(vals)){const n=[...vals];n[i]=Math.max(1,Number(input.value)||value);p.aperture=n;}else p.aperture=Math.max(1,Number(input.value)||value);});label.append(input);}fields.append(label);}
}
function renderChecks(){const issues=validate(state),errors=issues.filter(x=>x.severity==='error');$('checks-count').textContent=errors.length?`${errors.length} problemas de espacio o geometría`:'La distribución cabe en la caja';const list=$('checks-list');list.replaceChildren();for(const issue of issues){const row=html('div',`check-issue ${issue.severity}`);row.append(html('span','',issue.severity==='error'?'!':issue.severity==='measure'?'◌':'↗'),html('span','',issue.text));row.onclick=()=>{if(issue.ids[0]){state.ui.selected=issue.ids[0];render();}};list.append(row);}if(!issues.length)list.append(html('div','check-issue','La distribución sigue pendiente de verificación física y térmica.'));return new Set(errors.flatMap(x=>x.ids));}

function drawDiagram() {
  const root = $('diagram');
  root.replaceChildren();
  const b = state.box;
  const view = state.ui.view;
  const front = frontProfile(b);
  const rampVisible = front.enabled && front.valid;
  const vb = endView(view) ? [-b.offset-43,-b.height-22,b.width+2*(b.offset+43),b.height+53]
    : sideView(view) ? [-28,-b.height-22,b.length+56,b.height+55]
    : [-34,leftMount() ? -b.width-32 : -b.offset-37,Math.max(355,b.length)+64,b.width+b.offset+82];
  const s = el('svg', {viewBox:vb.join(' '),role:'img','aria-label':'Distribución del módulo'});
  svgMap = {svg:s,vb};
  const add=(tag,attrs,text)=>{const e=el(tag,attrs,text);s.append(e);return e;};
  if(view==='top'){
    const planRect = (x,y,width,height,attrs) =>
      add('rect',{x,y:Math.min(plotY(y),plotY(y+height)),width,height,...attrs});
    const labelSide = leftMount() ? -1 : 1;
    planRect(0,-b.offset-20,355,20,{rx:1,fill:'#c8d1ca',stroke:'#88998d','stroke-width':.6});
    for(const y of [-b.offset-16,-b.offset-4])add('line',{x1:0,y1:plotY(y),x2:355,y2:plotY(y),stroke:'#9aa99e','stroke-width':1});
    add('text',{x:177.5,y:plotY(-b.offset-29),'text-anchor':'middle',class:'diagram-title'},
      leftMount() ? 'PERFIL IZQUIERDO · HACIA LA MÁQUINA' : 'PERFIL DERECHO · HACIA LA MÁQUINA');
    for(const x of b.anchors)planRect(x-6,-b.offset,12,b.offset+b.wall,{fill:'#bc9858',stroke:'#977b42','stroke-width':.5});
    planRect(0,0,b.length,b.width,{rx:3,fill:'#e9efe4',stroke:'#79927c','stroke-width':.8});
    if (rampVisible) {
      planRect(0,0,front.run,b.width,{fill:'#d4e6df'});
      add('line', {x1:front.run,y1:0,x2:front.run,y2:plotY(b.width),stroke:'#427c6a','stroke-width':.8});
      add('text', {x:front.run/2,y:plotY(b.width)+(leftMount()?-5:8),'text-anchor':'middle',class:'diagram-dim'}, `${round(front.run)} mm · ${front.angle}°`);
    }
    if(state.ui.grid)for(let x=10;x<b.length;x+=10)for(let y=10;y<b.width;y+=10)add('circle',{cx:x,cy:plotY(y),r:.32,fill:'#becfba'});
    planRect(b.wall,b.wall,b.length-2*b.wall,b.width-2*b.wall,{rx:1,fill:'none',stroke:'#acc0a6','stroke-width':.5});
    if(b.length>b.bed-10){add('line',{x1:b.split,y1:0,x2:b.split,y2:plotY(b.width),stroke:'#b99554','stroke-width':.55,'stroke-dasharray':'2.5 2'});add('text',{x:b.split+2,y:plotY(b.width)+labelSide*7,class:'diagram-dim'},'UNIÓN');}
    add('text',{x:-8,y:plotY(b.width/2),transform:`rotate(-90 -8 ${plotY(b.width/2)})`,'text-anchor':'middle',class:'diagram-title'},'FRENTE / PANTALLA');
    add('text',{x:b.length/2,y:plotY(b.width)+labelSide*20,'text-anchor':'middle',class:'diagram-dim'},`${round(b.length)} mm · frente → atrás`);
    add('line',{x1:0,y1:plotY(b.width)+labelSide*13,x2:b.length,y2:plotY(b.width)+labelSide*13,stroke:'#859f80','stroke-width':.4});
  }else{
    const width = endView(view) ? b.width : b.length;
    if (endView(view)) {
      add('rect', {x:0,y:-b.height,width,height:b.height,rx:2,fill:'#e9efe4',stroke:'#789079','stroke-width':.8});
      const profileX = flipEnd(view) ? width + b.offset : -b.offset-20;
      add('rect', {x:profileX,y:-b.profileBase-40,width:20,height:40,rx:1,fill:'#c8d1ca',stroke:'#88998d','stroke-width':.6});
      add('text', {x:profileX+10,y:-b.profileBase-46,'text-anchor':'middle',class:'diagram-part-small'}, 'Perfil');
      if (view === 'front' && rampVisible) {
        add('rect', {x:0,y:-b.height,width,height:front.rise,fill:'#d4e6df'});
        add('line', {x1:0,y1:-front.frontHeight,x2:width,y2:-front.frontHeight,stroke:'#709584','stroke-width':.6});
      }
    } else {
      add('polygon', {points:sideOutline(b).map(([x,z]) => [x,-z].join(',')).join(' '),fill:'#e9efe4',stroke:'#789079','stroke-width':.8});
      if (rampVisible) {
        add('line', {x1:0,y1:-front.frontHeight,x2:front.run,y2:-b.height,stroke:'#327b64','stroke-width':1});
        add('text', {x:front.run+4,y:-b.height+11,class:'diagram-dim'}, `${front.angle}° / ${round(front.run)} mm`);
        add('text', {x:-4,y:-front.frontHeight/2,'text-anchor':'end',class:'diagram-dim'}, round(front.frontHeight)+' mm');
      }
      if (b.length > b.bed - 10) add('line',{x1:b.split,y1:-b.height,x2:b.split,y2:0,stroke:'#b99554','stroke-width':.5,'stroke-dasharray':'2 2'});
    }
    add('text',{x:width/2,y:14,'text-anchor':'middle',class:'diagram-dim'},`${round(width)} mm`);add('text',{x:-7,y:-b.height/2,transform:`rotate(-90 -7 ${-b.height/2})`,'text-anchor':'middle',class:'diagram-dim'},`${round(b.height)} mm`);
    const titles = {front:'PANEL FRONTAL',back:'PANEL TRASERO',side:'LADO EXTERIOR',inner:'PARED HACIA EL PERFIL'};
    add('text',{x:0,y:-b.height-12,class:'diagram-title'},titles[view]);
  }
  const issues=new Set(validate(state).filter(i=>i.severity==='error').flatMap(i=>i.ids));
  const ps=drawnParts().sort((a,b)=>a.z-b.z);for(const p of ps){const def=LIBRARY[p.type],bb=bounds(p,b);let min,max;if(endView(view)){const a=endX(bb.min[1],view),c=endX(bb.max[1],view);min=[Math.min(a,c),-bb.max[2]];max=[Math.max(a,c),-bb.min[2]];}else if(sideView(view)){min=[bb.min[0],-bb.max[2]];max=[bb.max[0],-bb.min[2]];}else{min=[bb.min[0],Math.min(plotY(bb.min[1]),plotY(bb.max[1]))];max=[bb.max[0],Math.max(plotY(bb.min[1]),plotY(bb.max[1]))];}
    const isMounted = (view === 'front' && ['front','ramp'].includes(p.face))
      || (view === 'back' && p.face === 'back') || (view === 'side' && p.face === 'outer') || (view === 'inner' && p.face === 'inner');
    const opacity=view==='top'?1:isMounted?1:.23;
    const g=el('g',{'data-part':p.id,class:'diagram-part',opacity});const sel=p.id===state.ui.selected;
    if(p.face==='floor'||p.face==='lid'){
      if(view==='top'){const cc=[[-p.size[0]/2,-p.size[1]/2,0],[p.size[0]/2,-p.size[1]/2,0],[p.size[0]/2,p.size[1]/2,0],[-p.size[0]/2,p.size[1]/2,0]].map(q=>project(point(p,q)));g.append(el('polygon',{points:cc.map(p=>p.join(',')).join(' '),fill:def.color,stroke:issues.has(p.id)?'#bd5249':sel?'#224c39':'#456b57','stroke-width':sel?1.1:.5}));
        if(p.type==='fan'){const y=plotY(p.y);g.append(el('circle',{cx:p.x,cy:y,r:Math.min(...p.size.slice(0,2))*.37,fill:'#dfe8db',stroke:'#647e69','stroke-width':.5}));for(let k=0;k<7;k++){const r=k*Math.PI*2/7;g.append(el('line',{x1:p.x+Math.cos(r)*3,y1:y+Math.sin(r)*3,x2:p.x+Math.cos(r+.5)*12,y2:y+Math.sin(r+.5)*12,stroke:'#798e7c','stroke-width':2}));}}
        for(const [hx,hy] of def.holes||[]){const q=project(point(p,[hx,hy,0]));g.append(el('circle',{cx:q[0],cy:q[1],r:1.6,fill:'#e8e8c6',stroke:'#8a9b74','stroke-width':.3}));}
        if(p.type==='cooler')for(let i=0;i<8;i++){const q1=project(point(p,[-p.size[0]/2+4+i*(p.size[0]-8)/7,-p.size[1]/2+3,0])),q2=project(point(p,[-p.size[0]/2+4+i*(p.size[0]-8)/7,p.size[1]/2-3,0]));g.append(el('line',{x1:q1[0],y1:q1[1],x2:q2[0],y2:q2[1],stroke:'#b9c9c6','stroke-width':1}));}
      }else g.append(el('rect',{x:min[0],y:min[1],width:Math.max(.8,max[0]-min[0]),height:Math.max(.8,max[1]-min[1]),fill:def.color,stroke:sel?'#1e563c':'none','stroke-width':.8}));
    } else if (p.face === 'ramp') {
      const half = p.size.slice(0,2).map(n => n/2);
      const base = [[-half[0],-half[1]],[half[0],-half[1]],[half[0],half[1]],[-half[0],half[1]]];
      const outline = base.map(([u,v]) => project(point(p,[u,v,0],b)));
      g.append(el('polygon', {points:outline.map(v=>v.join(',')).join(' '),fill:def.color,
        stroke:issues.has(p.id)?'#bd5249':sel?'#214c36':'#64836b','stroke-width':sel?1:.65}));
    } else g.append(el('rect',{x:min[0],y:min[1],width:Math.max(1.3,max[0]-min[0]),height:Math.max(1.3,max[1]-min[1]),rx:.8,fill:def.color,stroke:issues.has(p.id)?'#bd5249':sel?'#214c36':'#64836b','stroke-width':sel?1:.45}));
    if (p.type !== 'clip' && ((view === 'top' && ['floor','ramp'].includes(p.face)) || isMounted)) {
      const label = p.type === 'driver' ? (p.name.endsWith('X') ? 'TMC · X' : 'TMC · Y') : def.short;
      const [x,y] = p.face === 'ramp' ? project([p.x,p.y,p.z]) : [(min[0]+max[0])/2,(min[1]+max[1])/2];
      const fontSize = p.type === 'driver' || p.type === 'switch' ? 2.9 : 4.3;
      g.append(el('text',{x,y,'text-anchor':'middle','dominant-baseline':'middle',class:'diagram-label',fill:'#fff','font-size':fontSize,'font-weight':500},label));
    }
    g.addEventListener('pointerdown',e=>beginDiagramDrag(e,p));s.append(g);
  }
  if (view === 'top') {
    for (const base of mountingBases(state)) for (const seat of base.seats) {
      const [x,y] = project(seat.center);
      add('circle',{cx:x,cy:y,r:seat.outsideDiameterMM/2,fill:'none',stroke:'#c39456','stroke-width':.55,
        'stroke-dasharray':'1.2 1',class:'diagram-port','data-floor-base':base.owner});
    }
  }
  if (state.ui.ports) {
    for (const p of ps) for (const port of portBoxes(p, b)) {
      const start = project(port.origin), end = project(port.origin.map((v,i) => v + port.normal[i] * port.space));
      add('line',{x1:start[0],y1:start[1],x2:end[0],y2:end[1],stroke:'#ae8551','stroke-width':.65,'stroke-dasharray':'2 1.4',class:'diagram-port'});
      add('circle',{cx:start[0],cy:start[1],r:1.1,fill:'#b78c4f',class:'diagram-port'});
      if (state.ui.selected === p.id) add('text',{x:end[0]+1,y:end[1]+1,class:'diagram-part-small'},port.name);
    }
  }
  const visibleFaces = {top:['lid','ramp'],front:['front','ramp'],back:['back'],side:['outer'],inner:['inner']};
  for (const opening of apertures(state, {ventilation:view === 'inner'})) {
    if (!visibleFaces[view].includes(opening.face)) continue;
    const panel = enclosurePanel(b, opening.face);
    if (!panel) continue;
    const pts = openingOutline(panel, opening).map(uv => project(panelPoint(panel, uv)));
    const vent = opening.kind === 'hexagon';
    add('polygon', {
      points:pts.map(v=>v.join(',')).join(' '), fill:vent?'#f8faf5':'none',
      stroke:vent?'#759181':'#b48843','stroke-width':.55,'stroke-dasharray':vent?'none':'1.5 1',class:'diagram-port',
      'data-opening':opening.name,
    });
    if (view === 'back' && opening.id === 'rear-power') {
      const [x,y] = project(opening.center);
      add('text', {x,y:y+13,'text-anchor':'middle',class:'diagram-part-small'},opening.name);
    }
  }
  root.append(s);
}
function svgPoint(e){const pt=new DOMPoint(e.clientX,e.clientY);const v=pt.matrixTransform(svgMap.svg.getScreenCTM().inverse());return[v.x,v.y];}
function beginDiagramDrag(e,p){e.preventDefault();state.ui.selected=p.id;const start=unproject(svgPoint(e),p);drag={kind:'svg',id:p.id,start,original:clone(state),pointer:e.pointerId};$('viewport').setPointerCapture(e.pointerId);renderInspector();renderList();if(p.locked)toast('Esta pieza está bloqueada.');}
function dragDiagram(e){if(drag?.kind!=='svg')return;const p=drag.original.parts.find(p=>p.id===drag.id);if(p.locked)return;const pos=unproject(svgPoint(e),p),delta=pos.map((v,i)=>v-drag.start[i]);state=clone(drag.original);const snap=e.shiftKey?0:state.ui.snap;const d=delta.map((v,i)=>snap?Math.round((p[['x','y','z'][i]]+v)/snap)*snap-p[['x','y','z'][i]]:v);movePart(state,p.id,d,groupMoves());drawDiagram();renderInspector();renderChecks();update3D();}
function endDrag(){if(!drag)return;if(JSON.stringify(drag.original.parts)!==JSON.stringify(state.parts)){history.push(drag.original);future=[];save();}drag=null;controls&&(controls.enabled=true);render();}

let renderer,scene,camera,controls,root3D,content3D,partObjects=[],labelObjects=[],needsFit=true,webGLFailed=false;
const W=v=>new THREE.Vector3(v[0],v[2],-v[1]);
function init3D(){try{renderer=new THREE.WebGLRenderer({canvas:$('scene'),antialias:true,preserveDrawingBuffer:true});renderer.setPixelRatio(Math.min(devicePixelRatio,2));renderer.setClearColor('#eff3ea');renderer.outputColorSpace=THREE.SRGBColorSpace;scene=new THREE.Scene();scene.add(new THREE.HemisphereLight(0xffffff,0x71826b,2.5));const light=new THREE.DirectionalLight(0xfffbef,3);light.position.set(-100,400,-150);scene.add(light);camera=new THREE.PerspectiveCamera(36,1,.5,4000);controls=new OrbitControls(camera,renderer.domElement);controls.enableDamping=true;controls.dampingFactor=.09;controls.maxPolarAngle=Math.PI*.49;root3D=new THREE.Group();root3D.rotation.x=-Math.PI/2;scene.add(root3D);renderer.domElement.addEventListener('pointerdown',begin3DDrag);renderer.domElement.addEventListener('pointermove',move3DDrag);renderer.domElement.addEventListener('pointerup',endDrag);renderer.domElement.addEventListener('pointercancel',endDrag);new ResizeObserver(resize3D).observe($('viewport'));requestAnimationFrame(frame);}catch(e){webGLFailed=true;console.warn('3D unavailable:',e.message);if(state.ui.view==='3d')state.ui.view='top';}}
function material(color,opacity=1){return new THREE.MeshStandardMaterial({color,roughness:.65,metalness:.08,transparent:opacity<1,opacity,side:THREE.DoubleSide,depthWrite:opacity>.55});}
function cube(group,size,center,color,opacity=1){const o=new THREE.Mesh(new THREE.BoxGeometry(...size),material(color,opacity));o.position.set(...center);group.add(o);return o;}
function cylinder(group,r,h,center,color){const geo=new THREE.CylinderGeometry(r,r,h,32);geo.rotateX(Math.PI/2);const o=new THREE.Mesh(geo,material(color));o.position.set(...center);group.add(o);return o;}
function dispose(g){g.traverse(o=>{o.geometry?.dispose();if(o.material){for(const m of Array.isArray(o.material)?o.material:[o.material])m.dispose();}});g.removeFromParent();}
function drawFloorBases(group) {
  for (const base of mountingBases(state)) {
    if (base.cradleSizeMM) {
      const cradle = new THREE.Group();
      cradle.position.set(...base.center);
      cradle.rotation.z = base.rotation * Math.PI / 180;
      group.add(cradle);
      const [length,width] = base.cradleSizeMM;
      const h = base.heightMM;
      cube(cradle,[length-15,width,h],[0,0,h/2],'#b79263');
      for (const side of [-1,1]) {
        cube(cradle,[length-15,2,h+2],[0,side*(width-2)/2,(h+2)/2],'#ae8c60');
      }
    }
    for (const seat of base.seats) {
      const outline = new THREE.Shape();
      outline.absarc(0,0,seat.outsideDiameterMM/2,0,Math.PI*2);
      const bore = new THREE.Path();
      bore.absarc(0,0,seat.boreDiameterMM/2,0,Math.PI*2,true);
      outline.holes.push(bore);
      const geometry = new THREE.ExtrudeGeometry(outline,{depth:base.heightMM,bevelEnabled:false,curveSegments:16});
      const boss = new THREE.Mesh(geometry, material('#b79263'));
      boss.position.set(...seat.center);
      group.add(boss);
    }
  }
}
function wall(group, face, openings, alpha = 0.21) {
  const panel = enclosurePanel(state.box, face);
  if (!panel) return;
  const vectors = outline => outline.map(([x,y]) => new THREE.Vector2(x,y));
  const shape = new THREE.Shape(vectors(panel.outline));
  const holes = openings.filter(opening => opening.face === face && openingFits(panel, opening, 0.1));
  for (const opening of holes) {
    shape.holes.push(new THREE.Path(vectors(openingOutline(panel, opening).reverse())));
  }
  const depth = state.box.wall;
  const geometry = new THREE.ExtrudeGeometry(shape, {depth,bevelEnabled:false});
  if (panel.inward < 0) geometry.translate(0,0,-depth);
  const color = face === 'ramp' || (face === 'inner' && state.box.innerVent) ? '#9cbdaf' : '#bacab0';
  const mesh = new THREE.Mesh(geometry, material(color, alpha));
  mesh.position.set(...panel.origin);
  mesh.quaternion.setFromRotationMatrix(new THREE.Matrix4().makeBasis(...panel.axes.map(v=>new THREE.Vector3(...v))));
  group.add(mesh);
  const edge = new THREE.LineSegments(
    new THREE.EdgesGeometry(geometry, 30),
    new THREE.LineBasicMaterial({color:'#648879',transparent:true,opacity:face === 'inner' ? 0.62 : 0.45}),
  );
  edge.position.copy(mesh.position);
  edge.quaternion.copy(mesh.quaternion);
  group.add(edge);
}
function visualPart(p){const def=LIBRARY[p.type],g=new THREE.Group(),[w,d,h]=p.size;g.position.set(p.x,p.y,p.z);g.quaternion.setFromRotationMatrix(new THREE.Matrix4().makeBasis(...axes(p,state.box).map(a=>new THREE.Vector3(...a))));
 if(['pi','mks','mosfet','driver'].includes(p.type)){
   cube(g,[w,d,1.6],[0,0,.8],def.color);
   for(const [x,y]of def.holes||[])cylinder(g,2.1,.2,[x,y,1.7],'#dbc28a');
   if(p.type==='pi'){cube(g,[22,16,2],[0,0,2.6],'#888b89');for(const y of [-16,2,19])cube(g,[17,14,14],[w/2-5,y,8.6],'#b5babb');cube(g,[42,5,8],[-12,d/2-4,5.6],'#343c3a');for(const x of [-25,-10,4])cube(g,[9,6,5],[x,-d/2,4],'#babbb4');}
   if(p.type==='mks'){cube(g,[22,20,3],[w/2-14,1,3.1],'#b9bab1');for(const x of [-31,-17.5,-4,9.5])cube(g,[10,6,7],[x,d/2-7,5.1],'#293c35');cube(g,[12,16,11],[-8,-d/2+5,7.1],'#b9bcb6');cube(g,[9,14,11],[-23,-d/2+5,7.1],'#36443d');for(const x of [-29,-11,5])for(const a of [-1,1])cube(g,[3,22,8],[x+a*7.6,12,5.6],'#3d4e43');}
   if(p.type==='mosfet'){cube(g,[11,12,8],[4,0,5.6],'#bdc6b7');cube(g,[7,7,6],[-8,0,4.6],'#e5e7db');}
   if(p.type==='driver'){cube(g,[w*.75,d*.7,h-2],[0,0,h/2+1],'#a3aa9f');for(let i=0;i<5;i++)cube(g,[w*.1,d*.72,h*.4],[-w*.3+i*w*.15,0,h*.8],'#c9cfc3');}
 }else if(p.type==='cooler'){cube(g,[w,d,3],[0,0,1.5],'#46534d');for(let i=0;i<10;i++)cube(g,[2,d,h-3],[-w/2+2+i*(w-4)/9,0,(h+3)/2],'#75857a');}
 else if(p.type==='fan'){
   const surface = p.face === 'floor' ? h : 0;
   const side = p.face === 'floor' ? 1 : -1;
   cube(g,[w,d,h],[0,0,h/2],'#4b5b53');
   cylinder(g,Math.min(w,d)*.38,.4,[0,0,surface+side*.2],'#b8c4b0');
   cylinder(g,Math.min(w,d)*.12,.6,[0,0,surface+side*.6],'#687e68');
   for (let i=0;i<7;i++) {
     const a = i * Math.PI / 3.5;
     const blade = cube(g,[Math.min(w,d)*.22,3,.6],[Math.cos(a)*9,Math.sin(a)*9,surface+side*.6],'#5a705d');
     blade.rotation.z = a + .6;
   }
 }
 else if(p.type==='lcd'){cube(g,[w,d,1.6],[0,0,.8],'#283c35');cube(g,[w*.73,d*.86,3],[0,0,-1.5],'#182d2c');cube(g,[w*.64,d*.75,.3],[0,0,-3.2],'#527d91');cube(g,[w*.22,7,9],[-w*.16,d*.21,6],'#3c4e42');cube(g,[w*.22,7,9],[w*.14,d*.21,6],'#3c4e42');}
 else if(p.type==='switch'){cube(g,[w,d,h*.63],[0,0,h*.35],'#524c3d');cylinder(g,6,7,[0,0,-3.5],'#b8bcb3');cylinder(g,2,14,[0,0,-12],'#e3e5df');}
 else if (p.type === 'clip') {
   const thickness = Math.min(w * .18,d * .15,h * .23);
   const jaw = d * .27;
   cube(g,[w,d,thickness],[0,0,thickness/2],def.color);
   for (const side of [-1,1]) {
     cube(g,[w,thickness,h],[0,side*(d-thickness)/2,h/2],def.color);
     cube(g,[w,jaw,thickness],[0,side*(d-jaw)/2,h-thickness/2],def.color);
   }
 }
 else cube(g,[w,d,h],[0,0,h/2],def.color);
 const edges=new THREE.LineSegments(new THREE.EdgesGeometry(new THREE.BoxGeometry(w,d,h)),new THREE.LineBasicMaterial({color:p.id===state.ui.selected?'#d7a143':'#4f7964',transparent:true,opacity:p.id===state.ui.selected ? .9 : .18}));edges.position.z=h/2;g.add(edges);g.traverse(o=>o.userData.partId=p.id);return g;
}
function update3D(){if(!root3D||state.ui.view!=='3d')return;if(content3D)dispose(content3D);content3D=new THREE.Group();root3D.add(content3D);partObjects=[];labelObjects=[];const b=state.box;cube(content3D,[b.length,b.width,b.wall],[b.length/2,b.width/2,b.wall/2],'#c9d6bc',.73);
 drawFloorBases(content3D);
 const openings = apertures(state);
 for (const face of ['front','back','inner','outer','ramp']) wall(content3D, face, openings);
 if (state.ui.lid) wall(content3D, 'lid', openings, 0.16);
 if (state.ui.ports) {
   for (const part of drawnParts()) for (const port of portBoxes(part,b)) {
     const end = port.origin.map((value,i) => value + port.normal[i] * port.space);
     const geometry = new THREE.BufferGeometry().setFromPoints([port.origin,end].map(p=>new THREE.Vector3(...p)));
     const guide = new THREE.Line(geometry, new THREE.LineDashedMaterial({color:'#a0804b',dashSize:3,gapSize:2}));
     guide.computeLineDistances();
     content3D.add(guide);
   }
 }
 if(state.ui.robot){cube(content3D,[355,20,40],[177.5,-b.offset-10,b.profileBase+20],'#aab7ac',.75);for(const z of [10,30])cube(content3D,[355,.8,3.5],[177.5,-b.offset-.4,b.profileBase+z],'#718273');for(const x of b.anchors){cube(content3D,[20,b.offset+b.wall,5],[x,-b.offset/2,b.profileBase+6],'#b5985f');for(const z of [10,30]){const head=cylinder(content3D,3.5,2,[x,-b.offset+1,b.profileBase+z],'#9a7e48');head.rotation.x=Math.PI/2;}}}
 for(const p of drawnParts()){const g=visualPart(p);content3D.add(g);partObjects.push(g);labelObjects.push({p,g});}
 if(b.length>b.bed-10){const pts=[new THREE.Vector3(b.split,0,b.wall+.1),new THREE.Vector3(b.split,b.width,b.wall+.1)];content3D.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints(pts),new THREE.LineDashedMaterial({color:'#ae8c50',dashSize:4,gapSize:3})));}
 if(needsFit){fitCamera();needsFit=false;}}
function resize3D(){if(!renderer)return;const r=$('viewport').getBoundingClientRect();renderer.setSize(r.width,r.height,false);camera.aspect=r.width/r.height;camera.updateProjectionMatrix();}
function fitCamera() {
  if (!camera) return;
  const box = state.box;
  const contentLength = Math.max(box.length, state.ui.robot ? 355 : 0);
  const center = W([contentLength * 0.45, (box.width - box.offset) / 2, box.height * 0.4]);
  controls.target.copy(center);
  const viewport = $('viewport').getBoundingClientRect();
  const distance = Math.max(contentLength,box.width * 1.7,220) * Math.max(1.04, 1.07 * viewport.height / viewport.width);
  camera.position.copy(center).add(new THREE.Vector3(-distance*.75,distance*.87,-distance*.88));
  controls.update();
  resize3D();
}
function frame(){requestAnimationFrame(frame);if(state.ui.view!=='3d'||!renderer)return;controls.update();renderer.render(scene,camera);const labels=$('scene-labels');labels.replaceChildren();const rect=$('viewport').getBoundingClientRect();for(const {p}of labelObjects){
  if ((p.parent || p.type === 'clip') && p.id !== state.ui.selected) continue;
  const float = ['ramp','front','back','outer','inner','lid'].includes(p.face) ? -7 : p.size[2] + 6;
  const v = W(point(p, [0,0,float], state.box)).project(camera);if(v.z>1||v.z< -1)continue;const e=html('span',`scene-label${p.id===state.ui.selected?' selected':''}`,LIBRARY[p.type].short);e.style.left=(v.x*.5+.5)*rect.width+'px';e.style.top=(-v.y*.5+.5)*rect.height+'px';labels.append(e);}}
function ray(e){const rect=$('scene').getBoundingClientRect(),r=new THREE.Raycaster();r.setFromCamera(new THREE.Vector2((e.clientX-rect.left)/rect.width*2-1,-(e.clientY-rect.top)/rect.height*2+1),camera);return r;}
function begin3DDrag(e){if(e.button!==0||e.altKey)return;const r=ray(e),hit=r.intersectObjects(partObjects,true).find(h=>h.object.userData.partId);if(!hit)return;const p=state.parts.find(p=>p.id===hit.object.userData.partId);state.ui.selected=p.id;const n=W(axes(p,state.box)[2]).normalize(),origin=W([p.x,p.y,p.z]),plane=new THREE.Plane().setFromNormalAndCoplanarPoint(n,origin),start=new THREE.Vector3();if(!r.ray.intersectPlane(plane,start))return;controls.enabled=false;drag={id:p.id,original:clone(state),plane,start3D:start};$('scene').setPointerCapture(e.pointerId);renderList();renderInspector();update3D();}
function move3DDrag(e){if(!drag?.plane)return;const p=drag.original.parts.find(p=>p.id===drag.id);if(p.locked)return;const target=new THREE.Vector3();if(!ray(e).ray.intersectPlane(drag.plane,target))return;const v=target.sub(drag.start3D),raw=[v.x,-v.z,v.y];state=clone(drag.original);const snap=e.shiftKey?0:state.ui.snap,keys=['x','y','z'];const d=raw.map((v,i)=>snap?Math.round((p[keys[i]]+v)/snap)*snap-p[keys[i]]:v);movePart(state,p.id,d,groupMoves());update3D();renderInspector();renderChecks();}

function render(){const b=state.box;for(const key of boxFields)num(`box-${key}`,b[key]);b.anchors.forEach((n,i)=>num(`anchor-${i}`,n));$('dimensions-label').textContent=`${round(b.length)} × ${round(b.width)} × ${round(b.height)} mm`;$('print-summary').textContent=b.length>b.bed-10?`Dos secciones de ${round(b.split)} y ${round(b.length-b.split)} mm`:'Una sección según el largo de cama';$('undo').disabled=!history.length;$('redo').disabled=!future.length;$('snap').value=state.ui.snap;$('show-ports').checked=state.ui.ports;$('show-lid').checked=state.ui.lid;
 const front = frontProfile(b);
 $('mount-side-label').textContent = leftMount() ? 'Módulo a la izquierda del robot' : 'Módulo a la derecha del robot';
 $('show-electronics').checked = state.ui.electronics !== false;
 $('inner-vent').checked = b.innerVent;
 const displayZone = b.screenZone > 0 && b.screenZone <= front.run ? ` · ${b.screenZone} mm para la pantalla` : '';
 $('front-summary').textContent = !front.enabled ? 'Frente vertical' : !front.valid ? 'Revisá la altura y el ángulo' : `Labio de ${round(front.frontHeight)} mm${displayZone}`;
 for(const e of document.querySelectorAll('[data-view]')) {
   const active = e.dataset.view === state.ui.view;
   e.classList.toggle('active', active);
   e.setAttribute('aria-pressed', active ? 'true' : 'false');
 }
 const three=state.ui.view==='3d';$('scene').style.display=three?'block':'none';$('scene-labels').style.display=three?'block':'none';$('diagram').style.display=three?'none':'block';$('view-hint').textContent=three?'Arrastrá una pieza · arrastrá el fondo para orbitar · rueda para zoom':'Arrastrá las piezas · R para girar · flechas para ajustar';$('empty-view').hidden=!(three&&webGLFailed);renderList();renderInspector();renderChecks();if(!three)drawDiagram();update3D();renderCutouts();save();}
function renderCutouts(){const list=$('cutouts-list');list.replaceChildren();state.cutouts.forEach((h,i)=>{const row=html('div','cutout-item');row.append(html('span','',`${h.name} · ${h.size.join(' × ')} mm`));const remove=html('button','','×');remove.setAttribute('aria-label',`Retirar abertura ${h.name}`);remove.onclick=()=>commit(()=>state.cutouts.splice(i,1));row.append(remove);list.append(row);});}

for(const [type,def]of Object.entries(LIBRARY))$('add-part').add(new Option(def.name,type));
for(const key of boxFields)$('box-'+key).addEventListener('change',e=>{const v=Number(e.target.value),min=Number(e.target.min),max=Number(e.target.max);if(!e.target.value||!Number.isFinite(v)||v<min||v>max){e.target.value=round(state.box[key]);toast(`Usá un valor entre ${min} y ${max}.`);return;}commit(()=>setBox(state,key,v));});
for(let i=0;i<2;i++)$(`anchor-${i}`).onchange=e=>commit(()=>state.box.anchors[i]=Math.max(0,Math.min(600,Number(e.target.value)||0)));
for(const key of ['x','y','z'])$('part-'+key).onchange=e=>{const p=selected(),value=Number(e.target.value);if(!p||!Number.isFinite(value))return;const delta=[0,0,0];delta[['x','y','z'].indexOf(key)]=value-p[key];commit(()=>movePart(state,p.id,delta,groupMoves()));};
$('part-name').onchange=e=>commit(()=>selected().name=e.target.value.slice(0,100)||LIBRARY[selected().type].name);
$('part-face').onchange=e=>commit(()=>setMountingFace(state,selected(),e.target.value));
$('part-rotation').onchange=e=>{const p=selected(),v=Number(e.target.value);if(p&&Number.isFinite(v))commit(()=>rotatePart(state,p.id,v-p.rotation));};
$('rotate-left').onclick=()=>commit(()=>selected()&&rotatePart(state,selected().id,-90));$('rotate-right').onclick=()=>commit(()=>selected()&&rotatePart(state,selected().id,90));
['w','d','h'].forEach((key,i)=>$('part-'+key).onchange=e=>{const v=Number(e.target.value);if(v>=.5&&v<=500)commit(()=>{selected().size[i]=v;selected().verified=false;});else render();});
$('part-locked').onchange=e=>commit(()=>selected().locked=e.target.checked);$('part-verified').onchange=e=>commit(()=>selected().verified=e.target.checked);$('part-parent').onchange=e=>commit(()=>selected().parent=e.target.value||null);
$('remove-part').onclick=()=>{const p=selected();if(!p)return;commit(()=>{for(const q of state.parts)if(q.parent===p.id)q.parent=null;state.parts=state.parts.filter(q=>q.id!==p.id);state.ui.selected=state.parts[0]?.id;});};
$('add-part').onchange=e=>{const type=e.target.value;if(!LIBRARY[type])return;commit(()=>{const n=initialState().parts.find(p=>p.type===type)||{id:'',type,name:LIBRARY[type].name,size:[...LIBRARY[type].size],x:state.box.length/2,y:state.box.width/2,z:8,rotation:0,face:'floor',visible:true,locked:false,parent:null,verified:false};const p=clone(n);p.id=`${type}-${Date.now().toString(36)}`;p.parent=null;p.x=round(state.box.length/2);p.y=round(state.box.width/2);p.verified=false;setMountingFace(state,p,p.face==='ramp'&&!frontProfile(state.box).enabled?'front':p.face);state.parts.push(p);state.ui.selected=p.id;});e.target.value='';};
document.querySelectorAll('[data-view]').forEach(e=>e.onclick=()=>{if(e.dataset.view==='3d'&&webGLFailed){toast('Usá las vistas de planta y de paneles en este navegador.');return;}state.ui.view=e.dataset.view;render();resize3D();});
$('show-ports').onchange=e=>{state.ui.ports=e.target.checked;render();};$('show-lid').onchange=e=>{state.ui.lid=e.target.checked;render();};$('snap').onchange=e=>{state.ui.snap=Number(e.target.value);save();};$('fit-view').onclick=()=>{if(state.ui.view==='3d')fitCamera();else drawDiagram();};
$('inner-vent').onchange = e => commit(() => setBox(state, 'innerVent', e.target.checked));
$('show-electronics').onchange = e => {
  state.ui.electronics = e.target.checked;
  render();
};
$('undo').onclick=()=>{if(history.length){future.push(clone(state));state=history.pop();render();}};$('redo').onclick=()=>{if(future.length){history.push(clone(state));state=future.pop();render();}};
$('toggle-checks').onclick=()=>{$('checks-list').hidden=!$('checks-list').hidden;$('toggle-checks').textContent=$('checks-list').hidden?'Ver detalles':'Ocultar';};
$('download-json').onclick=()=>{downloads('FT412-modulo-lateral-diseno.json',JSON.stringify(exportLayout(state),null,2));toast('Diseño exportado. Podés pasarlo para convertir la distribución en CAD.');};
$('download-html').onclick=()=>{const doc=document.documentElement.cloneNode(true);doc.querySelector('#diagram').replaceChildren();doc.querySelector('#scene-labels').replaceChildren();const snap=exportLayout(state);snap.documentId=`saved-${Date.now()}`;doc.querySelector('#saved-layout').textContent=JSON.stringify(snap).replace(/</g,'\\u003c');doc.querySelector('#loading').hidden=false;doc.querySelector('#toast').hidden=true;doc.querySelector('#cutout-dialog').removeAttribute('open');downloads('FT412-modulo-lateral-editor.html','<!doctype html>\n'+doc.outerHTML,'text/html;charset=utf-8');toast('HTML guardado con tu distribución y el editor completo.');};
$('import').onclick=()=>$('import-file').click();$('import-file').onchange=async e=>{const f=e.target.files[0];if(!f)return;try{if(f.size>2e6)throw new Error('El archivo es demasiado grande.');const next=sanitize(JSON.parse(await f.text()));commit(()=>state=next);toast('Diseño cargado.');}catch(err){toast(err.message);}e.target.value='';};
$('reset-design').onclick = () => {
  if (confirm('¿Cargar el boceto de 280 × 120 mm? Podés volver a tu diseño con Deshacer.')) {
    commit(() => {
      state = initialState();
      if (webGLFailed) state.ui.view = 'top';
      needsFit = true;
    });
  }
};
$('snapshot').onclick=async()=>{if(state.ui.view==='3d'&&renderer){renderer.render(scene,camera);const a=document.createElement('a');a.href=renderer.domElement.toDataURL('image/png');a.download='FT412-modulo-vista-3D.png';a.click();return;}const s=svgMap.svg.cloneNode(true),sty=el('style');sty.textContent='.diagram-title,.diagram-dim,.diagram-part-small{font-family:Arial,sans-serif;fill:#55725b;font-size:4px}.diagram-title{font-weight:bold}.diagram-label{font-family:Arial,sans-serif}';s.prepend(sty);s.setAttribute('xmlns',NS);s.setAttribute('width','1800');s.setAttribute('height','1100');const url=URL.createObjectURL(new Blob([new XMLSerializer().serializeToString(s)],{type:'image/svg+xml'}));const image=new Image();image.onload=()=>{const c=document.createElement('canvas');c.width=1800;c.height=1100;const ctx=c.getContext('2d');ctx.fillStyle='#f5f8f0';ctx.fillRect(0,0,c.width,c.height);ctx.drawImage(image,0,0,c.width,c.height);const a=document.createElement('a');a.download='FT412-modulo-vista.png';a.href=c.toDataURL('image/png');a.click();URL.revokeObjectURL(url);};image.src=url;};
$('add-cutout').onclick=()=>$('cutout-dialog').showModal();$('cancel-cutout').onclick=()=>$('cutout-dialog').close();$('cutout-form').onsubmit=e=>{e.preventDefault();const f=new FormData(e.target),face=f.get('face'),u=Number(f.get('u')),v=Number(f.get('v')),b=state.box;const center=face==='front'||face==='back'?[face==='front'?0:b.length,u,v]:face==='lid'?[u,v,b.height]:[u,face==='inner'?0:b.width,v];commit(()=>state.cutouts.push({id:`cut-${Date.now()}`,name:String(f.get('name')),face,center,size:[Number(f.get('w')),Number(f.get('h'))],kind:'rect',draft:true}));$('cutout-dialog').close();};
document.addEventListener('keydown', e => {
  if (e.target.closest('input,textarea,select,dialog')) return;
  const modified = e.metaKey || e.ctrlKey;
  const key = e.key.toLowerCase();
  if (modified && key === 'z') { e.preventDefault(); $(e.shiftKey ? 'redo' : 'undo').click(); return; }
  if (modified && key === 's') { e.preventDefault(); $('download-html').click(); return; }
  const part = selected();
  if (!part) return;
  if (key === 'r') { e.preventDefault(); $('rotate-right').click(); return; }
  const step = e.shiftKey ? 10 : (state.ui.snap || 1);
  const directions = {ArrowLeft:[-step,0],ArrowRight:[step,0],ArrowUp:[0,-step],ArrowDown:[0,step]};
  const direction = directions[e.key];
  if (!direction) return;
  e.preventDefault();
  const [u,v] = direction;
  const view = state.ui.view;
  let delta;
  if (endView(view)) delta = [inclinedDistance(part,-v),flipEnd(view) ? -u : u,-v];
  else if (sideView(view)) delta = [u,0,-v];
  else delta = [u,view === 'top' ? plotY(v) : v,0];
  commit(() => movePart(state,part.id,delta,groupMoves()));
});

init3D();$('loading').hidden=true;render();
document.addEventListener('pointermove',dragDiagram);document.addEventListener('pointerup',endDrag);document.addEventListener('pointercancel',endDrag);
window.ft412Editor={getState:()=>clone(state),getIssues:()=>validate(state),exportLayout:()=>exportLayout(state),load:v=>{state=sanitize(v);history=[];future=[];render();},getApertures:()=>apertures(state),getVersion:()=>VERSION,
  projectPart:id=>{const p=state.parts.find(p=>p.id===id);if(!p||!camera)return null;const v=W(point(p,[0,0,3],state.box)).project(camera),r=$('scene').getBoundingClientRect();return {x:r.left+(v.x*.5+.5)*r.width,y:r.top+(-v.y*.5+.5)*r.height};}};

if (new URLSearchParams(location.search).get("home")==="en") {
  const home=document.querySelector("[data-landing]");
  home.href="https://livinginacat.world/";home.textContent="← Back to home";
}
