// Keep the mounted screen awake while it is visible and the browser allows it.
let lock;
async function keepAwake() {
  if (document.hidden || !navigator.wakeLock || (lock && !lock.released)) return;
  try { lock = await navigator.wakeLock.request("screen"); } catch { /* The system may be saving power. */ }
}
document.addEventListener("visibilitychange", keepAwake);
keepAwake();
