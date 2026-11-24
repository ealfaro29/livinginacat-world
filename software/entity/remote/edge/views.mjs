const copy = {
  es: {
    title: "Acceso a Alfonsito", user: "Usuario", password: "Contraseña", enter: "Entrar",
    wrong: "Revisá el usuario y la contraseña.", rate: "Esperá un minuto antes de volver a intentar.",
    retry: "Volvé a ingresar con este formulario.",
    unavailable: "El acceso no está disponible en este momento.", logout: "Cerrar sesión", switch: "English",
    status: "Conectando…", offline: "Sin conexión", hardware: "Conexiones", arm: "Brazo MKS", camera: "Cámara",
    phone: "iPhone", connect: "Conectar", view: "Ver cámara", cameraOptions: "Opciones de cámara", setup: "Calibrar", panel: "Tarea y cola",
    pulse: "Abrir Pulso", hide: "Cerrar cámara", refresh: "Actualizar imagen", next: "Cuando prendás la Raspberry, esta página se reconectará sola.",
    phoneHelp: "Abrí el enlace del iPhone en Safari y dejá la página visible en Alfonsito. Podés usar Wi-Fi o datos móviles.",
    groupConnect: "Conectar equipo", pair: "Vincular iPhone", pairHelp: "Escaneá el QR con el iPhone de la máquina y agregá Alfonsito a Inicio. Abrí el ícono y escribí acá el código que aparece.", code: "Código del iPhone",
    phoneLink: "Enlace para el iPhone", shortcuts: "Atajos del iPhone", retryPhone: "Volver a conectar", offlinePhone: "Alfonsito está sin conexión. Encendé la Raspberry y volvé a conectar.",
  },
  en: {
    title: "Sign in to Alfonsito", user: "Username", password: "Password", enter: "Sign in",
    wrong: "Check your username and password.", rate: "Wait a minute before trying again.",
    retry: "Please sign in again using this form.",
    unavailable: "Sign-in is currently unavailable.", logout: "Sign out", switch: "Español",
    status: "Connecting…", offline: "Offline", hardware: "Connections", arm: "MKS arm", camera: "Camera",
    phone: "iPhone", connect: "Connect", view: "View camera", cameraOptions: "Camera settings", setup: "Calibrate", panel: "Task and queue",
    pulse: "Open Pulse", hide: "Close camera", refresh: "Refresh image", next: "When you power on the Raspberry Pi, this page reconnects automatically.",
    phoneHelp: "Open the iPhone link in Safari and leave the page visible on Alfonsito. Wi-Fi and mobile data both work.",
    groupConnect: "Connect equipment", pair: "Pair iPhone", pairHelp: "Scan the QR with the mounted iPhone and add Alfonsito to its Home Screen. Open the icon and enter the code it shows.", code: "iPhone code",
    phoneLink: "iPhone link", shortcuts: "iPhone shortcuts", retryPhone: "Reconnect", offlinePhone: "Alfonsito is offline. Power on the Raspberry Pi, then reconnect.",
  },
};
export const phoneHead = `<link rel="manifest" href="/ui/iphone.webmanifest"><link rel="apple-touch-icon" sizes="180x180" href="/ui/alfonsito-180.png">
  <meta name="apple-mobile-web-app-title" content="Alfonsito"><meta name="apple-mobile-web-app-capable" content="yes">
  <meta name="mobile-web-app-capable" content="yes"><meta name="theme-color" content="#10130f">`;
