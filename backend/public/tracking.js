const $ = (s) => document.querySelector(s);
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);
const phases = [["shipped", "Shipped"], ["miami", "Miami"], ["costa_rica", "Costa Rica"], ["delivered", "Entregado"]];
let items = [], savePhase, pending = new Set();
const verificationDate = (value) => value ? new Intl.DateTimeFormat("es-CR", { dateStyle: "medium", timeStyle: "short", timeZone: "America/Costa_Rica" }).format(new Date(value)) + " · CR" : "Sin fecha registrada";
const eventDate = (value) => new Intl.DateTimeFormat("es-CR", { dateStyle: "medium", timeZone: "UTC" }).format(new Date(value + "T12:00:00Z"));
function evidenceLinks(item) {
  const evidence = item.evidence || [];
  if (!evidence.length) return `<small class="tracking-verification">Revisión: ${esc(verificationDate(item.sourceCheckedAt))}. Sin enlace externo registrado.</small>`;
  return `<div class="tracking-evidence">${evidence.map((proof) => `<div class="tracking-proof"><a href="${esc(proof.url)}" target="_blank" rel="noopener noreferrer">${esc(proof.label)} ↗</a>${proof.detail ? `<small>${esc(proof.detail)}</small>` : ""}<small>${esc(proof.eventLabel)}: ${proof.eventDate ? `<time datetime="${esc(proof.eventDate)}">${esc(eventDate(proof.eventDate))}</time>${proof.eventTime ? " · " + esc(proof.eventTime) : ""}` : "fecha no indicada por la fuente"}</small><small>Verificado: <time datetime="${esc(proof.observedAt)}">${esc(verificationDate(proof.observedAt))}</time></small></div>`).join("")}</div>`;
}
export function clearTracking() {
  items = [];
  pending.clear();
  $("#tracking-lists").replaceChildren();
  $("#tracking-summary").textContent = "";
}
export function setTracking(payload) {
  items = payload.items;
  render();
}
function render() {
  const query = $("#tracking-search").value.toLocaleLowerCase("es"), filter = $("#tracking-filter").value;
  const visible = items.filter((item) => {
    if (![item.title, item.vendor, item.note].join(" ").toLocaleLowerCase("es").includes(query)) return false;
    if (filter === "pending") return !item.stages.delivered;
    if (filter === "delivered") return item.stages.delivered;
    if (filter === "costa_rica") return item.stages.costa_rica && !item.stages.delivered;
    if (filter === "miami") return item.stages.miami && !item.stages.costa_rica && !item.stages.delivered;
    if (filter === "unshipped") return !item.stages.shipped && !item.stages.delivered;
    return true;
  });
  const count = (scope) => items.filter((x) => x.scope === scope).length;
  $("#tracking-summary").textContent = `${count("project")} artículos del proyecto · ${count("personal")} personales · ${items.filter((x) => x.stages.delivered).length} entregados`;
  const positions = new Map([...document.querySelectorAll(".tracking-scroll")].map((el) => [el.dataset.scope, el.scrollLeft]));
  $("#tracking-lists").innerHTML = [["project", "Proyecto"], ["personal", "Personal"]].map(([scope, title]) => {
    const rows = visible.filter((x) => x.scope === scope);
    return `<section class="tracking-section" aria-labelledby="tracking-${scope}-title"><div class="tracking-section-heading"><h2 id="tracking-${scope}-title">${title}</h2><span>${rows.length} artículos</span></div><div class="tracking-scroll" data-scope="${scope}"><table class="tracking-table"><thead><tr><th scope="col">Artículo</th><th scope="col">Tienda</th><th scope="col">Cantidad</th>${phases.map(([, label]) => `<th scope="col" class="phase-col">${label}</th>`).join("")}<th scope="col">Estado / pendiente</th></tr></thead><tbody>${rows.map((item) => `<tr data-item="${esc(item.id)}"><th scope="row">${esc(item.title)}</th><td>${esc(item.vendor)}</td><td>${esc(item.quantity)}</td>${phases.map(([phase, label]) => !item.shippingRequired && phase !== "delivered" ? '<td class="phase-cell"><span class="not-applicable" title="Compra local, sin envío">—</span></td>' : `<td class="phase-cell ${item.stages[phase] ? "phase-confirmed" : ""}"><input type="checkbox" data-phase="${phase}" data-item-id="${esc(item.id)}" aria-label="${label}: ${esc(item.title)}" ${item.stages[phase] ? "checked" : ""} ${pending.has(item.id) ? "disabled" : ""} title="${item.manuallyMarked.includes(phase) ? "Marcado por ti" : item.stages[phase] ? "Confirmado en la revisión" : "Sin confirmar"}"></td>`).join("")}<td class="tracking-note">${esc(item.note)}${evidenceLinks(item)}<span class="tracking-row-status" role="status">${pending.has(item.id) ? "Guardando…" : ""}</span></td></tr>`).join("") || '<tr><td colspan="8" class="tracking-empty">No hay artículos con este filtro.</td></tr>'}</tbody></table></div></section>`;
  }).join("");
  for (const el of document.querySelectorAll(".tracking-scroll")) el.scrollLeft = positions.get(el.dataset.scope) || 0;
}
export function initTracking({ api, refresh, toast }) {
  savePhase = async (input) => {
    const item = items.find((x) => x.id === input.dataset.itemId);
    if (!item || pending.has(item.id)) return;
    const phase = input.dataset.phase, value = input.checked;
    pending.add(item.id);
    input.closest("tr").querySelectorAll("input").forEach((x) => x.disabled = true);
    input.closest("tr").querySelector(".tracking-row-status").textContent = "Guardando…";
    try {
      await api(`/api/tracking/${encodeURIComponent(item.id)}`, { method: "PATCH", body: JSON.stringify({ version: item.version, phase, value }) });
      pending.delete(item.id);
      await refresh();
      const saved = [...document.querySelectorAll("#tracking-lists input")].find((x) => x.dataset.itemId === item.id && x.dataset.phase === phase);
      if (saved) {
        saved.focus({ preventScroll: true });
        saved.closest("tr").querySelector(".tracking-row-status").textContent = "Guardado";
      }
    } catch (error) {
      pending.delete(item.id);
      await refresh();
      toast(error.message);
    }
  };
  $("#tracking-search").addEventListener("input", render);
  $("#tracking-filter").addEventListener("change", render);
  $("#tracking-lists").addEventListener("change", (event) => {
    if (event.target.matches("input[data-phase]")) savePhase(event.target);
  });
}
