const lang = document.documentElement.lang;
const words = lang === "en" ? {
  online: "Online", offline: "Offline", yes: "Connected", no: "Disconnected",
  busy: "Connecting…", failed: "Couldn’t connect. Open setup to check the connection.",
  armErrors: {
    arm_usb_missing: "The Raspberry Pi can’t see the MKS. Check the USB cable between them.",
    arm_no_reply: "USB is connected, but the MKS didn’t answer. Check that its 12 V power is on.",
    arm_usb_busy: "Another process is using the MKS. Try again in a few seconds.",
    arm_usb_access: "Entity needs permission to open the MKS USB port on the Raspberry Pi.",
    arm_identity: "The device on this USB port didn’t identify itself as an MKS DLC32.",
    arm_usb_io: "USB communication was interrupted. Try connecting again.",
  },
  select: "Choose your camera in setup.", frame: "Couldn’t get an image. Try again when the camera is free.",
} : {
  online: "En línea", offline: "Sin conexión", yes: "Conectado", no: "Desconectado",
  busy: "Conectando…", failed: "No se pudo conectar. Abrí la configuración para revisar la conexión.",
  armErrors: {
    arm_usb_missing: "La Raspberry no ve la MKS. Revisá el cable USB entre las dos.",
    arm_no_reply: "El USB está conectado, pero la MKS no respondió. Revisá que esté encendida con 12 V.",
    arm_usb_busy: "Otro proceso está usando la MKS. Volvé a intentar en unos segundos.",
    arm_usb_access: "Entity necesita permiso para abrir el puerto USB de la MKS en la Raspberry.",
    arm_identity: "El dispositivo en ese puerto USB no se identificó como una MKS DLC32.",
    arm_usb_io: "Se interrumpió la comunicación por USB. Volvé a conectar desde el panel.",
  },
  select: "Elegí la cámara en la configuración.", frame: "No se pudo obtener la imagen. Probá cuando la cámara esté libre.",
};
const el = id => document.getElementById(id);
const view = el("view-camera");
const frame = el("frame");
const figure = el("camera-view");
const busy = new Set();
let groupConnecting = false;
let latestHardware = null;
let polling = false;
let online = false;
let frameRequest = 0;
let connectionErrors = [];

