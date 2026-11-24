const es = document.documentElement.lang === "es";
for (const card of document.querySelectorAll(".shortcut-card")) {
  const status = card.querySelector(".copy-status");
  const field = card.querySelector(".copy-fallback");
  async function copy(value) {
    try {
      await navigator.clipboard.writeText(value);
      field.hidden = true;
      field.value = "";
      status.textContent = es ? "Copiado." : "Copied.";
    } catch {
      field.value = value;
      field.hidden = false;
      field.focus();
      field.select();
      status.textContent = es ? "Tocá el valor seleccionado y elegí Copiar." : "Tap the selected value and choose Copy.";
    }
  }
  card.querySelector("[data-copy-url]").addEventListener("click", () => copy(card.querySelector("label input").value));
  const credential = card.querySelector("[data-credential]");
  credential.addEventListener("click", async () => {
    credential.disabled = true;
    try {
      const response = await fetch("/atajos/autorizacion/" + credential.dataset.credential, { method: "POST", cache: "no-store" });
      if (response.status === 401) { location.replace("/?next=%2Fatajos&lang=" + (es ? "es" : "en")); return; }
      if (!response.ok) throw new Error();
      await copy(await response.text());
    } catch {
      status.textContent = es ? "Volvé a intentar la copia." : "Please try copying again.";
    } finally { credential.disabled = false; }
  });
}
