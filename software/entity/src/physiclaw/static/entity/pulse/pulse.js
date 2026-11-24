const $ = (id) => document.getElementById(id);
const copy = {
  es: {
    title: 'Pulso',
    instructions: 'Tocá los cinco blancos al encenderse.',
    hits: 'Aciertos',
    time: 'Tiempo',
    arena: 'Tablero',
    target: 'Blanco',
    ready: 'Listo para jugar',
    manual: 'Jugar a mano',
    stop: 'Detener',
    again: 'Jugar de nuevo',
    go: 'Prepará la toma',
    playing: 'Ronda en curso',
    hit: 'Acierto',
    miss: 'Fuera del blanco',
    won: 'Ronda completa',
    stopped: 'Ronda detenida',
    misses: 'Toques fuera',
    next: 'Blanco',
  },
  en: {
    title: 'Pulse',
    instructions: 'Tap all five targets as they light up.',
    hits: 'Hits',
    time: 'Time',
    arena: 'Playfield',
    target: 'Target',
    ready: 'Ready to play',
    manual: 'Play by hand',
    stop: 'Stop',
    again: 'Play again',
    go: 'Get ready',
    playing: 'Round in progress',
    hit: 'Hit',
    miss: 'Off target',
    won: 'Round complete',
    stopped: 'Round stopped',
    misses: 'Misses',
    next: 'Target',
  },
};
const positions = [
  [16, 16],
  [84, 16],
  [50, 50],
  [16, 84],
  [84, 84],
];
const initialLanguage = new URLSearchParams(location.search).get('lang');
let lang = initialLanguage === 'en' ? 'en' : 'es';
let phase = 'ready',
  hits = 0,
  misses = 0,
  order = [],
  started = 0,
  elapsed = 0;
let round = '',
  mode = 'manual',
  lastCommand = '',
  statusKey = 'ready',
  countdown = 0;
let advanceTimer,
  countTimer,
  accepting = false;
const paired = location.pathname.replace(/\/$/, '') === '/jugar';
const randomId = () =>
  Array.from(crypto.getRandomValues(new Uint8Array(12)), (b) =>
    b.toString(16).padStart(2, '0'),
  ).join('');
const client = randomId();
const pad = (n) => String(n).padStart(2, '0');
const timeText = (ms) => {
  const s = Math.floor(ms / 1000);
  return pad(Math.floor(s / 60)) + ':' + pad(s % 60);
};
for (const top of [16, 50, 84])
  for (const left of [16, 50, 84]) {
    const pin = document.createElement('i');
    pin.style.left = left + '%';
    pin.style.top = top + '%';
    $('pins').append(pin);
  }