async function call(path, options = {}) {
  const response = await fetch(path, { cache: "no-store", ...options });
  if (response.status === 401) {
    location.replace("/?lang=" + lang);
    throw new Error("login");
  }
  const result = await response.json();
  if (!response.ok || result.status === "error") throw new Error(result.error || "request");
  return result;
}
function notice(message = "") {
  connectionErrors = [];
  el("feedback").textContent = message;
  el("feedback").hidden = !message;
}
function showConnectionErrors(errors, hardware) {
  const pending = errors.filter(([id]) => !hardware?.[id]);
  notice(pending.map(([, message]) => message).join(" "));
  connectionErrors = pending;
}
function closeCamera() {
  frameRequest++;
  figure.hidden = true;
  frame.removeAttribute("src");
  frame.hidden = true;
  view.textContent = view.dataset.open;
}
async function readFrame() {
  const id = ++frameRequest;
  el("refresh-frame").disabled = true;
  try {
    const result = await call("/operator/camera");
    if (id !== frameRequest) return;
    if (typeof result.image !== "string" || !result.image.length) throw new Error("frame");
    frame.src = "data:image/jpeg;base64," + result.image;
    frame.hidden = false;
    notice();
  } catch (error) {
    if (id === frameRequest) notice(error.message === "select_camera" ? words.select : words.frame);
  } finally {
    if (id === frameRequest) el("refresh-frame").disabled = false;
  }
}
function render(hardware) {
  latestHardware = hardware;
  online = Boolean(hardware);
  const all = el("connect-all");
  all.disabled = !online || groupConnecting || busy.size > 0 || (hardware.arm && hardware.camera);
  all.textContent = groupConnecting ? words.busy : hardware?.arm && hardware?.camera
    ? (lang === "es" ? "Equipo conectado" : "Equipment connected") : (lang === "es" ? "Conectar equipo" : "Connect equipment");
  el("connection").textContent = online ? words.online : words.offline;
  el("connection").classList.toggle("online", online);
  el("offline-note").hidden = online;
  const phoneHelp = el("phone-help");
  if (phoneHelp) phoneHelp.hidden = !online || hardware.bridge;
  for (const [id, key] of [["arm", "arm"], ["camera", "camera"], ["phone", "bridge"]]) {
    const connected = Boolean(hardware?.[key]);
    let status = connected ? words.yes : words.no;
    if (lang === "es" && id === "camera") status = connected ? "Conectada" : "Desconectada";
    el(id + "-state").textContent = online ? status : "—";
    const button = el(id + "-btn");
    if (button) {
      button.disabled = !online || connected || groupConnecting || busy.has(id);
      button.hidden = online && connected;
    }
  }
  for (const link of document.querySelectorAll(".device-link")) link.setAttribute("aria-disabled", String(!online));
  view.disabled = !online;
  if (!online && !figure.hidden) closeCamera();
  if (connectionErrors.some(([id]) => hardware?.[id])) showConnectionErrors(connectionErrors, hardware);
}
async function poll() {
  if (polling || document.hidden) return;
  polling = true;
  try {
    const state = await call("/entity/state");
    render(state.hardware && typeof state.hardware.arm === "boolean" ? state.hardware : null);
  } catch { render(null); }
  finally { polling = false; }
}
async function requestConnection(id) {
  const path = id === "arm" ? "/api/connect-arm" : "/operator/connect-camera";
  return call(path, { method: "POST", headers: { "Content-Type": "application/json" }, body: "{}" });
}
async function connect(ids, group = false) {
  if (!online || groupConnecting || busy.size) return;
  groupConnecting = group;
  const errors = [];
  const pending = ids.filter(id => !latestHardware?.[id]);
  for (const id of pending) busy.add(id);
  render(latestHardware);
  notice(words.busy);
  try {
    for (const id of pending) {
      try { await requestConnection(id); }
      catch (err) {
        const label = id === "arm" ? (lang === "es" ? "Brazo MKS" : "MKS arm") : (lang === "es" ? "Cámara" : "Camera");
        const detail = id === "arm" && Object.hasOwn(words.armErrors, err.message)
          ? words.armErrors[err.message] : err.message === "select_camera" ? words.select : words.failed;
        errors.push([id, label + " · " + detail]);
      }
    }
  } finally {
    busy.clear();
    groupConnecting = false;
    render(latestHardware);
    await poll();
    showConnectionErrors(errors, latestHardware);
  }
}
for (const id of ["arm", "camera"]) el(id + "-btn").addEventListener("click", () => connect([id]));
el("connect-all").addEventListener("click", () => connect(["arm", "camera"], true));
el("pair-form").addEventListener("submit", async event => {
  event.preventDefault();
  const button = event.currentTarget.querySelector("button");
  const box = el("pair-code");
  const result = el("pair-result");
  button.disabled = true;
  try {
    await call("/operator/pair-phone", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ code: box.value }) });
    box.value = "";
    result.textContent = lang === "es" ? "Código aceptado. Dejá el ícono abierto en el iPhone." : "Code accepted. Leave the app open on the iPhone.";
    await poll();
  } catch (err) {
    result.textContent = err.message === "invalid_code"
      ? (lang === "es" ? "Revisá el código que aparece ahora en el iPhone." : "Check the code currently shown on the iPhone.")
      : (lang === "es" ? "Volvé a intentar en un momento." : "Please try again shortly.");
  } finally { button.disabled = false; }
});
for (const link of document.querySelectorAll(".device-link")) {
  link.addEventListener("click", event => { if (!online) event.preventDefault(); });
}
view.addEventListener("click", () => {
  if (!figure.hidden) return closeCamera();
  figure.hidden = false;
  view.textContent = view.dataset.close;
  readFrame();
});
el("refresh-frame").addEventListener("click", readFrame);
document.addEventListener("visibilitychange", poll);
window.addEventListener("online", poll);
poll();
setInterval(poll, 5000);
