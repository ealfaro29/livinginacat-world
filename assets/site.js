for (const stage of document.querySelectorAll("[data-model-stage]")) {
  const tabs = [...stage.querySelectorAll("[data-model]")];
  const views = [...stage.querySelectorAll("[data-drawing]")];
  function show(tab) {
    for (const t of tabs) t.setAttribute("aria-pressed", String(t === tab));
    for (const v of views) v.hidden = v.dataset.drawing !== tab.dataset.model;
  }
  for (const tab of tabs) {
    tab.addEventListener("click", () => show(tab));
    tab.addEventListener("keydown", (event) => {
      if (!["ArrowLeft", "ArrowRight", "Home", "End"].includes(event.key))
        return;
      event.preventDefault();
      const i = tabs.indexOf(tab);
      const next =
        event.key === "Home"
          ? 0
          : event.key === "End"
            ? tabs.length - 1
            : (i + (event.key === "ArrowLeft" ? -1 : 1) + tabs.length) %
              tabs.length;
      tabs[next].focus();
      show(tabs[next]);
    });
  }
}
const form = document.querySelector("[data-parts-controls]");
if (form) {
  const search = form.querySelector("[data-part-search]"),
    group = form.querySelector("[data-group-select]");
  const groups = [...document.querySelectorAll("[data-part-group]")];
  const out = document.querySelector("[data-part-count]"),
    empty = document.querySelector("[data-empty]");
  const clean = (v) =>
    v
      .normalize("NFKD")
      .replace(/[\u0300-\u036f]/g, "")
      .toLowerCase()
      .replace(/[×✕]/g, "x");
  function filter() {
    const words = clean(search.value.trim()).split(/\s+/).filter(Boolean);
    let total = 0;
    for (const section of groups) {
      let matches = 0;
      for (const row of section.querySelectorAll("[data-part-row]")) {
        const content = clean(row.cells[0].textContent);
        row.hidden =
          (!!group.value && group.value !== section.dataset.partGroup) ||
          !words.every((word) => content.includes(word));
        if (!row.hidden) matches++;
      }
      section.hidden = !matches;
      total += matches;
    }
    out.textContent = total + " " + out.dataset[document.documentElement.lang];
    empty.hidden = total !== 0;
  }
  form.hidden = false;
  form.addEventListener("submit", (event) => event.preventDefault());
  search.addEventListener("input", filter);
  group.addEventListener("change", filter);
  document.querySelector("[data-reset]").addEventListener("click", () => {
    form.reset();
    filter();
    search.focus();
  });
}
for (const box of document.querySelectorAll("[data-viewer-box]")) {
  const start = box.querySelector("[data-load]");
  start.addEventListener("click", (event) => {
    if (event.ctrlKey || event.metaKey || event.shiftKey || event.altKey)
      return;
    event.preventDefault();
    const frame = document.createElement("iframe");
    frame.src = box.dataset.src;
    frame.title = box.dataset.title;
    frame.allowFullscreen = true;
    window.addEventListener("message", (event) => {
      if (
        event.origin !== location.origin ||
        event.source !== frame.contentWindow ||
        event.data?.type !== "ft412:visor-height"
      )
        return;
      const height = event.data.height;
      if (Number.isFinite(height) && height >= 200 && height <= 2200)
        frame.style.height = Math.ceil(height) + "px";
    });
    box.replaceChildren(frame);
    frame.addEventListener("load", () => frame.focus(), { once: true });
  });
}
