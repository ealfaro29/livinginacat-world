const search = document.querySelector("#item-search"),
  vendor = document.querySelector("#vendor-filter"),
  status = document.querySelector("#status-filter");
if (search) {
  const rows = [...document.querySelectorAll("[data-item]")];
  const normalize = (s) =>
    s
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .toLowerCase();
  function filter() {
    const term = normalize(search.value);
    let count = 0;
    for (const row of rows) {
      const show =
        normalize(row.textContent).includes(term) &&
        (!vendor.value || row.dataset.vendor === vendor.value) &&
        (!status.value || row.dataset.status === status.value);
      row.hidden = !show;
      if (show) count++;
    }
    document.querySelector("#filter-count").textContent =
      `${count} of ${rows.length} lines`;
  }
  search.addEventListener("input", filter);
  vendor.addEventListener("change", filter);
  status.addEventListener("change", filter);
}

const sketchDetails = {
  eyes: {
    title: "01 / THE EYES",
    text: "A camera observes the screen before and after each action. Its view must be calibrated to the real machine.",
  },
  motion: {
    title: "02 / THE MOTION",
    text: "Two motors drive the CoreXY mechanism. The rails and belts position the touch head over the phone; travel limits still need physical calibration.",
  },
  touch: {
    title: "03 / THE TOUCH",
    text: "A capacitive tip makes real contact with the iPhone. Tap, swipe and drag are goals to test; a single tip cannot perform two-finger gestures.",
  },
};
for (const button of document.querySelectorAll("[data-sketch]"))
  button.addEventListener("click", () => {
    for (const other of document.querySelectorAll("[data-sketch]")) {
      other.setAttribute("aria-pressed", String(other === button));
      other.classList.toggle("active", other === button);
    }
    const note = document.querySelector("#sketch-note"),
      detail = sketchDetails[button.dataset.sketch];
    note.querySelector("b").textContent = detail.title;
    note.querySelector("p").textContent = detail.text;
  });
