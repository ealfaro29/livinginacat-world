const lang = document.documentElement.lang;
const es = lang === "es";
const t = (spanish, english) => es ? spanish : english;
const el = id => document.getElementById(id);
const labels = {
  brightness: t("Brillo", "Brightness"), contrast: t("Contraste", "Contrast"),
  saturation: t("Saturación", "Saturation"), sharpness: t("Nitidez", "Sharpness"),
  power_line_frequency: t("Antiparpadeo", "Anti-flicker"),
};
const frequencies = [t("Desactivado", "Off"), "50 Hz", "60 Hz", t("Automático", "Automatic")];
const errors = {
  camera_offline: t("La cámara está desconectada.", "The camera is disconnected."),
  device_offline: t("Alfonsito está sin conexión.", "Alfonsito is offline."),
  camera_busy: t("La cámara está ocupada. Volvé a intentar cuando termine la operación.", "The camera is busy. Try again when the operation finishes."),
  task_active: t("Podés cambiar la imagen cuando termine la tarea.", "You can adjust the image once the task finishes."),
  settings_changed: t("Los valores cambiaron. Revisá el valor actual y volvé a aplicar el ajuste.", "Settings changed. Check the current value and apply your change again."),
  controls_unavailable: t("El controlador de la cámara no ofrece estos ajustes en este momento.", "The camera driver is not providing image controls right now."),
  preset_unavailable: t("No se pudo guardar el ajuste en la Raspberry.", "Could not save the setting on the Raspberry Pi."),
  setting_rejected: t("La cámara no confirmó el ajuste.", "The camera did not confirm the setting."),
  select_camera: t("Elegí la cámara en la configuración de Alfonsito.", "Choose the camera in Alfonsito setup."),
};
const endpoint = "/entity/api/camera/";
const controls = el("controls");
const image = el("live-image");
let state = null;
let schema = "";
let writing = false;
let loading = false;
let revision = 0;
let paused = false;
let leaving = false;
let timer;
let inFlight;
let imageUrl;
let lastNotice = "";
let lastFrameError = "";

async function request(path, options = {}) {
  const response = await fetch(path, {cache: "no-store", ...options});
  if (response.status === 401) {
    location.replace("/?lang=" + lang + "&next=%2Fcamara");
    throw new Error("sign_in");
  }
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.error || "device_offline");
  }
  return response;
}

function notice(text, error = false) {
  el("control-status").textContent = text;
  el("control-status").classList.toggle("error", error);
}

function showOptics(optics) {
  const values = el("optics-values");
  values.replaceChildren();
  function row(title, value) {
    const dt = document.createElement("dt");
    const dd = document.createElement("dd");
    dt.textContent = title;
    dd.textContent = value;
    values.append(dt, dd);
  }
  if (optics.focus_automatic_continuous === 1) row(t("Enfoque", "Focus"), t("Automático", "Auto"));
  else if (optics.focus_absolute != null) row(t("Enfoque", "Focus"), String(optics.focus_absolute));
  if (optics.auto_exposure != null && optics.auto_exposure !== 1) row(t("Exposición", "Exposure"), t("Automática", "Auto"));
  else if (optics.exposure_time_absolute != null) {
    row(t("Exposición", "Exposure"), (optics.exposure_time_absolute / 10).toLocaleString(lang) + " ms");
  }
  el("optics").hidden = !values.childElementCount;
}

function makeControl(name, info) {
  const row = document.createElement("div");
  row.className = "camera-control";
  const head = document.createElement("div");
  head.className = "control-label";
  const label = document.createElement("label");
  label.htmlFor = "setting-" + name;
  label.textContent = labels[name];
  head.append(label);
  row.append(head);
  let input;
  if (info.choices) {
    input = document.createElement("select");
    for (const value of info.choices) input.add(new Option(frequencies[value], String(value)));
    head.append(input);
  } else {
    input = document.createElement("input");
    input.type = "range";
    for (const key of ["min", "max", "step"]) input[key] = info[key];
    const output = document.createElement("output");
    output.id = "value-" + name;
    output.setAttribute("for", label.htmlFor);
    head.append(output);
    row.append(input);
    input.addEventListener("input", () => { output.textContent = input.value; });
  }
  input.id = label.htmlFor;
  input.addEventListener("change", () => apply(name, Number(input.value)));
  return row;
}

function render(data) {
  state = data;
  const entries = Object.keys(labels).filter(name => data.controls[name]);
  const signature = JSON.stringify([data.device, entries.map(name => {
    const {value, ...range} = data.controls[name];
    return [name, range];
  })]);
  if (signature !== schema) {
    controls.replaceChildren(...entries.map(name => makeControl(name, data.controls[name])));
    schema = signature;
  }
  for (const name of entries) {
    const value = data.controls[name].value;
    el("setting-" + name).value = value;
    const output = el("value-" + name);
    if (output) output.textContent = value;
  }
  el("device-meta").textContent = [data.model, data.size?.join(" × ")].filter(Boolean).join(" · ");
  el("setting-help").textContent = !entries.length ? errors.controls_unavailable : data.device
    ? t("Soltá cada control para aplicar el cambio. Alfonsito lo recuerda al reconectar esta cámara.", "Release a control to apply its setting. Alfonsito remembers it when this camera reconnects.")
    : t("Los cambios se aplican a esta sesión.", "Changes apply to this session.");
  showOptics(data.optics || {});
  el("cam-connect").hidden = true;
  controls.disabled = writing;
}

