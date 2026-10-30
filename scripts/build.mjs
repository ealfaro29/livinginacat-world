import fs from "node:fs/promises";
import { createHash } from "node:crypto";
import path from "node:path";
import { fileURLToPath } from "node:url";
import matter from "gray-matter";
import { marked } from "marked";
import { renderHome, postCard, articleCover } from "./presentation.mjs";
import { guides, guideUrl, guideCatalog, renderGuidePage } from "./guides.mjs";
import {
  root,
  readJSON,
  money,
  esc,
  date,
  labels,
  totals,
  csv,
} from "./lib.mjs";
const site = await readJSON("data/site.json"),
  ledger = await readJSON("data/ledger.json"),
  hardware = await readJSON("data/hardware-release.json");
const groupedExpenses = ledger.otherExpenses.filter(
  (x) => x.name === "Taxes, tariffs, shipping and others" && x.includedInVendorOrderTotals,
);
const sum = totals(ledger),
  repo = `https://github.com/${site.repoOwner}/${site.repoName}`;
const assetVersions = Object.fromEntries(
  await Promise.all(
    [
      "style.css",
      "site.js",
      "brand/robot-cat-48.png",
      "brand/robot-cat-180.png",
      "shopping-list-1080x1440.png",
    ].map(async (name) => [
      name,
      createHash("sha256")
        .update(await fs.readFile(new URL(`public/assets/${name}`, root)))
        .digest("hex")
        .slice(0, 10),
    ]),
  ),
);
const asset = (name) => `/assets/${name}?v=${assetVersions[name]}`;
const out = new URL("dist/", root);
await fs.rm(out, { recursive: true, force: true });
await fs.mkdir(out, { recursive: true });
await fs.cp(new URL("public/", root), out, { recursive: true });
const write = async (file, text) => {
  const p = new URL(file, out);
  await fs.mkdir(path.dirname(fileURLToPath(p)), { recursive: true });
  await fs.writeFile(p, text);
};
const posts = [];
for (const file of (await fs.readdir(new URL("content/posts/", root))).filter(
  (x) => x.endsWith(".md"),
)) {
  const raw = await fs.readFile(new URL("content/posts/" + file, root), "utf8");
  const p = matter(raw);
  posts.push({ ...p.data, date: String(p.data.date), content: p.content, raw });
}
posts.sort((a, b) => b.number - a.number);
const badge = (status) =>
  `<span class="badge ${status.includes("attention") ? "attention" : ""}">${esc(labels[status] ?? status)}</span>`;
const nav = [
  ["/journal/", "Journal"],
  ["/purchases/", "Purchases"],
  ["/shipments/", "Shipments"],
  ["/documentation/", "Documentation"],
];
function shell(title, body, url = "/", description = site.description) {
  return `<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>${esc(title === site.name ? site.name : title + " · " + site.name)}</title><meta name="description" content="${esc(description)}"><meta name="theme-color" content="#101011"><link rel="canonical" href="${site.url}${url}"><meta property="og:title" content="${esc(title)}"><meta property="og:description" content="${esc(description)}"><meta property="og:type" content="${url.includes("/journal/") && url != "/journal/" ? "article" : "website"}"><meta property="og:url" content="${site.url}${url}"><meta property="og:image" content="${site.url}/assets/social-cat-world-dark-v3.png"><meta name="twitter:card" content="summary_large_image"><meta property="og:image:width" content="1200"><meta property="og:image:height" content="630"><link rel="icon" href="${asset("brand/robot-cat-48.png")}" type="image/png"><link rel="stylesheet" href="${asset("style.css")}"><link rel="alternate" type="application/rss+xml" title="living in a cat world" href="/feed.xml"></head><body><a class="skip" href="#contenido">Skip to content</a><header class="site-header"><a class="brand" href="/"><img src="${asset("brand/robot-cat-180.png")}" width="44" height="44" alt=""><span>living in a<span class="brand-world">cat world</span></span></a><nav aria-label="Main">${nav.map(([href, label]) => `<a href="${href}"${url.startsWith(href) ? ' aria-current="page"' : ""}>${label}</a>`).join("")}<a class="github" href="${repo}">GitHub ↗</a></nav><details class="mobile-nav"><summary>MENU <span>+</span></summary><nav aria-label="Mobile">${nav.map(([href, label]) => `<a href="${href}">${label} ↗</a>`).join("")}<a href="${repo}">GitHub ↗</a></nav></details></header><main id="contenido">${body}</main><footer><div><a class="footer-brand" href="/">living in a<br>cat world<span class="red-period">.</span></a><p>An AI for life in the real world.<br>Design, build and test, documented openly.</p></div><div><a href="${repo}">Code and files ↗</a><a href="/feed.xml">RSS</a><a href="/admin/">Private admin ↗</a><a href="/documentation/#transparency">How we document</a><span>Updated: ${date(ledger.updatedAt)} · USD</span></div><p class="footnote">Prototype in development. No physical build or test yet. Published under <a href="${repo}/blob/main/LICENSE">MIT</a>, with <a href="/documentation/attribution/">PhysiClaw attribution</a>.</p></footer><script src="${asset("site.js")}" defer></script></body></html>`;
}
const intro = (eyebrow, title, text) =>
  `<section class="page-intro wrap"><p class="eyebrow">${eyebrow}</p><h1>${title}</h1><p class="lead">${text}</p></section>`;
