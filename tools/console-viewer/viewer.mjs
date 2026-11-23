import { modes } from './modes.mjs';
import { createWorkshop } from './scene.mjs';

const page=document.documentElement;
const find=id=>document.getElementById(id);
const buttons=selector=>Array.from(document.querySelectorAll(selector));
const views=buttons('[data-view]');
const angles=buttons('[data-angle]');
const parameters=new URLSearchParams(location.search);
const ids={conjunto:'outside',herrajes:'hardware',recorrido:'travel',interruptor:'switch',camara:'optics',electronica:'electronics'};
const embedded=page.classList.contains('embed');
const requested=parameters.get('vista');
let current=Object.hasOwn(ids,requested)?ids[requested]:embedded?'outside':'hardware';
let angle='iso',selected=-1, pins=[], labels=[], scene;
const pose={x:0,y:0,z:0,on:false};
const mm=n=>n.toLocaleString('es-CR',{maximumFractionDigits:2})+' mm';
const posterText={
  outside:'Consola completa con el pórtico de la cámara y el teléfono',
  hardware:'Tornillos y tuercas del conjunto a través de las piezas impresas',
  travel:'Rieles, puente móvil y motores del mecanismo',
  optics:'Cámara en su soporte regulable por encima del teléfono',
  switch:'Interruptor frontal, su tuerca y sus dos bornes',
  electronics:'Raspberry Pi, MKS y componentes bajo la cama del teléfono'
};
const fallbackImages=Object.fromEntries(Object.keys(modes).map(mode=>[mode,new URL('./'+mode+'.webp',import.meta.url).href]));
function mark(index){
  selected=selected===index?-1:index;
  for(const [i,label] of labels.entries()){
    label.setAttribute('aria-pressed',String(i===selected));
    pins[i]?.setAttribute('aria-pressed',String(i===selected));
  }
  scene?.mark(selected<0?null:modes[current].tags[selected][3]);
}
function positionPins(points){
  const show=find('annotations').checked;
  for(const [i,point] of points.entries()){
    if(!pins[i])continue;
    pins[i].hidden=!show||!point.visible;
    pins[i].style.left=point.left+'%';
    pins[i].style.top=point.top+'%';
  }
}
function displayMode(save=false){
  const definition=modes[current];
  find('section-title').textContent=definition.title;
  find('section-text').textContent=definition.text;
  const poster=find('poster');
  poster.src=fallbackImages[current];
  poster.alt=posterText[current];
  for(const b of views)b.setAttribute('aria-pressed',String(b.dataset.view===current));
  for(const id of ['travel','optics','switch'])find(id+'-controls').hidden=!scene||current!==id;
  find('parts').replaceChildren();
  find('pins').replaceChildren();
  pins=[];labels=[];selected=-1;
  definition.tags.forEach(([title,description],i)=>{
    const label=document.createElement(scene?'button':'div');
    label.className='tag';
    const index=document.createElement('span');
    index.className='index';index.textContent=String(i+1);
    const stack=document.createElement('span');
    const name=document.createElement('strong');
    name.textContent=title;
    const detail=document.createElement('small');
    detail.textContent=description;
    stack.append(name,detail);label.append(index,stack);find('parts').append(label);
    if(!scene)return;
    label.type='button';label.setAttribute('aria-pressed','false');
    label.onclick=()=>mark(i);labels.push(label);
    const pin=document.createElement('button');
    pin.type='button';pin.className='pin';pin.textContent=String(i+1);
    pin.setAttribute('aria-label',title);pin.setAttribute('aria-pressed','false');
    pin.title=title;pin.onclick=()=>mark(i);
    find('pins').append(pin);pins.push(pin);
  });
  scene?.select(current,definition,pose,angle);
  if(save&&!embedded){
    const link=new URL(location.href);
    link.searchParams.set('vista',Object.keys(ids).find(id=>ids[id]===current));
    history.replaceState(null,'',link);
  }
}
function setPose(){
  pose.x=Number(find('sx').value);
  pose.y=Number(find('sy').value);
  pose.z=Number(find('sz').value);
  find('xout').value=mm(pose.x);find('yout').value=mm(pose.y);
  find('lensout').value=mm(100+pose.z);find('heightout').textContent=mm(231+pose.z);
  for(const b of buttons('[data-toggle]'))b.setAttribute('aria-pressed',String((b.dataset.toggle==='on')===pose.on));
  scene?.pose(pose);
}
for(const b of views)b.onclick=()=>{current=b.dataset.view;displayMode(true);};
for(const b of angles)b.onclick=()=>{
  angle=b.dataset.angle;for(const a of angles)a.setAttribute('aria-pressed',String(a===b));
  scene?.angle(angle);
};
for(const b of buttons('[data-toggle]'))b.onclick=()=>{pose.on=b.dataset.toggle==='on';setPose();};
for(const b of buttons('[data-position]'))b.onclick=()=>{
  const value=Number(b.dataset.position);
  find('sx').value=String(value*55.05);find('sy').value=String(value*105.05);setPose();
};
for(const id of ['sx','sy','sz'])find(id).oninput=setPose;
find('annotations').onchange=()=>scene?.redraw();

function showStatic(){
  scene=undefined;
  page.dataset.render='static';
  find('viewer').querySelector('canvas')?.remove();
  const status=find('status');
  status.hidden=false;
  status.textContent='Vista estática · elegí una sección para ver su imagen.';
  displayMode();
}
if(embedded && window.parent!==window){
  const workspace=document.querySelector('.workspace');
  const resize=new ResizeObserver(()=>{
    const height=Math.ceil(workspace.getBoundingClientRect().height);
    window.parent.postMessage({type:'ft412:visor-height',height},location.origin);
  });
  resize.observe(workspace);
}
displayMode();
const status=find('status');
status.textContent='Cargando el modelo 3D…';status.hidden=false;
try{
  scene=await createWorkshop(find('viewer'),positionPins,showStatic);
  page.dataset.render='live';
  status.hidden=true;
  displayMode();
}catch{
  showStatic();
}