function shell(lang, content, signedIn, next = "/", script = signedIn ? "/ui/portal.js" : "") {
  const t = copy[lang];
  const other = lang === "es" ? "en" : "es";
  return `<!doctype html><html lang="${lang}"><head><meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1"><meta name="color-scheme" content="dark">
    ${["/iphone", "/bridge", "/jugar"].includes(next) ? phoneHead : ""}
    <title>Alfonsito · Entity by Sentient</title><link rel="icon" href="/ui/sentient.svg">
    <link rel="stylesheet" href="/ui/portal.css">${script ? `<script type="module" src="${script}"></script>` : ""}
    </head><body><header><a class="brand" href="/?lang=${lang}" aria-label="${lang === "es" ? "Inicio de Entity" : "Entity dashboard"}"><img src="/ui/sentient.svg" alt=""><strong>Entity</strong><span>by Sentient</span></a>
    <nav><a hreflang="${other}" href="/?lang=${other}&amp;next=${encodeURIComponent(next)}">${t.switch}</a>
    ${signedIn ? `<form method="post" action="/auth/logout?lang=${lang}"><button class="text" type="submit">${t.logout}</button></form>` : ""}</nav></header>
    ${content}</body></html>`;
}
export function loginPage(lang, next = "/", message = "") {
  const t = copy[lang];
  return shell(lang, `<main class="login"><a class="back-link" href="https://livinginacat.world/${lang === "es" ? "es/" : ""}">← ${lang === "es" ? "Volver al proyecto" : "Back to project"}</a><img class="login-mark" src="/ui/sentient.svg" alt="">
    <h1>${t.title}</h1><form method="post" action="/auth/login?lang=${lang}&amp;next=${encodeURIComponent(next)}">
    <label>${t.user}<input name="username" autocomplete="username" autocapitalize="none" spellcheck="false" required maxlength="64"></label>
    <label>${t.password}<input name="password" type="password" autocomplete="current-password" required maxlength="256"></label>
    ${message ? `<p class="notice" role="alert">${t[message]}</p>` : ""}
    <button class="primary" type="submit">${t.enter}<span aria-hidden="true">→</span></button></form></main>`, false, next);
}
export function homePage(lang, offline = false) {
  const t = copy[lang];
  const q = "?lang=" + lang;
  const row = (id, title, button = "") => `<div class="device"><b>${title}</b><span id="${id}-state">—</span>${button ? `<button id="${id}-btn" class="small" disabled>${button}</button>` : ""}</div>`;
  return shell(lang, `<main class="home"><a class="back-link" href="https://livinginacat.world/${lang === "es" ? "es/" : ""}">← ${lang === "es" ? "Volver al proyecto" : "Back to project"}</a><section class="home-head"><h1>Alfonsito</h1><span id="connection" class="pill" role="status">${offline ? t.offline : t.status}</span></section>
    <p id="offline-note" ${offline ? "" : "hidden"}>${t.next}</p>
    <section class="devices"><h2>${t.hardware}</h2>${row("arm", t.arm, t.connect)}${row("camera", t.camera, t.connect)}${row("phone", t.phone)}</section>
    <details class="pair-box"><summary>${t.pair}</summary><div class="pair-layout"><img width="148" height="148" src="/ui/iphone-qr.png" alt="QR · Alfonsito"><form id="pair-form"><label>${t.pairHelp}
      <input id="pair-code" type="text" inputmode="numeric" autocomplete="off" aria-label="${t.code}" maxlength="12" placeholder="0000 0000" required></label>
      <button class="small" type="submit">${t.pair}</button><span id="pair-result" role="status"></span></form></div></details>
    <p class="phone-links"><a href="/iphone${q}" target="_blank" rel="noopener">${t.phoneLink}</a><a href="/atajos${q}">${t.shortcuts}</a></p>
    <p id="phone-help" hidden>${t.phoneHelp}</p><p id="feedback" class="notice" role="status" hidden></p>
    <div class="tools"><button type="button" class="primary" id="connect-all" disabled>${t.groupConnect}</button><a class="tool device-link" href="/setup-hardware${q}&amp;calibrate=1">${t.setup}<span aria-hidden="true">↗</span></a>
      <a class="tool" href="/tareas${q}">${t.panel}</a><a class="tool device-link" href="/control${q}">${t.pulse}</a>
      <button class="tool" id="view-camera" data-open="${t.view}" data-close="${t.hide}" disabled>${t.view}</button>
      <a class="tool" href="/camara${q}">${t.cameraOptions}</a></div>
    <figure id="camera-view" hidden><img id="frame" alt="${t.camera}" hidden><button type="button" class="small" id="refresh-frame">${t.refresh}</button></figure>
    </main>`, true);
}

