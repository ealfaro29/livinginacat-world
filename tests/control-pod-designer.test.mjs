import test from 'node:test';
import assert from 'node:assert/strict';
import {initialState,clone,bounds,intersects,movePart,rotatePart,setBox,validate,sanitize,exportLayout,apertures,restoreLayout,mountingBases} from '../tools/control-pod-designer/model.mjs';
import {enclosurePanel,frontProfile,openingFits,rampMountHeight} from '../tools/control-pod-designer/enclosure.mjs';

test('the owner layout retains the 30 mm lip, 45° panel and 90 mm body without a step',()=>{
  const state = initialState();
  const profile = frontProfile(state.box);
  assert.deepEqual([state.box.length,state.box.width,state.box.height], [280,120,90]);
  assert.equal(profile.angle, 45);
  assert.equal(profile.run, 60);
  assert.equal(Math.round(profile.frontHeight), 30);
  assert.equal(state.box.screenZone, 55);
  assert.equal(state.box.split, 135);
  assert.equal(state.parts.filter(part => part.type !== 'clip').length,10);
  assert.equal(state.box.mountSide,'left');
  assert.ok(state.parts.every(part => !part.verified));
  assert.ok(!validate(state).some(issue => issue.severity === 'error'));
});
test('the CanaKit fan travels with the heatsink and its opening stays in the roof',()=>{
  const s=initialState(),before=clone(s);movePart(s,'pi',[-10,-5,7]);
  for(const id of ['pi','cooler','fan']){const a=before.parts.find(p=>p.id===id),b=s.parts.find(p=>p.id===id);assert.equal(b.x,a.x-10);assert.equal(b.y,a.y-5);assert.equal(b.z,a.z+7);}
  setBox(s,'height',100);
  const vent=apertures(s).find(opening=>opening.owner==='fan');
  assert.equal(vent.face,'lid');
  assert.deepEqual(vent.center,[86,57,100]);
  assert.equal(s.parts.find(part=>part.id==='fan').z,36);
});
test('MKS rotation carries both drivers around the board and preserves their radial offsets',()=>{
  const s=initialState(),m=s.parts.find(p=>p.id==='mks');const drivers=s.parts.filter(p=>p.parent==='mks').map(p=>({id:p.id,r:Math.hypot(p.x-m.x,p.y-m.y)}));
  rotatePart(s,'mks',90);for(const d of drivers){const p=s.parts.find(p=>p.id===d.id);assert.ok(Math.abs(Math.hypot(p.x-m.x,p.y-m.y)-d.r)<.2);assert.equal(p.rotation,270);}
  const b=bounds(m);assert.equal(Math.round(b.max[0]-b.min[0]),70);assert.equal(Math.round(b.max[1]-b.min[1]),90);
});
test('the display and cutout stay on the inclined panel after drag, angle and height changes',()=>{
  const state = initialState();
  const lcd = state.parts.find(part => part.id === 'lcd');
  movePart(state,'lcd',[3,2,0]);
  setBox(state,'frontAngle',40);
  setBox(state,'height',95);
  assert.equal(lcd.z,rampMountHeight(state.box,lcd.x));
  const opening=apertures(state).find(entry=>entry.owner==='lcd');
  assert.ok(openingFits(enclosurePanel(state.box,'ramp'),opening));
  assert.equal(opening.face,'ramp');
  assert.equal(opening.center[1],62);
  const first=frontProfile(state.box);
  assert.ok(Math.abs(opening.center[2]-first.frontHeight-opening.center[0]*first.slope)<1e-8);
});
test('the exterior stays solid, with power and switch at the back, one roof vent and inner honeycomb',()=>{
  const state=initialState(),cuts=apertures(state);
  assert.deepEqual(cuts.filter(o=>o.face==='back').map(o=>o.name).sort(),['Interruptor','Paso de corriente']);
  assert.ok(!cuts.some(o=>o.face==='outer'||o.face==='front'||o.recess!==undefined));
  assert.deepEqual(cuts.filter(o=>o.face==='lid').map(o=>o.owner),['fan']);
  const honeycomb=cuts.filter(o=>o.kind==='hexagon');
  assert.ok(honeycomb.length>0);
  assert.ok(honeycomb.every(o=>o.face==='inner'&&state.box.anchors.every(x=>Math.abs(o.center[0]-x)>=19)));
  setBox(state,'length',290);
  assert.equal(state.parts.find(part=>part.id==='switch').x,287);
  assert.ok(apertures(state).filter(o=>o.face==='back').every(o=>o.center[0]===290));
});
test('six clips mount inside both walls and the lid, with no external holes',()=>{
  const state=initialState();
  const clips=state.parts.filter(part=>part.type==='clip');
  for(const face of ['inner','outer','lid']) assert.equal(clips.filter(part=>part.face===face).length,2);
  assert.ok(!apertures(state).some(opening=>opening.owner?.startsWith('clip-')));
  movePart(state,'clip-inner-1',[20,11,4]);
  assert.equal(clips[0].y,state.box.wall);
  assert.ok(apertures(state).filter(opening=>opening.kind==='hexagon')
    .every(opening=>Math.abs(opening.center[0]-clips[0].x)>15 || Math.abs(opening.center[2]-clips[0].z)>15));
  setBox(state,'width',140);
  assert.ok(clips.filter(p=>p.face==='outer').every(p=>p.y===137));
});
test('the four floor bases export screw sockets tied to the moved components',()=>{
  const state=initialState();
  const bases=mountingBases(state);
  assert.deepEqual(bases.map(base=>[base.owner,base.seats.length]),[['pi',4],['mks',4],['mosfet',2],['fuse',2]]);
  assert.equal(bases.find(base=>base.owner==='fuse').kind,'cradle');
  movePart(state,'mks',[7,0,0]);
  const after=exportLayout(state).floorBases.find(base=>base.owner==='mks');
  assert.equal(after.seats[0].center[0],bases[1].seats[0].center[0]+7);
  assert.equal(after.seats[0].center[2],state.box.wall);
});
test('collision test separates a true 3D collision from vertically stacked parts',()=>{
  const s=initialState(),a=s.parts.find(p=>p.id==='mosfet'),b=clone(a);b.id='other';assert.equal(intersects(a,b),true);b.z=a.z+a.size[2]+1;assert.equal(intersects(a,b),false);
  b.z=a.z;b.rotation=45;assert.equal(intersects(a,b),true);
});
test('moving MOSFET into MKS reports a collision without flagging intended driver mounting',()=>{
  const s=initialState(),a=s.parts.find(p=>p.id==='mosfet'),m=s.parts.find(p=>p.id==='mks');a.x=m.x;a.y=m.y;
  assert.ok(validate(s).some(i=>i.severity==='error'&&i.ids.includes('mosfet')&&i.ids.includes('mks')));
  assert.ok(!validate(initialState()).some(i=>i.severity==='error'&&i.ids.includes('driver-x')));
});
test('lowering the lid detects fan-to-heatsink collisions inside the linked Pi assembly',()=>{
  const s=initialState();
  s.parts.find(part=>part.id==='fan').face='lid';
  setBox(s,'height',35);
  assert.ok(validate(s).some(i=>i.severity==='error'&&i.ids.includes('fan')&&i.ids.includes('cooler')));
});
test('long sections and out-of-profile anchors are reported before export',()=>{
  const s=initialState();s.box.split=270;s.box.anchors[1]=370;const issues=validate(s);assert.ok(issues.some(i=>i.text.includes('fuera de los límites de impresión')));assert.ok(issues.some(i=>i.text.includes('apoyo')));
});
test('layout round trip retains dimensions and edits without mutating the active design',()=>{
  const s=initialState();s.box.width=155;s.parts.find(part=>part.id==='pi').x=91;const before=JSON.stringify(s),result=exportLayout(s);assert.equal(JSON.stringify(s),before);assert.equal(result.fabricationReady,false);
  const read=sanitize(JSON.parse(JSON.stringify(result)));assert.deepEqual(read.box,s.box);assert.deepEqual(read.parts,s.parts);assert.ok(result.apertureSchedule.length>=5);
});
test('invalid imports and cyclic or duplicated groups are rejected',()=>{
  assert.throws(()=>sanitize({}));
  const state=initialState(), pi=state.parts.find(part=>part.id==='pi');
  pi.parent='fan';
  assert.throws(()=>sanitize(state),/circular/);
  pi.parent=null;
  state.parts[1].id=state.parts[0].id;
  assert.throws(()=>sanitize(state),/repetidos/);
});
test('custom version 1 layouts retain the flat lid, part poses and connector apertures',()=>{
  const saved = {
    schema:'ft412-control-layout',version:1,box:{length:343,width:132,height:73},
    parts:[{id:'mks',type:'mks',x:132,y:95,z:8,rotation:180}],cutouts:[],
  };
  const s = restoreLayout(saved,{upgradeStock:true});
  assert.equal(s.version,2);
  assert.equal(s.box.length,343);
  assert.equal(s.box.frontRun,0);
  assert.equal(s.box.innerVent,false);
  assert.equal(s.parts[0].x,132);
  const first=apertures(s).find(h=>h.name==='Reserva salida de mazo');
  assert.equal(first.face,'lid');
  assert.ok(first.center.every(Number.isFinite));
  movePart(s,'mks',[10,0,0]);
  assert.equal(apertures(s).find(h=>h.name===first.name).center[0],first.center[0]+10);
});
