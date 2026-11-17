import test from 'node:test';
import assert from 'node:assert/strict';
import {initialState,clone,bounds,intersects,movePart,rotatePart,setBox,validate,sanitize,exportLayout,apertures} from '../tools/control-pod-designer/model.mjs';

test('side module begins at full 355 mm with physically unconfirmed envelopes and two print sections',()=>{
  const s=initialState();assert.equal(s.box.length,355);assert.equal(s.parts.length,10);assert.ok(s.parts.every(p=>!p.verified));
  assert.equal(s.box.split,177.5);assert.ok(!validate(s).some(i=>i.severity==='error'));
});
test('moving Pi moves its cooler and lid fan, while raising Pi retains fan on the lid',()=>{
  const s=initialState(),before=clone(s);movePart(s,'pi',[-10,-5,7]);
  for(const id of ['pi','cooler','fan']){const a=before.parts.find(p=>p.id===id),b=s.parts.find(p=>p.id===id);assert.equal(b.x,a.x-10);assert.equal(b.y,a.y-5);assert.equal(b.z,a.z+(id==='fan'?0:7));}
  setBox(s,'height',90);assert.equal(s.parts.find(p=>p.id==='fan').z,87);
});
test('MKS rotation carries both drivers around the board and preserves their radial offsets',()=>{
  const s=initialState(),m=s.parts.find(p=>p.id==='mks');const drivers=s.parts.filter(p=>p.parent==='mks').map(p=>({id:p.id,r:Math.hypot(p.x-m.x,p.y-m.y)}));
  rotatePart(s,'mks',90);for(const d of drivers){const p=s.parts.find(p=>p.id===d.id);assert.ok(Math.abs(Math.hypot(p.x-m.x,p.y-m.y)-d.r)<.2);assert.equal(p.rotation,270);}
  const b=bounds(m);assert.equal(Math.round(b.max[0]-b.min[0]),70);assert.equal(Math.round(b.max[1]-b.min[1]),90);
});
test('front screen uses Y for width, Z for height and positive X for connector depth',()=>{
  const lcd=initialState().parts.find(p=>p.id==='lcd'),b=bounds(lcd);
  assert.deepEqual(b.min,[3,48,14]);assert.deepEqual(b.max,[18,128,64]);
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
  const s=initialState();setBox(s,'height',35);assert.ok(validate(s).some(i=>i.severity==='error'&&i.ids.includes('fan')&&i.ids.includes('cooler')));
});
test('long sections and out-of-profile anchors are reported before export',()=>{
  const s=initialState();s.box.split=270;s.box.anchors[1]=370;const issues=validate(s);assert.ok(issues.some(i=>i.text.includes('demasiado larga')));assert.ok(issues.some(i=>i.text.includes('apoyo')));
});
test('layout round trip retains dimensions and edits without mutating the active design',()=>{
  const s=initialState();s.box.width=155;s.parts[0].x=301;const before=JSON.stringify(s),result=exportLayout(s);assert.equal(JSON.stringify(s),before);assert.equal(result.fabricationReady,false);
  const read=sanitize(JSON.parse(JSON.stringify(result)));assert.deepEqual(read.box,s.box);assert.deepEqual(read.parts,s.parts);assert.ok(result.apertureSchedule.length>=5);
});
test('invalid imports and cyclic or duplicated groups are rejected',()=>{
  assert.throws(()=>sanitize({}));const s=initialState();s.parts[0].parent='fan';assert.throws(()=>sanitize(s),/circular/);s.parts[0].parent=null;s.parts[1].id=s.parts[0].id;assert.throws(()=>sanitize(s),/repetidos/);
});
test('lid cable reservations have finite coordinates and follow the control board',()=>{
  const s=initialState(),first=apertures(s).find(h=>h.name==='Reserva salida de mazo');assert.equal(first.face,'lid');assert.ok(first.center.every(Number.isFinite));movePart(s,'mks',[10,0,0]);const moved=apertures(s).find(h=>h.name===first.name);assert.equal(moved.center[0],first.center[0]+10);
});