function place(el, point) {
  el.style.left = point[0] + '%';
  el.style.top = point[1] + '%';
}
function draw() {
  const c = copy[lang];
  document.documentElement.lang = lang;
  document.title = c.title + ' · Entity by Sentient';
  $('game').dataset.phase = phase;
  $('title').textContent = c.title;
  $('instruction').textContent = c.instructions;
  $('lang').textContent = lang === 'es' ? 'EN' : 'ES';
  $('lang').lang = lang === 'es' ? 'en' : 'es';
  $('arena').setAttribute('aria-label', c.arena);
  $('hitsLabel').textContent = c.hits;
  $('timeLabel').textContent = c.time;
  $('hits').firstChild.textContent = pad(hits);
  $('clock').textContent = timeText(elapsed);
  [...$('progress').children].forEach((e, i) => e.classList.toggle('lit', i < hits));
  const busy = phase === 'playing' || phase === 'countdown';
  $('play').textContent = busy ? c.stop : phase === 'ready' ? c.manual : c.again;
  $('play').className = busy ? 'secondary' : 'primary';
  $('overlay').hidden = phase === 'playing' || phase === 'ready';
  $('target').hidden = phase !== 'ready' && !(phase === 'playing' && accepting);
  $('target').setAttribute('aria-label', c.target + ' ' + (hits + 1));
  if (phase === 'ready') place($('target'), [50, 50]);
  if (phase === 'playing' && hits < positions.length)
    place($('target'), positions[order[hits]]);
  $('overlayLabel').textContent =
    phase === 'countdown' ? c.go : phase === 'won' ? c.won : c.stopped;
  $('overlayNumber').textContent = phase === 'countdown' ? String(countdown) : hits + '/5';
  $('overlayDetail').textContent =
    phase === 'countdown'
      ? ''
      : c.time + ' ' + timeText(elapsed) + ' · ' + c.misses + ' ' + misses;
  $('status').textContent = c[statusKey] || c.ready;
}
function end(nextPhase) {
  clearInterval(countTimer);
  clearTimeout(advanceTimer);
  if (phase === 'playing') elapsed = performance.now() - started;
  accepting = false;
  phase = nextPhase;
  statusKey = phase === 'won' ? 'won' : 'stopped';
  draw();
  report();
}
function start(id, source) {
  if (phase === 'playing' || phase === 'countdown') return;
  order = positions.map((_, i) => i);
  for (let i = order.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [order[i], order[j]] = [order[j], order[i]];
  }
  round = id;
  mode = source;
  hits = 0;
  misses = 0;
  elapsed = 0;
  phase = 'countdown';
  countdown = 3;
  statusKey = 'go';
  accepting = false;
  draw();
  report();
  const deadline = performance.now() + 3000;
  countTimer = setInterval(() => {
    countdown = Math.ceil((deadline - performance.now()) / 1000);
    if (countdown <= 0) {
      clearInterval(countTimer);
      phase = 'playing';
      statusKey = 'playing';
      started = performance.now();
      accepting = true;
      draw();
      report();
    } else if ($('overlayNumber').textContent !== String(countdown)) draw();
  }, 75);
}
function hit() {
  const spot = positions[order[hits]];
  accepting = false;
  hits++;
  statusKey = 'hit';
  place($('echo'), spot);
  $('echo').classList.remove('pop');
  void $('echo').offsetWidth;
  $('echo').classList.add('pop');
  if (hits === positions.length) {
    end('won');
    return;
  }
  draw();
  report();
  advanceTimer = setTimeout(() => {
    if (phase === 'playing') {
      accepting = true;
      draw();
      report();
    }
  }, 350);
}
$('arena').addEventListener('pointerdown', (e) => {
  if (!e.isTrusted || !e.isPrimary || e.button !== 0 || phase !== 'playing' || !accepting)
    return;
  e.preventDefault();
  const r = $('target').getBoundingClientRect();
  if (
    Math.hypot(e.clientX - r.x - r.width / 2, e.clientY - r.y - r.height / 2) <=
    r.width / 2
  ) {
    hit();
  } else {
    misses++;
    statusKey = 'miss';
    draw();
    report();
  }
});
$('target').addEventListener('click', (e) => {
  if (e.isTrusted && e.detail === 0 && phase === 'playing' && accepting) hit();
});
$('lang').onclick = () => {
  lang = lang === 'es' ? 'en' : 'es';
  draw();
};
$('play').onclick = () => {
  if (phase === 'playing' || phase === 'countdown') end('stopped');
  else start(randomId(), 'manual');
};
setInterval(() => {
  if (phase === 'playing') {
    elapsed = performance.now() - started;
    $('clock').textContent = timeText(elapsed);
  }
}, 200);
let reporting = false,
  dirty = false;
async function report() {
  if (!paired) return;
  if (reporting) {
    dirty = true;
    return;
  }
  reporting = true;
  try {
    const response = await fetch('/api/phone', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      cache: 'no-store',
      body: JSON.stringify({
        client,
        round,
        phase,
        hits,
        misses,
        visible: !document.hidden,
        accepting,
        mode,
        lang,
      }),
    });
    if (response.status === 401 && location.protocol === 'https:') {
      location.replace('/?next=%2Fjugar&lang=' + (lang === 'en' ? 'en' : 'es'));
      return;
    }
    if (response.ok) {
      const cmd = await response.json();
      if (cmd.start && cmd.start !== lastCommand && !document.hidden) {
        lastCommand = cmd.start;
        start(cmd.start, 'entity');
      }
      if (cmd.stop && cmd.stop === round && (phase === 'playing' || phase === 'countdown'))
        end('stopped');
    }
  } catch (_) {
  } finally {
    reporting = false;
    if (dirty) {
      dirty = false;
      setTimeout(report, 0);
    }
  }
}
document.addEventListener('visibilitychange', () => {
  if (document.hidden && (phase === 'playing' || phase === 'countdown')) end('stopped');
  else report();
});
draw();
if (paired) {
  report();
  setInterval(report, 550);
}