export function tasksPage(lang) {
  const es = lang === "es";
  return shell(lang, `<main class="tasks-page"><a class="back-link" href="/?lang=${lang}">← ${es ? "Volver al inicio" : "Back to dashboard"}</a>
    <h1>${es ? "Tareas y cola" : "Tasks and queue"}</h1>
    <form id="composer"><label for="instructions">${es ? "¿Qué querés que haga Alfonsito?" : "What should Alfonsito do?"}</label>
      <textarea id="instructions" maxlength="2000" rows="3" required placeholder="${es ? "Abrí la calculadora y multiplicá 89 por 90." : "Open Calculator and multiply 89 by 90."}"></textarea>
      <div class="queue-timing"><label>${es ? "Cuándo" : "When"}<select id="timing"><option value="now">${es ? "Cuando le toque" : "Next available turn"}</option><option value="later">${es ? "Programar para después" : "Schedule for later"}</option></select></label>
      <label id="schedule-field" hidden>${es ? "Fecha y hora" : "Date and time"}<input id="scheduled" type="datetime-local"><small id="zone"></small></label></div>
      <button id="submit-task" class="primary" type="submit" disabled>${es ? "Agregar a la cola" : "Add to queue"}</button>
      <span id="task-feedback" role="status"></span></form>
    <p id="task-connection" class="notice" role="status"></p>
    <section class="queue-section"><h2>${es ? "En curso" : "Running"}</h2><div id="current-task"></div></section>
    <section class="queue-section"><h2>${es ? "Pendientes" : "Waiting"}</h2><ol id="waiting-tasks"></ol><p id="empty-queue">${es ? "La cola está vacía." : "The queue is empty."}</p></section>
    <section class="queue-section" id="last-section" hidden><h2>${es ? "Último resultado" : "Last result"}</h2><div id="last-task"></div></section>
    <a class="back-link" href="/entity/?lang=${lang}">${es ? "Ver pantalla MKS" : "View MKS display"} →</a>
    </main>`, true, "/tareas", "/ui/tasks.js");
}

export function cameraPage(lang) {
  const es = lang === "es";
  return shell(lang, `<main class="camera-page">
    <a class="back-link" href="/?lang=${lang}">← ${es ? "Volver al inicio" : "Back to dashboard"}</a>
    <h1>${copy[lang].cameraOptions}</h1>
    <div class="camera-layout"><section class="preview-column" aria-labelledby="preview-title">
      <div class="camera-heading"><h2 id="preview-title">${es ? "Vista en vivo" : "Live view"}</h2><span id="live-state" class="pill" role="status">${es ? "Conectando…" : "Connecting…"}</span></div>
      <div class="camera-stage"><div class="camera-picture" id="picture"><img id="live-image" alt="${es ? "Vista desde la cámara de Alfonsito" : "View from Alfonsito’s camera"}" hidden></div>
        <span id="frame-note">${es ? "Esperando imagen…" : "Waiting for an image…"}</span></div>
      <div class="camera-actions"><button class="small" type="button" id="pause">${es ? "Pausar vista" : "Pause preview"}</button>
        <label class="grid-switch"><input type="checkbox" id="grid">${es ? "Cuadrícula" : "Grid"}</label></div>
      <p class="camera-meta" id="device-meta"></p>
    </section><section class="image-column" aria-labelledby="image-title">
      <h2 id="image-title">${es ? "Ajustes de imagen" : "Image settings"}</h2>
      <p id="setting-help" class="camera-help"></p>
      <fieldset id="controls" disabled aria-labelledby="image-title"></fieldset>
      <p id="control-status" class="control-status" role="status"></p>
      <button type="button" class="small" id="cam-connect" hidden>${es ? "Conectar cámara" : "Connect camera"}</button>
      <section id="optics" class="optics" hidden><h3>${es ? "Enfoque y exposición" : "Focus and exposure"}</h3>
        <p class="camera-help">${es ? "Entity ajusta estos valores durante la calibración." : "Entity adjusts these values during calibration."}</p><dl id="optics-values"></dl>
      </section>
    </section></div></main>`, true, "/camara", "/ui/camera.js");
}

