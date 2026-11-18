const dot = (a, b) => a.reduce((sum, value, index) => sum + value * b[index], 0);
const radians = angle => angle * Math.PI / 180;

export function frontProfile(box) {
  const run = box.frontRun ?? 0;
  const angle = run > 0 ? (box.frontAngle ?? 0) : 0;
  const sin = Math.sin(radians(angle));
  const cos = Math.cos(radians(angle));
  const slope = sin / cos;
  const rise = run * slope;
  return {
    run, angle, sin, cos, slope, rise,
    enabled: run > 0,
    surfaceLength: run / cos,
    frontHeight: box.height - rise,
    valid: run === 0 || (run <= box.length - box.wall && box.height - rise >= box.wall),
  };
}

export function rampMountHeight(box, x) {
  const {frontHeight, slope, cos} = frontProfile(box);
  return frontHeight + x * slope - box.wall / cos;
}

export function insideRoofHeight(box, x) {
  const front = frontProfile(box);
  const flat = box.height - box.wall;
  return front.enabled && front.valid ? Math.min(flat, rampMountHeight(box, x)) : flat;
}

export function sideOutline(box) {
  const front = frontProfile(box);
  const outline = [[0, 0], [box.length, 0], [box.length, box.height]];
  if (front.enabled && front.valid) {
    outline.push([front.run, box.height], [0, front.frontHeight]);
  } else {
    outline.push([0, box.height]);
  }
  return outline;
}

export function rampAxes(box) {
  const {sin, cos} = frontProfile(box);
  return [[0, 1, 0], [cos, 0, sin], [sin, 0, -cos]];
}

export function enclosurePanel(box, face) {
  const front = frontProfile(box);
  const run = front.enabled && front.valid ? front.run : 0;
  const rectangle = (width, height) => [[0, 0], [width, 0], [width, height], [0, height]];
  switch (face) {
    case 'ramp':
      if (!run) return null;
      return {origin:[0,0,front.frontHeight], axes:rampAxes(box), outline:rectangle(box.width, front.surfaceLength), inward:1};
    case 'front':
      return {origin:[0,0,0], axes:[[0,1,0],[0,0,1],[1,0,0]], outline:rectangle(box.width, run ? front.frontHeight : box.height), inward:1};
    case 'back':
      return {origin:[box.length,0,0], axes:[[0,1,0],[0,0,1],[1,0,0]], outline:rectangle(box.width, box.height), inward:-1};
    case 'inner':
    case 'outer':
      return {origin:[0,face === 'outer' ? box.width : 0,0], axes:[[1,0,0],[0,0,1],[0,-1,0]], outline:sideOutline(box), inward:face === 'outer' ? 1 : -1};
    case 'lid':
      return {origin:[run,0,box.height], axes:[[1,0,0],[0,1,0],[0,0,1]], outline:rectangle(box.length - run, box.width), inward:-1};
    case 'floor':
      return {origin:[0,0,0], axes:[[1,0,0],[0,1,0],[0,0,1]], outline:rectangle(box.length, box.width), inward:1};
    default:
      return null;
  }
}

export function panelPoint(panel, [u, v, depth = 0]) {
  return panel.origin.map((value, i) =>
    value + u * panel.axes[0][i] + v * panel.axes[1][i] + depth * panel.axes[2][i]);
}

export function panelCoordinates(panel, position) {
  const offset = position.map((value, i) => value - panel.origin[i]);
  return panel.axes.slice(0, 2).map(axis => dot(offset, axis));
}

export function openingOutline(panel, opening) {
  const [u, v] = panelCoordinates(panel, opening.center);
  const [halfWidth, halfHeight] = opening.size.map(value => value / 2);
  const angle = radians(opening.rotation ?? 0);
  const cos = Math.cos(angle);
  const sin = Math.sin(angle);
  const sides = opening.kind === 'circle' ? 32 : opening.kind === 'hexagon' ? 6 : 0;
  const outline = sides
    ? Array.from({length:sides}, (_, i) => {
      const a = i * 2 * Math.PI / sides;
      return [halfWidth * Math.cos(a), halfHeight * Math.sin(a)];
    })
    : [[-halfWidth,-halfHeight],[halfWidth,-halfHeight],[halfWidth,halfHeight],[-halfWidth,halfHeight]];
  return outline.map(([x,y]) => [u + x * cos - y * sin, v + x * sin + y * cos]);
}

export function openingFits(panel, opening, margin = 0) {
  if (!panel) return false;
  const outline = openingOutline(panel, opening);
  return panel.outline.every(([x, y], i) => {
    const [nextX, nextY] = panel.outline[(i + 1) % panel.outline.length];
    const dx = nextX - x;
    const dy = nextY - y;
    const minimum = (margin - 0.05) * Math.hypot(dx, dy);
    return outline.every(([u, v]) => dx * (v - y) - dy * (u - x) >= minimum);
  });
}

export function innerVentOpenings(box, mounts = []) {
  if (!box.innerVent) return [];
  const panel = enclosurePanel(box, 'inner');
  const radius = 7;
  const pitch = radius * Math.sqrt(3) + 3;
  const rowHeight = pitch * Math.sqrt(3) / 2;
  const keepouts = mounts.map(mount => {
    const outline = openingOutline(panel, mount);
    return [0,1].map(axis => [
      Math.min(...outline.map(v => v[axis])) - radius - 2,
      Math.max(...outline.map(v => v[axis])) + radius + 2,
    ]);
  });
  const openings = [];
  for (let row = 0, z = 17; z < box.height - 8; row++, z += rowHeight) {
    const start = 13 + (row % 2) * pitch / 2;
    for (let x = start; x < box.length - 8; x += pitch) {
      const reserved = box.anchors.some(anchor => Math.abs(x - anchor) < 19);
      const seam = box.length > box.bed - 10 && Math.abs(x - box.split) < 14;
      const underClip = keepouts.some(([[x0,x1],[z0,z1]]) => x >= x0 && x <= x1 && z >= z0 && z <= z1);
      if (reserved || seam || underClip) continue;
      const opening = {
        name:'Panal de ventilación', face:'inner', center:[x, 0, z],
        size:[2 * radius, 2 * radius], kind:'hexagon', rotation:30, draft:true,
      };
      if (openingFits(panel, opening, 4)) openings.push(opening);
    }
  }
  return openings;
}