const card = (p) => postCard(p, ledger);
const finances = `<div class="stats"><div><strong>${money(sum.confirmedOrderTotal)}</strong><span>Confirmed orders + domain</span><small>Includes documented tax, shipping and grouped expenses. Bank settlement is not fully reconciled.</small></div><div><strong>${sum.shipped}</strong><span>Reported shipments</span><small>Based on vendor and carrier notices; some parcels still await carrier acceptance.</small></div><div><strong>${hardware.installedPrintedParts}</strong><span>Parts to print</span><small>${hardware.stlDesigns} designs + ${hardware.coupons} fit coupons.</small></div></div>`;
await write(
  "index.html",
  shell(
    "living in a cat world",
    renderHome({ posts, ledger, finances, hardware }),
  ),
);
await write(
  "journal/index.html",
  shell(
    "The journal",
    intro(
      "BUILDING IN THE OPEN",
      "The journal.",
      "Decisions, progress and mistakes documented from the start.",
    ) +
      `<section class="wrap post-grid section compact">${posts.map(card).join("")}</section>`,
    "/journal/",
  ),
);
for (const p of posts) {
  await write(
    `journal/${p.slug}/index.html`,
    shell(
      p.title,
      `<article class="article wrap"><header><a class="back" href="/journal/">← Back to the journal</a><p class="eyebrow">ENTRY ${String(p.number).padStart(2, "0")} · <time datetime="${p.date}">${date(p.date)}</time></p><h1>${esc(p.title)}</h1><p class="lead">${esc(p.excerpt)}</p><p class="article-byline">living in a cat world · Field notes</p></header>${articleCover(p, ledger)}<div class="prose">${marked.parse(p.content)}</div><aside class="article-end"><p>This entry preserves a snapshot of its publication date. The latest status is in the purchase and shipment records.</p><a class="text-link" href="/purchases/">Open the current record →</a> · <a href="${repo}/tree/main/content/posts">Read or propose changes in Markdown ↗</a></aside></article>`,
      `/journal/${p.slug}/`,
      p.excerpt,
    ),
  );
  await write(`downloads/post-${p.number}.md`, p.raw);
}
const vendorRows = ledger.orders
  .map(
    (o) =>
      `<tr><th scope="row">${esc(o.vendor)}</th><td>${money(o.quotedSubtotalCents)}</td><td>${badge(o.status)}</td><td>${money(o.invoiceTotalCents)}${o.invoiceTotalFinal === false ? "<small>Provisional</small>" : ""}</td><td>${money(o.actualPaidCents)}${o.paymentPartial ? "<small>Partial subtotal</small>" : ""}</td><td class="notes">${esc(o.notes)}</td></tr>`,
  )
  .join("");