async function load() {
  if (loading || writing || document.hidden || leaving) return;
  loading = true;
  const started = revision;
  try {
    const response = await request(endpoint + "options");
    const data = await response.json();
    if (started !== revision) return;
    render(data);
    notice(lastNotice);
  } catch (error) {
    if (started !== revision) return;
    controls.disabled = true;
    lastNotice = "";
    el("cam-connect").hidden = error.message !== "camera_offline";
    if (error.message !== "camera_busy") {
      el("device-meta").textContent = "";
      el("optics").hidden = true;
      el("setting-help").textContent = "";
      controls.replaceChildren();
      schema = "";
      state = null;
    }
    notice(errors[error.message] || errors.device_offline, true);
  } finally { loading = false; }
}

async function apply(name, value) {
  if (writing || !state) return;
  const previous = state.controls[name].value;
  if (value === previous) return;
  revision++;
  writing = true;
  controls.disabled = true;
  notice(t("Aplicando…", "Applying…"));
  try {
    const response = await request(endpoint + "options", {method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({device: state.device, control: name, value, previous})});
    render(await response.json());
    lastNotice = labels[name] + " · " + (state.device ? t("Guardado", "Saved") : t("Aplicado", "Applied"));
    notice(lastNotice);
  } catch (error) {
    lastNotice = "";
    writing = false;
    await load();
    notice(errors[error.message] || errors.setting_rejected, true);
  } finally {
    writing = false;
    controls.disabled = !state;
  }
}

function frameStatus(label, message = "", live = false) {
  const badge = el("live-state");
  if (badge.textContent !== label) badge.textContent = label;
  badge.classList.toggle("online", live);
  el("frame-note").textContent = message;
  el("frame-note").hidden = !message;
}

async function nextFrame() {
  if (paused || document.hidden || leaving || inFlight) return;
  clearTimeout(timer);
  if (loading || writing) {
    timer = setTimeout(nextFrame, 200);
    return;
  }
  const controller = new AbortController();
  inFlight = controller;
  const timeout = setTimeout(() => controller.abort(), 10000);
  let delay = 700;
  try {
    const response = await request(endpoint + "preview", {signal: controller.signal});
    if (!response.headers.get("Content-Type")?.startsWith("image/jpeg")) throw new Error("frame");
    const blob = await response.blob();
    if (controller.signal.aborted || paused || document.hidden || leaving) return;
    const previous = imageUrl;
    imageUrl = URL.createObjectURL(blob);
    image.src = imageUrl;
    image.hidden = false;
    if (previous) URL.revokeObjectURL(previous);
    frameStatus(t("En vivo", "Live"), "", true);
    lastFrameError = "";
  } catch (error) {
    if (!paused && !document.hidden && !leaving) {
      delay = 3500;
      frameStatus(t("En espera", "Waiting"), errors[error.message] || t("Esperando una imagen nueva…", "Waiting for a fresh image…"));
      if (error.message === "camera_offline" && lastFrameError !== error.message) load();
      lastFrameError = error.message;
    }
  } finally {
    clearTimeout(timeout);
    inFlight = null;
    if (!paused && !document.hidden && !leaving) timer = setTimeout(nextFrame, delay);
  }
}

function stopFrames() {
  clearTimeout(timer);
  inFlight?.abort();
}
el("pause").addEventListener("click", () => {
  paused = !paused;
  el("pause").textContent = paused ? t("Reanudar vista", "Resume preview") : t("Pausar vista", "Pause preview");
  stopFrames();
  if (paused) frameStatus(t("En pausa", "Paused"));
  else nextFrame();
});
el("grid").addEventListener("change", event => el("picture").classList.toggle("grid", event.target.checked));
el("cam-connect").addEventListener("click", async event => {
  const button = event.currentTarget;
  button.disabled = true;
  try {
    await request("/operator/connect-camera", {method: "POST", headers: {"Content-Type": "application/json"}, body: "{}"});
    await load();
  } catch (error) { notice(errors[error.message] || errors.camera_offline, true); }
  finally { button.disabled = false; }
});
document.addEventListener("visibilitychange", () => {
  stopFrames();
  if (!document.hidden) { load(); nextFrame(); }
});
window.addEventListener("pagehide", () => {
  leaving = true;
  stopFrames();
  if (imageUrl) { URL.revokeObjectURL(imageUrl); imageUrl = null; image.removeAttribute("src"); image.hidden = true; }
});
window.addEventListener("pageshow", event => {
  if (event.persisted) { leaving = false; load(); nextFrame(); }
});
setInterval(() => {
  if (!controls.contains(document.activeElement) || controls.disabled) load();
}, 15000);
load();
nextFrame();
