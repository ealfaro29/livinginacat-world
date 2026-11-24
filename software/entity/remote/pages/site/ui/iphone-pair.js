const es = document.documentElement.lang === "es";
const code = document.getElementById("pair-code");
const message = document.getElementById("pair-message");
const install = document.getElementById("install-hint");
if (navigator.standalone || matchMedia("(display-mode: standalone)").matches) install.hidden = true;
let query = "start", timer, pending = false;
async function poll() {
  clearTimeout(timer);
  if (document.hidden || pending) return;
  pending = true;
  let delay = 2500;
  try {
    const response = await fetch("/iphone/pair/" + query, { method: "POST", cache: "no-store" });
    if (response.status === 410) { query = "start"; code.textContent = "—"; delay = 250; }
    else if (response.ok) {
      const data = await response.json();
      if (data.linked) { location.replace("/iphone?lang=" + (es ? "es" : "en")); return; }
      code.textContent = data.code.slice(0, 4) + " " + data.code.slice(4);
      message.textContent = "";
      query = "status";
    } else { throw new Error(String(response.status)); }
  } catch (err) {
    if (err.message === "429") delay = 60000;
    message.textContent = es ? "Esperando conexión. Se reintentará automáticamente." : "Waiting for connection. This page will retry automatically.";
  } finally {
    pending = false;
    if (!document.hidden) timer = setTimeout(poll, delay);
  }
}
document.addEventListener("visibilitychange", poll);
window.addEventListener("online", poll);
poll();