const amazonRows = ledger.amazonOrders
  .map(
    (o) =>
      `<tr><th>${o.id}</th><td>${money(o.invoiceItemsCents)}</td><td>${money(o.discountCents)}</td><td>${money(o.orderTotalCents)}</td><td>${money(o.actualPaidCents)}</td><td>${badge(o.status)}</td></tr>`,
  )
  .join("");
const itemRows = ledger.items
  .map((x) => {
    const order = ledger.orders.find((o) => o.id === x.orderId),
      status = x.procurementStatus ?? order.status;
    return `<tr data-item data-vendor="${esc(x.vendor)}" data-status="${status}"><td><a href="${esc(x.url)}" rel="noreferrer">${esc(x.name)} ↗</a><small>${esc(x.notes)}</small></td><td>${esc(x.vendor)}</td><td>${x.quantity}</td><td>${money(x.quotedUnitCents)}</td><td>${money(x.quotedTotalCents)}</td><td>${badge(status)}${x.shipmentOrderRef ? `<small>${x.shipmentOrderRef}</small>` : ""}</td><td>${money(x.actualPaidCents)}</td></tr>`;
  })
  .join("");
const forwarding = ledger.forwardingCharges;
const forwardingLatest = [...new Map([...(forwarding?.observations ?? [])].sort((a, b) => a.observedAt.localeCompare(b.observedAt)).map((x) => [x.shipmentId, x])).values()];
const crc = (amount) => new Intl.NumberFormat("es-CR", {style: "currency", currency: "CRC", maximumFractionDigits: 0}).format(amount);
const forwardingTotal = forwardingLatest.reduce((sum, x) => sum + x.amountCRC, 0);
const forwardingSummary = `<div class="note-card mt"><p class="eyebrow">FORWARDING · CRC</p><h2>Speedy charges · ${crc(forwardingTotal)}</h2><p>Amounts shown by Speedy for received, exactly matched project shipments on ${date(forwarding.observedAt)}. Payment and the final consolidated total are not confirmed; charges may change. This subtotal is separate from USD purchase totals.</p><ul>${forwardingLatest.map((x) => `<li>${esc(x.shipmentId)}: ${crc(x.amountCRC)} · ${x.weightLbs} lb</li>`).join("")}</ul></div>`;
await write(
  "purchases/index.html",
  shell(
    "Purchases and accounts",
    intro(
      "PUBLIC RECORD · USD",
      "Every purchase, in context.",
      "Quoted prices, order totals and payments confirmed by the owner or vendor are shown separately. Unknown amounts remain unconfirmed.",
    ) +
      `<section class="wrap">${finances}${forwardingSummary}<div class="notice"><strong>${ledger.purchasesPaused ? "Purchases paused." : "Purchases resumed, one store at a time."}</strong> The owner confirms shipped purchases are paid. <strong>${money(sum.verifiedPaid)} in confirmed payments</strong> combines owner confirmations with vendor receipts. This is a partial subtotal; bank charges have not been independently reconciled.</div><div class="section-heading"><h2>By store</h2><span class="caption">As of: ${date(ledger.updatedAt)}</span></div><div class="table-scroll"><table><caption class="sr-only">Quotes, order totals and owner- or vendor-confirmed payments by store</caption><thead><tr><th>Store</th><th>Items quoted</th><th>Status</th><th>Order total</th><th>Confirmed paid</th><th>Details</th></tr></thead><tbody>${vendorRows}</tbody></table></div><p class="caption">Confirmed orders and the domain total <strong>${money(sum.confirmedOrderTotal)}</strong>. This excludes future forwarding costs and unconfirmed additional charges. Order amounts are not all independently reconciled against bank transactions.</p><p class="caption"><strong>Current equipment list estimate: ${money(sum.quotedItems)} in item quotes + ${money(sum.equipmentAllowance)} equipment allowance = ${money(sum.quoted)}.</strong> The allowance is an unallocated planning amount requested by the project owner, not a vendor quote, order or payment. Tax and shipping are excluded.</p><p class="caption">“Unconfirmed” does not mean $0. FramingTech’s $300.66 includes $121.51 in provisional shipping; its parts subtotal remains $179.15. Do not add both columns together.</p><h2 class="mt">Amazon orders</h2><p>Order totals: <strong>${money(sum.amazon)}</strong>, including the Taxes, tariffs, shipping and others category. AMZ-06 includes a pack of frame joining plates. The owner confirms shipped orders are paid. The remaining order is not included in the paid subtotal.</p><div class="table-scroll"><table><thead><tr><th>Public reference</th><th>Items</th><th>Discount</th><th>Order total</th><th>Confirmed paid</th><th>Status</th></tr></thead><tbody>${amazonRows}</tbody></table></div><p class="caption">Standard shipping on AMZ-02 and AMZ-03 is offset by equal shipping credits. AMZ references are public aliases, not the store’s order numbers.</p><div class="two-col mt"><div class="note-card"><p class="eyebrow">GROUPED COSTS</p><h3>Taxes, tariffs, shipping and others · ${money(sum.taxesAndOthers)}</h3>${groupedExpenses.map((x) => `<p><strong>${esc(x.vendor)}:</strong> ${money(x.categoryTotalCents)}.</p>`).join("")}<p>Already included in order totals.</p></div><div class="note-card"><p class="eyebrow">BLOG INFRASTRUCTURE</p><h3>Domain · ${money(419)} paid</h3><p>First year of livinginacat.world. Announced renewal: $71.99 on October 26, 2027, before possible charges. A future cost; pricing may change.</p></div></div><div class="notice neutral"><strong>Contributions and balance: not reconciled.</strong> There is no verified total of contributions received yet. We do not calculate a balance from incomplete data. This record documents orders and expenses, not a bank audit.</div></section><section class="wrap section" id="parts"><div class="section-heading"><div><p class="eyebrow">BILL OF MATERIALS</p><h2>All ${ledger.items.length} equipment lines.</h2></div><div class="downloads"><a href="${asset("shopping-list-1080x1440.png")}" download>PNG ↓</a><a href="/downloads/purchases.csv" download>CSV ↓</a><a href="/downloads/ledger.json" download>JSON ↓</a><a href="/downloads/shopping-list.md" download>Markdown ↓</a></div></div><div class="filters"><label>Search parts<input id="item-search" type="search" placeholder="Raspberry, screw, camera…"></label><label>Store<select id="vendor-filter"><option value="">All stores</option>${ledger.orders.map((o) => `<option>${esc(o.vendor)}</option>`).join("")}</select></label><label>Status<select id="status-filter"><option value="">All statuses</option>${[...new Set(ledger.items.map((x) => x.procurementStatus ?? ledger.orders.find((o) => o.id === x.orderId).status))].map((s) => `<option value="${s}">${labels[s]}</option>`).join("")}</select></label></div><p id="filter-count" class="caption" aria-live="polite">${ledger.items.length} lines</p><div class="table-scroll"><table class="items-table"><caption class="sr-only">Complete equipment list</caption><thead><tr><th>Part / quoted offer</th><th>Store</th><th>Qty.</th><th>Unit price</th><th>Quoted subtotal</th><th>Status</th><th>Items paid</th></tr></thead><tbody>${itemRows}</tbody></table></div><p class="caption">Quantity means purchase units; one pack may contain several parts. Item quotes reflect the initial planning snapshot and subsequent replacements, and may differ from confirmed order prices. Links are not affiliate links. Listings and lead times do not guarantee physical compatibility.</p><h2 class="mt">Recorded changes</h2><ul class="change-list">${ledger.changes.map((c) => `<li><time>${date(c.date ?? ledger.updatedAt)}</time><p>${esc(c.detail ?? c.summary ?? c.description ?? c.note ?? JSON.stringify(c))}</p></li>`).join("")}</ul><a class="text-link" href="${repo}/commits/main/data/ledger.json">View the full history on GitHub ↗</a></section>`,
    "/purchases/",
  ),
);
const shipCard = (s) =>
  `<article class="shipment-card"><div class="card-meta"><span>${s.id}</span>${badge(s.status)}</div><h2>${esc(s.title ?? (s.id === "AMZ-PKG-01" ? "Assembly file" : s.id === "AMZ-PKG-02" ? "Phone package" : s.vendor))}</h2><p class="carrier">${esc(s.carrier)}</p><dl><div><dt>${s.expectedDeliveryDate ? "Estimated arrival" : "Planned dispatch"}</dt><dd>${date(s.expectedDeliveryDate ?? s.expectedShipDate)}</dd></div><div><dt>Delivery</dt><dd>${s.deliveredAt ? date(s.deliveredAt) : "Unconfirmed"}</dd></div><div><dt>Last checked</dt><dd>${date(s.lastChecked ?? ledger.updatedAt)}</dd></div></dl><p>${esc(s.notes)}</p><small>Source: ${esc(s.source ?? "Vendor evidence")} · ${esc(s.orderRef)}</small></article>`;
