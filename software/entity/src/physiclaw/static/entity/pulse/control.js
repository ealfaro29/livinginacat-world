const $ = (id) => document.getElementById(id);
const es = {
  title: 'Pulso',
  intro: 'Cinco blancos. Entity los busca con la cámara y los toca en el iPhone.',
  heading: 'Control de la toma',
  start: 'Jugar con Entity',
  stop: 'Detener',
  label: 'Aciertos',
  phoneLabel: 'En el iPhone, abrí',
  no_phone: 'Abrí el juego en el iPhone y dejá esa pestaña visible.',
  many: 'Hay dos tableros abiertos. Dejá visible solo el del iPhone que está en la máquina.',
  ready: 'Cuando estés grabando, iniciá la ronda. La cuenta atrás dura tres segundos.',
  busy: 'Ya hay otra tarea en Entity. Esperá a que termine.',
  countdown: 'La ronda está por empezar.',
  playing: 'Entity está buscando el blanco encendido.',
  done: 'El iPhone confirmó los cinco aciertos.',
  stopping: 'Deteniendo la ronda al terminar el toque en curso.',
  stopped: 'Ronda detenida.',
  offline: 'El equipo no está listo. Comprobá la conexión de Entity.',
  lost: 'El iPhone dejó de mostrar esta ronda.',
  vision: 'La cámara no distinguió el blanco. Revisá el encuadre y los reflejos.',
  miss: 'El iPhone no registró el toque dentro del blanco.',
  error: 'No se pudo completar la ronda.',
  manual: 'Hay una ronda manual en curso.',
  again: 'Grabar otra ronda',
};
const en = {
  title: 'Pulse',
  intro: 'Five targets. Entity finds them with its camera and taps them on the iPhone.',
  heading: 'Recording controls',
  start: 'Play with Entity',
  stop: 'Stop',
  label: 'Hits',
  phoneLabel: 'On the iPhone, open',
  no_phone: 'Open the game on the iPhone and keep that tab visible.',
  many: 'Two game screens are open. Keep only the iPhone in the machine visible.',
  ready: 'Start the round when you are recording. The countdown lasts three seconds.',
  busy: 'Entity is busy with another task. Wait for it to finish.',
  countdown: 'The round is about to start.',
  playing: 'Entity is looking for the active target.',
  done: 'The iPhone confirmed all five hits.',
  stopping: 'Stopping after the current tap.',
  stopped: 'Round stopped.',
  offline: 'The machine is not ready. Check the Entity connection.',
  lost: 'The iPhone is no longer showing this round.',
  vision: 'The camera could not identify the target. Check framing and reflections.',
  miss: 'The iPhone did not register a hit on the target.',
  error: 'The round could not finish.',
  manual: 'A manual round is in progress.',
  again: 'Record another round',
};
let lang = new URLSearchParams(location.search).get('lang') === 'en' ? 'en' : 'es',
  state = {},
  pending = false;
function draw() {
  const c = lang === 'es' ? es : en;
  document.documentElement.lang = lang;
  document.title = c.title + ' · Entity';
  for (const k of ['title', 'intro', 'heading', 'stop', 'label', 'phoneLabel'])
    $(k).textContent = c[k];
  $('lang').textContent = lang === 'es' ? 'EN' : 'ES';
  $('explain').textContent = c[state.reason] || c.no_phone;
  $('score').textContent = String(state.hits || 0).padStart(2, '0') + ' / 05';
  $('start').textContent = state.reason === 'done' ? c.again : c.start;
  $('start').disabled = pending || !state.can_start;
  $('stop').hidden = !state.running;
  $('stop').disabled = pending || state.reason === 'stopping';
  if (state.phone_url) {
    $('link').href = state.phone_url + '?lang=' + lang;
    $('link').textContent = state.phone_url;
  }
}
async function sync(action = '') {
  if (action) pending = true;
  draw();
  try {
    const options = action ? { method: 'POST', headers: { 'X-Pulse-Control': '1' } } : {};
    const r = await fetch('/control/' + (action || 'state'), { ...options, cache: 'no-store' });
    state = await r.json();
  } catch {
    state = { reason: 'offline' };
  } finally {
    if (action) pending = false;
    draw();
  }
}
$('start').onclick = () => sync('start');
$('stop').onclick = () => sync('stop');
$('lang').onclick = () => {
  lang = lang === 'es' ? 'en' : 'es';
  draw();
};
await sync();
setInterval(() => {
  if (!pending) sync();
}, 650);
