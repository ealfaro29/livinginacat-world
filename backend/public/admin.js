const $ = (s) => document.querySelector(s);
const esc = (s) =>
  String(s ?? "").replace(
    /[&<>"']/g,
    (c) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[
        c
      ],
  );
const money = (c) =>
  c == null
    ? "Unconfirmed"
    : new Intl.NumberFormat("en-US", {
        style: "currency",
        currency: "USD",
      }).format(c / 100);
const date = (s) =>
  s
    ? new Intl.DateTimeFormat("en-US", {
        month: "short",
        day: "numeric",
        year: "numeric",
        timeZone: "America/Costa_Rica",
      }).format(new Date(s.length === 10 ? s + "T18:00:00Z" : s))
    : "Not confirmed";
let data,
  editing,
  uploading,
  tab = "packages",
  setupKey = new URLSearchParams(location.hash.slice(1)).get("setup");
if (setupKey) history.replaceState(null, "", location.pathname);
async function api(path, options = {}) {
  const r = await fetch(path, {
    ...options,
    headers: {
      ...(options.body instanceof ArrayBuffer
        ? {}
        : { "Content-Type": "application/json" }),
      ...options.headers,
    },
  });
  const content = await r.json();
  if (!r.ok) {
    if (r.status === 401 && path != "/api/login") await boot();
    throw new Error(content.error || "Request failed.");
  }
  return content;
}
function toast(message) {
  $("#toast").textContent = message;
  $("#toast").hidden = false;
  setTimeout(() => ($("#toast").hidden = true), 4500);
}
function busy(form, value) {
  form
    .querySelectorAll("button[type=submit]")
    .forEach((b) => (b.disabled = value));
}
async function boot() {
  try {
    const s = await api("/api/session");
    $("#loading").hidden = true;
    $("#auth").hidden = s.signedIn;
    $("#app").hidden = !s.signedIn;
    $("#logout").hidden = !s.signedIn;
    if (s.signedIn) {
      setupKey = null;
      await refresh();
    } else {
      data = null;
      for (const section of ["#packages", "#orders", "#history"])
        $(section).replaceChildren();
      const setup = s.setupAvailable && setupKey;
      $("#auth-title").textContent = setup ? "Make it yours." : "Welcome back.";
      $("#auth-description").textContent = setup
        ? "Choose your owner password to activate this private dispatch room. Use at least 14 characters."
        : "Sign in to manage orders, private invoices and locker arrivals.";
      $("#auth-mode").textContent = setup
        ? "ONE-TIME OWNER SETUP"
        : "OWNER ACCESS";
      $("#confirm-label").hidden = !setup;
      $("#auth-submit").textContent = setup
        ? "Activate private admin →"
        : "Enter the dispatch room →";
      const p = $("#auth-form [name=password]");
      $("#auth-form [name=username]").readOnly = !!setup;
      p.autocomplete = setup ? "new-password" : "current-password";
      p.minLength = setup ? 14 : 1;
      if (s.setupAvailable && !setupKey)
        $("#auth-description").textContent =
          "Owner setup is required. Use the private activation link opened for you.";
    }
  } catch (e) {
    $("#loading").textContent = "Unable to connect. Refresh to try again.";
  }
}
$("#auth-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const form = e.currentTarget,
    fields = new FormData(form);
  $("#auth-error").textContent = "";
  if (setupKey && fields.get("password") !== fields.get("confirm")) {
    $("#auth-error").textContent = "Passwords do not match.";
    return;
  }
  busy(form, true);
  try {
    await api(setupKey ? "/api/setup" : "/api/login", {
      method: "POST",
      body: JSON.stringify({
        key: setupKey,
        username: fields.get("username"),
        password: fields.get("password"),
      }),
    });
    form.reset();
    await boot();
  } catch (e) {
    $("#auth-error").textContent = e.message;
  } finally {
    busy(form, false);
  }
});
$("#logout").addEventListener("click", async () => {
  try {
    await api("/api/logout", { method: "POST", body: "{}" });
    data = null;
    $("#packages").replaceChildren();
    $("#orders").replaceChildren();
    $("#history").replaceChildren();
    await boot();
  } catch (e) {
    toast(e.message);
  }
});
async function refresh() {
  try {
    data = await api("/api/snapshot");
    render();
    $("#sync").textContent =
      "● Synced · " +
      new Date().toLocaleTimeString("en-US", {
        hour: "2-digit",
        minute: "2-digit",
      });
  } catch (e) {
    $("#sync").textContent = "Sync failed · refresh to retry";
    toast(e.message);
  }
}
$("#refresh").addEventListener("click", refresh);
const carrierLabels = { awaiting_tracking: "Awaiting tracking", preparing: "Preparing", shipped: "Shipped", carrier_delivered: "Delivered by carrier", on_hold: "On hold" };
const speedyLabels = { received: "Received by Speedy", in_transit: "In transit", delivered: "Delivered to recipient" };
function state(p) {
  if (p.speedyStatus) return [speedyLabels[p.speedyStatus] || "Speedy status", "arrived"];
  if (p.lockerArrivedAt) return ["At the locker", "arrived"];
  if (p.prealertedAt) return ["Prealerted", ""];
  if (p.readiness.ready) return ["Ready to prealert", "ready"];
  if (p.shippingStatus === "on_hold") return ["On hold", ""];
  return [p.tracking ? "Needs invoice PDF" : "Awaiting tracking", ""];
}
function render() {
  const ps = data.packages,
    counts = [
      ps.length,
      ps.filter(
        (p) => p.readiness.ready && !p.prealertedAt && !p.lockerArrivedAt,
      ).length,
      ps.filter((p) => p.prealertedAt && !p.lockerArrivedAt).length,
      ps.filter((p) => p.lockerArrivedAt).length,
    ];
  $("#stats").innerHTML = counts
    .map(
      (n, i) =>
        `<div class="stat"><strong>${String(n).padStart(2, "0")}</strong><span>${["Package records", "Ready to prealert", "Prealerted / in transit", "Received at locker"][i]}</span></div>`,
    )
    .join("");
  $("#package-count").textContent = ps.length;
  renderPackages();
  $("#orders").innerHTML = data.orders
    .map(
      (o) =>
        `<article class="order"><div><h3>${esc(o.vendor)}</h3><div class="order-reference">${esc(o.orderReference || "Not ordered")} · ${esc(o.id)}</div></div><div class="order-body"><strong>${esc(o.title)}</strong><p>${esc(o.notes)}</p><p>${esc(o.status.replaceAll("_", " "))} · ${o.orderedAt ? date(o.orderedAt) : "No purchase confirmed"}</p></div><div class="price">${money(o.totalCents)}<small>${o.status === "deferred" ? "QUOTED" : "ORDER TOTAL"}</small></div></article>`,
    )
    .join("");
  $("#history").innerHTML = data.history
    .map(
      (h) =>
        `<li><span>${esc(h.action)} · <strong>${esc(h.entity_id)}</strong></span><small>${date(h.created_at)} ${esc(new Date(h.created_at).toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit" }))} / ${esc(h.actor)}</small></li>`,
    )
    .join("");
}
function renderPackages() {
  const query = $("#search").value.toLowerCase(),
    filter = $("#filter").value;
  const visible = data.packages.filter((p) => {
    const o = data.orders.find((o) => o.id === p.orderId);
    if (
      ![o?.vendor, p.title, p.contents, p.tracking, p.carrier]
        .join(" ")
        .toLowerCase()
        .includes(query)
    )
      return false;
    return (
      filter === "all" ||
      (filter === "arrived" && p.lockerArrivedAt) ||
      (filter === "prealerted" && p.prealertedAt && !p.lockerArrivedAt) ||
      (filter === "ready" &&
        p.readiness.ready &&
        !p.prealertedAt &&
        !p.lockerArrivedAt) ||
      (filter === "needs" && !p.readiness.ready && !p.lockerArrivedAt)
    );
  });
  const priority = (p) =>
    p.lockerArrivedAt
      ? 5
      : p.readiness.ready && !p.prealertedAt
        ? 0
        : p.prealertedAt
          ? 1
          : p.tracking
            ? 2
            : p.shippingStatus === "on_hold"
              ? 4
              : 3;
  visible.sort(
    (a, b) =>
      priority(a) - priority(b) ||
      (a.expectedArrival || "9999").localeCompare(
        b.expectedArrival || "9999",
      ) ||
      a.id.localeCompare(b.id),
  );
  $("#packages").innerHTML = visible.length
    ? visible
        .map((p) => {
          const order = data.orders.find((o) => o.id === p.orderId),
            [label, cls] = state(p);
          return `<article class="package ${cls}"><div class="package-top"><span>${esc(order?.vendor)} / ${esc(p.id)}</span><span class="badge ${cls}">${label}</span></div><h3>${esc(p.title)}</h3><p class="contents" title="${esc(p.contents)}">${esc(p.contents)}</p><div class="tracking-row"><div><strong>${esc(p.tracking || "Tracking not issued yet")}</strong><small>${esc(p.carrier || "Carrier not confirmed")}</small></div>${p.tracking ? `<button class="text-button" data-action="copy" data-id="${esc(p.id)}">Copy ↗</button>` : ""}</div><dl><div><dt>Carrier status</dt><dd>${esc(carrierLabels[p.shippingStatus] || "Unknown")}</dd></div><div><dt>Speedy status</dt><dd>${esc(speedyLabels[p.speedyStatus] || (p.lockerArrivedAt ? "Received at locker" : "Not confirmed"))}</dd></div><div><dt>Estimated arrival</dt><dd>${date(p.expectedArrival)}</dd></div><div><dt>Locker arrival</dt><dd>${p.lockerArrivedAt ? date(p.lockerArrivedAt) : "Not received"}</dd></div><div><dt>Prealert</dt><dd>${p.prealertedAt ? date(p.prealertedAt) : "Not submitted"}</dd></div><div><dt>Goods value</dt><dd>${money(p.declaredValueCents)}</dd></div>${p.expectedShipDate ? `<div><dt>Planned dispatch</dt><dd>${date(p.expectedShipDate)}</dd></div>` : ""}</dl><div class="requirements">${[
            ["Tracking", !!p.tracking],
            ["Carrier", !!p.carrier],
            ["Invoice PDF", p.document?.kind === "invoice"],
          ]
            .map(
              ([l, done]) =>
                `<span class="requirement ${done ? "done" : ""}">${done ? "✓" : "○"} ${l}</span>`,
            )
            .join(
              "",
            )}</div><div class="file-row">${p.document ? `<a href="/api/documents/${esc(p.document.id)}" download>${esc(p.document.kind === "invoice" ? "Invoice / receipt PDF ↓" : p.document.kind === "provisional_invoice" ? "Provisional invoice ↓" : "Order confirmation ↓")}</a>` : '<span class="muted">No PDF attached</span>'}<button class="text-button" data-action="pdf" data-id="${esc(p.id)}">${p.document ? "Replace" : "Attach PDF"} +</button></div><div class="package-actions"><button class="secondary" data-action="edit" data-id="${esc(p.id)}">Edit details</button>${!p.lockerArrivedAt ? `<button class="secondary" data-action="arrive" data-id="${esc(p.id)}">Mark locker arrival ✓</button>` : ""}${p.readiness.ready && !p.prealertedAt ? `<button class="secondary" data-action="prealert" data-id="${esc(p.id)}">Mark prealert submitted</button>` : ""}</div>${p.consolidationReference ? `<p class="private-notes">↳ Consolidation: <strong>${esc(p.consolidationReference)}</strong></p>` : ""}${p.notes ? `<p class="private-notes">${esc(p.notes)}</p>` : ""}<p class="source">Evidence: ${esc(p.source || "Manual entry")} · checked ${date(p.sourceCheckedAt)}${p.prealertReference ? "<br>Speedy reference: " + esc(p.prealertReference) : ""}${p.speedyStatusVerifiedAt ? "<br>Speedy status checked: " + date(p.speedyStatusVerifiedAt) : ""}</p></article>`;
        })
        .join("")
    : '<p class="empty">No packages match this view.</p>';
}
$("#search").addEventListener("input", () => data && renderPackages());
$("#filter").addEventListener("change", () => data && renderPackages());
document.querySelectorAll("[data-tab]").forEach((b) =>
  b.addEventListener("click", () => {
    tab = b.dataset.tab;
    document
      .querySelectorAll("[data-tab]")
      .forEach((x) => x.setAttribute("aria-selected", String(x === b)));
    ["packages", "orders", "history"].forEach(
      (x) => ($("#" + x + "-panel").hidden = x !== tab),
    );
  }),
);
function openEditor(p) {
  editing = p;
  const f = $("#package-form");
  f.reset();
  $("#editor-error").textContent = "";
  $("#order-label").hidden = !!p;
  f.elements.orderId.innerHTML = data.orders
    .map(
      (o) =>
        `<option value="${esc(o.id)}">${esc(o.vendor)} · ${esc(o.orderReference || o.id)}</option>`,
    )
    .join("");
  for (const field of [
    "title",
    "contents",
    "carrier",
    "tracking",
    "shippingStatus",
    "expectedArrival",
    "notes",
    "prealertReference",
  ])
    f.elements[field].value =
      p?.[field] || (field === "shippingStatus" ? "awaiting_tracking" : "");
  f.elements.value.value =
    p?.declaredValueCents == null
      ? ""
      : (p.declaredValueCents / 100).toFixed(2);
  f.elements.prealerted.checked = !!p?.prealertedAt;
  f.elements.arrived.checked = !!p?.lockerArrivedAt;
  $("#editor-title").textContent = p ? "Package details." : "Add a package.";
  $("#editor").showModal();
}
$("#new-package").addEventListener("click", () => openEditor(null));
$("#close-editor").addEventListener("click", () => $("#editor").close());
$("#close-pdf").addEventListener("click", () => $("#pdf-editor").close());
$("#packages").addEventListener("click", async (e) => {
  const b = e.target.closest("[data-action]");
  if (!b) return;
  const p = data.packages.find((p) => p.id === b.dataset.id);
  if (!p) return;
  if (b.dataset.action === "edit") openEditor(p);
  if (b.dataset.action === "pdf") {
    uploading = p;
    $("#pdf-form").reset();
    $("#pdf-error").textContent = "";
    $("#pdf-package").textContent = p.title;
    $("#pdf-editor").showModal();
  }
  if (b.dataset.action === "copy") {
    try {
      await navigator.clipboard.writeText(p.tracking);
      toast("Tracking number copied.");
    } catch {
      toast("Select and copy the tracking number above.");
    }
  }
  if (["arrive", "prealert"].includes(b.dataset.action)) {
    openEditor(p);
    const form = $("#package-form");
    if (b.dataset.action === "arrive") form.elements.arrived.checked = true;
    else form.elements.prealerted.checked = true;
  }
});
$("#package-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const f = e.currentTarget,
    fields = new FormData(f),
    payload = {};
  for (const key of [
    "orderId",
    "title",
    "contents",
    "carrier",
    "tracking",
    "shippingStatus",
    "expectedArrival",
    "notes",
    "prealertReference",
  ])
    payload[key] = fields.get(key);
  payload.declaredValueCents =
    fields.get("value") === ""
      ? null
      : Math.round(Number(fields.get("value")) * 100);
  payload.prealertedAt = fields.get("prealerted")
    ? editing?.prealertedAt || new Date().toISOString()
    : null;
  payload.lockerArrivedAt = fields.get("arrived")
    ? editing?.lockerArrivedAt || new Date().toISOString()
    : null;
  if (editing) payload.version = editing.version;
  busy(f, true);
  try {
    const r = await api(
      editing ? "/api/packages/" + editing.id : "/api/packages",
      { method: editing ? "PATCH" : "POST", body: JSON.stringify(payload) },
    );
    if (
      !editing &&
      (payload.prealertedAt || payload.lockerArrivedAt || payload.notes)
    )
      await api("/api/packages/" + r.id, {
        method: "PATCH",
        body: JSON.stringify({ ...payload, version: 1 }),
      });
    $("#editor").close();
    await refresh();
    toast("Saved and synced across your devices.");
  } catch (e) {
    $("#editor-error").textContent = e.message;
  } finally {
    busy(f, false);
  }
});
$("#pdf-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const f = e.currentTarget,
    file = f.elements.file.files[0];
  if (!file) return;
  if (file.size > 8 * 1024 * 1024) {
    $("#pdf-error").textContent = "Maximum PDF size is 8 MB.";
    return;
  }
  busy(f, true);
  try {
    await api(
      "/api/packages/" +
        uploading.id +
        "/document?" +
        new URLSearchParams({ name: file.name, kind: f.elements.kind.value }),
      {
        method: "POST",
        body: await file.arrayBuffer(),
        headers: {
          "Content-Type": "application/pdf",
          "X-Record-Version": String(uploading.version),
        },
      },
    );
    $("#pdf-editor").close();
    await refresh();
    toast("PDF uploaded privately.");
  } catch (e) {
    $("#pdf-error").textContent = e.message;
  } finally {
    busy(f, false);
  }
});
document.addEventListener("visibilitychange", () => {
  if (!document.hidden && data && !$("dialog[open]")) refresh();
});
setInterval(() => {
  if (!document.hidden && data && !$("dialog[open]")) refresh();
}, 30000);
await boot();