await write(
  "shipments/index.html",
  shell(
    "Shipment tracking",
    intro(
      "FROM THE STORE TO THE WORKBENCH",
      "On the way. And getting ready.",
      "Status checked against available orders and emails. Estimated dates are kept separate from confirmed deliveries.",
    ) +
      `<section class="wrap">${forwardingSummary}<div class="shipment-grid">${ledger.shipments.map(shipCard).join("")}</div><div class="notice"><strong>Seventeen packages have been prealerted across two project consolidations.</strong> Speedy’s package listing shows five shipments received. Some parcels still await carrier acceptance.</div><div class="note-card mt"><h2>How this record is updated</h2><p>Last reviewed on ${date(ledger.updatedAt)}. Updates are based on reviewed vendor, carrier and forwarder records. This public page does not check email or stores in real time. The <a href="/admin/">private dispatch room</a> holds original PDFs, full tracking numbers, Speedy prealerts and confirmed locker arrivals.</p><p>Full tracking numbers, addresses and private tracking links stay outside the site and repository. “Shipped” does not mean “delivered.”</p><a class="text-link" href="/purchases/">Match shipments to purchases →</a></div></section>`,
    "/shipments/",
  ),
);
await write(
  "documentation/index.html",
  shell(
    "Open documentation",
    intro(
      "FILES TO READ, PRINT AND IMPROVE",
      "Building in the open.",
      "We share the available design, its checks, and everything that still needs a test on the workbench.",
    ) +
      `<section class="wrap"><div class="docs-feature"><div><p class="eyebrow">HARDWARE · V${hardware.version}</p><h2>The prototype parts.</h2><p>16 STL designs, their editable STEP files, 3 fit coupons and CAD review records. The manifest specifies 22 installed parts. The archive excludes commercial reference CAD and complete regeneration scripts.</p><a class="button" href="/downloads/${hardware.filename}" download>Download public CAD · 3 MB ↓</a><p class="caption hash">SHA-256: ${hardware.sha256}</p><a class="text-link" href="/documentation/release-scope/">Read the print guide and release scope ↗</a></div><img src="/assets/printed-parts.png" alt="CAD preview of the prototype’s printed parts" loading="lazy"></div><div class="notice"><strong>Not physically validated.</strong> Geometry and export checks do not validate assembly, tolerances, contact force or thermal behavior. Print the fit coupons and check the actual parts first.</div>${guideCatalog()}<div class="prose policy" id="transparency"><h2>Our transparency rules</h2><ol><li><strong>Keep the evidence.</strong> Original documents stay private. We publish the relevant amounts and statuses, without addresses or private identifiers.</li><li><strong>Keep estimates distinct from facts.</strong> Quoted, ordered, paid, shipped and delivered are distinct states. Unknown does not mean zero.</li><li><strong>Avoid double counting.</strong> Grouped expenses included in an order are not added again. Tax and shipping are explained separately when evidence is available.</li><li><strong>Record corrections.</strong> Data updates are tracked in Git; journal entries keep their dated context.</li><li><strong>Publish technical limits.</strong> Each test will document its setup, conditions, results and failures. CAD is not presented as evidence of unproven reliability.</li></ol><h2>Origin and license</h2><p>The mechanical foundation derives from <a href="https://github.com/physiclaw/PhysiClaw">PhysiClaw</a>, hardware v0.51, under MIT. We retain its notice and document our modifications. The blog and our contributions are published under MIT. Read the <a href="/documentation/attribution/">attribution and release scope</a>.</p><h2>What is not published yet</h2><p>The complete robot software, regeneration scripts and physical test results will be added as they are developed and validated. This initial site documents the start; it does not present those stages as complete.</p></div></section>`,
    "/documentation/",
  ),
);
await write(
  "404.html",
  shell(
    "Page not found",
    intro(
      "404",
      "Nothing here yet.",
      "Return to the journal to follow the project.",
    ) +
      `<div class="wrap"><a class="button" href="/">Back to the home page →</a></div>`,
    "/404.html",
  ),
);
await write(
  "admin/index.html",
  `<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex,nofollow"><meta http-equiv="refresh" content="0;url=https://livinginacat-admin.sentient-proposal-comments.workers.dev/"><title>Private admin · living in a cat world</title><link rel="stylesheet" href="${asset("style.css")}"></head><body><main class="wrap section"><p class="eyebrow">PRIVATE PROJECT OPERATIONS</p><h1>The dispatch room.</h1><p>Orders, invoice PDFs, Speedy prealerts and locker arrivals. Owner sign-in required.</p><a class="button" href="https://livinginacat-admin.sentient-proposal-comments.workers.dev/">Open private admin →</a><p><a href="/">← Public journal</a></p></main></body></html>`,
);
await write("CNAME", site.domain + "\n");
await write(".nojekyll", "");
await write("downloads/ledger.json", JSON.stringify(ledger, null, 2) + "\n");
const rows = [
  [
    "id",
    "store",
    "item",
    "quantity",
    "quoted_unit_usd",
    "quoted_subtotal_usd",
    "status",
    "paid_items_usd",
    "url",
    "record_type",
    "notes",
  ],
  ...ledger.items.map((x) => [
    x.id,
    x.vendor,
    x.name,
    x.quantity,
    (x.quotedUnitCents / 100).toFixed(2),
    (x.quotedTotalCents / 100).toFixed(2),
    x.procurementStatus ?? ledger.orders.find((o) => o.id === x.orderId).status,
    x.actualPaidCents == null ? "" : (x.actualPaidCents / 100).toFixed(2),
    x.url,
    "equipment_quote",
    x.notes,
  ]),
  ...(ledger.equipmentAllowances ?? []).map((x) => [
    x.id,
    "Not assigned",
    x.name,
    "",
    "",
    (x.amountCents / 100).toFixed(2),
    x.status,
    "",
    "",
    "planning_allowance",
    x.notes,
  ]),
];
await write("downloads/purchases.csv", csv(rows));
await write(
  "downloads/shopping-list.md",
  `# Shopping list · living in a cat world\n\nUpdated: ${ledger.updatedAt}. USD. Item quotes; tax and shipping excluded unless noted. ${ledger.purchasesPaused ? "Purchases paused." : "Purchases in progress, one store at a time."}\n\nEquipment quoted, including allowance: ${money(sum.quoted)}. Listed item quotes: ${money(sum.quotedItems)}; unallocated equipment allowance: ${money(sum.equipmentAllowance)}. The allowance is a planning amount, not a vendor quote, order or payment. Payment and shipping status: ${site.url}/purchases/.\n\n| Store | Item | Quantity | Unit price | Subtotal | Status | Offer |\n|---|---|---:|---:|---:|---|---|\n${ledger.items.map((x) => `| ${x.vendor} | ${x.name.replaceAll("|", "/")} | ${x.quantity} | ${money(x.quotedUnitCents)} | ${money(x.quotedTotalCents)} | ${labels[x.procurementStatus ?? ledger.orders.find((o) => o.id === x.orderId).status]} | [Product](${x.url}) |`).join("\n")}\n\n## Equipment allowance\n\n${(ledger.equipmentAllowances ?? []).map((x) => `- ${x.name}: ${money(x.amountCents)}. ${x.notes}`).join("\n")}\n\nItem quotes ${money(sum.quotedItems)} + allowance ${money(sum.equipmentAllowance)} = total estimate ${money(sum.quoted)}.\n\n## Reconciliation\n\nAmazon: ${ledger.amazonOrders.length} orders totaling ${money(sum.amazon)}, including the Taxes, tariffs, shipping and others category; five have carrier tracking, including four carrier-reported deliveries. AMZ-06 adds a pack of frame joining plates after the original estimate. The owner confirms shipped orders are paid; the remaining order is not included in the paid subtotal. Bank settlement has not been independently reconciled. Taxes, tariffs, shipping and others: ${money(sum.taxesAndOthers)} (${groupedExpenses.map((x) => `${x.vendor}: ${money(x.categoryTotalCents)}`).join("; ")}). Already included in vendor order totals. FramingTech: $300.66 paid ($179.15 parts + $121.51 provisional shipping). West3D: $17.55 paid per vendor invoice. Domain: $4.19 paid. Owner- or vendor-confirmed payments: ${money(sum.verifiedPaid)}, a partial subtotal. Shipped items of a partially shipped order are excluded until their payment can be allocated reliably.\n\nOther vendor order totals (see the purchase record for payment status):\n${ledger.orders
    .filter(
      (x) =>
        !["amazon", "framingtech"].includes(x.id) &&
        x.orderedAt &&
        x.invoiceTotalCents != null,
    )
    .map(
      (x) =>
        `- ${x.vendor}: ${money(x.invoiceTotalCents)}${x.invoiceTotalFinal === false ? " provisional" : ""}; ${labels[x.status]}.`,
    )
    .join("\n")}\n`,
);
await fs.copyFile(
  new URL("docs/PROJECT.md", root),
  new URL("downloads/project-guide.md", out),
);
for (const guide of guides) {
  const markdown = await fs.readFile(
    guide.source === "@shopping-list"
      ? new URL("downloads/shopping-list.md", out)
      : new URL(guide.source, root),
    "utf8",
  );
  await write(`downloads/guides/${guide.slug}.md`, markdown);
  await write(
    `documentation/${guide.slug}/index.html`,
    shell(
      guide.title,
      renderGuidePage(guide, markdown, { repo, siteUrl: site.url }),
      guideUrl(guide),
      guide.description,
    ),
  );
}
const routes = [
  "/",
  "/journal/",
  "/purchases/",
  "/shipments/",
  "/documentation/",
  ...guides.map(guideUrl),
  ...posts.map((p) => `/journal/${p.slug}/`),
];
await write(
  "sitemap.xml",
  `<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">${routes.map((r) => `<url><loc>${site.url}${r}</loc><lastmod>${ledger.updatedAt}</lastmod></url>`).join("")}</urlset>`,
);
await write(
  "robots.txt",
  `User-agent: *\nAllow: /\nSitemap: ${site.url}/sitemap.xml\n`,
);
await write(
  "feed.xml",
  `<?xml version="1.0" encoding="UTF-8"?><rss version="2.0"><channel><title>living in a cat world</title><link>${site.url}</link><description>${esc(site.description)}</description><language>en</language>${posts.map((p) => `<item><title>${esc(p.title)}</title><link>${site.url}/journal/${p.slug}/</link><guid>${site.url}/journal/${p.slug}/</guid><description>${esc(p.excerpt)}</description><pubDate>${new Date(p.date + "T12:00:00Z").toUTCString()}</pubDate></item>`).join("")}</channel></rss>`,
);
console.log(
  `Built ${routes.length} pages, ${guides.length} guides, ${ledger.items.length} equipment lines; quote ${money(sum.quoted)}, verified paid (partial) ${money(sum.verifiedPaid)}.`,
);