export function phoneOfflinePage(lang, path) {
  const t = copy[lang];
  return shell(lang, `<main class="home"><h1>Alfonsito</h1><p>${t.offlinePhone}</p>
    <a class="primary" href="${path}?lang=${lang}">${t.retryPhone}</a></main>`, true, path, "/ui/reconnect.js");
}

export function shortcutsPage(lang) {
  const es = lang === "es";
  const t = copy[lang];
  const title = es ? "Atajos del iPhone" : "iPhone shortcuts";
  const intro = es
    ? "Los dos atajos usan entity.livinginacat.world aunque reiniciés Alfonsito o cambiés de Wi-Fi. En el iPhone, abrí cada atajo y revisá la URL y el encabezado en «Obtener contenido de URL»."
    : "Both shortcuts use entity.livinginacat.world across restarts and Wi-Fi changes. On the iPhone, open each shortcut and check the URL and header in Get Contents of URL.";
  const rows = [
    ["screenshot", "PhysiClaw Upload Screenshot", "POST", es ? "Mantené «Tomar captura de pantalla» antes de la solicitud. En «Cuerpo de la solicitud», elegí «Archivo» y seleccioná esa captura." : "Keep Take Screenshot before the request. Under Request Body, choose File and select that screenshot."],
    ["clipboard", "PhysiClaw Clipboard", "GET", es ? "Después de la solicitud, dejá «Copiar al portapapeles» conectado al resultado." : "After the request, keep Copy to Clipboard connected to its result."],
  ];
  const cards = rows.map(([kind, name, method, instructions]) => `<section class="shortcut-card"><h2>${name}</h2>
    <p><b>${es ? "Método" : "Method"}</b> ${method}</p><label>URL<input value="https://entity.livinginacat.world/api/bridge/${kind}" readonly></label>
    <button type="button" class="small" data-copy-url>${es ? "Copiar URL" : "Copy URL"}</button>
    <p>${es ? "En «Encabezados», agregá" : "Under Headers, add"} <code>Authorization</code>. ${es ? "Pegá como valor la autorización de este atajo." : "Paste this shortcut’s authorization as its value."}</p>
    <button type="button" class="small" data-credential="${kind}">${es ? "Copiar autorización" : "Copy authorization"}</button>
    <input class="copy-fallback" aria-label="${es ? "Valor para copiar" : "Value to copy"}" readonly hidden>
    <p class="copy-status" role="status"></p><p>${instructions}</p>
    <a href="shortcuts://open-shortcut?name=${encodeURIComponent(name)}">${es ? "Abrir este atajo en Atajos" : "Open this shortcut in Shortcuts"}</a></section>`).join("");
  return shell(lang, `<main class="home"><a class="back-link" href="/?lang=${lang}">← ${es ? "Volver al inicio" : "Back to dashboard"}</a><h1>${title}</h1><p>${intro}</p>${cards}
    <a class="primary" href="/iphone?lang=${lang}">${t.phoneLink}</a></main>`, true, "/atajos", "/ui/shortcuts.js");
}

export function phonePairPage(lang) {
  const es = lang === "es";
  return shell(lang, `<main class="home phone-pair"><h1>Alfonsito</h1>
    <p id="install-hint">${es ? "En Safari, tocá Compartir → Agregar a Inicio. Después abrí Alfonsito desde el nuevo ícono." : "In Safari, tap Share → Add to Home Screen. Then open Alfonsito using its new icon."}</p>
    <h2>${es ? "Vinculá este iPhone" : "Pair this iPhone"}</h2>
    <p>${es ? "Desde otro equipo, iniciá sesión en el panel de Entity, elegí «Vincular iPhone» y escribí este código." : "On another device, sign in to the Entity dashboard, choose “Pair iPhone”, and enter this code."}</p>
    <output id="pair-code" class="pair-code" aria-label="${es ? "Código de vinculación" : "Pairing code"}">—</output>
    <p id="pair-message" role="status"></p><a href="/?lang=${lang}&amp;next=%2Fiphone">${es ? "O iniciar sesión en este iPhone" : "Or sign in on this iPhone"}</a></main>`, false, "/iphone", "/ui/iphone-pair.js");
}
