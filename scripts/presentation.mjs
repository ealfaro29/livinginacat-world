import { esc } from "./lib.mjs";

const v1Name = "Alfonsito";
export const v1Label = `V1 · ${v1Name}`;

const words = {
  en: {
    home: "Overview",
    v1: v1Label,
    v2: "V2 · Console",
    guide: "Assembly guide",
    files: "Documentation",
    skip: "Skip to content",
    lang: "Read in Spanish",
    footer: "An open hardware project based on PhysiClaw.",
    license: "Credits & licenses",
  },
  es: {
    home: "Inicio",
    v1: v1Label,
    v2: "V2 · Consola",
    guide: "Guía de montaje",
    files: "Documentación",
    skip: "Ir al contenido",
    lang: "Leer en inglés",
    footer: "Un proyecto de hardware abierto basado en PhysiClaw.",
    license: "Créditos y licencias",
  },
};
export const route = (lang, page = "home") =>
  (lang === "es" ? "/es/" : "/") + (page === "home" ? "" : page + "/");
const t = (lang, en, es) => (lang === "es" ? es : en);
const viewer = "/assets/v2/visor/";
const mechanical = "/assets/v2/visor/ft412-v2-step.zip";
const versionImage = {
  v1: "/assets/editions/v1-corexy.webp",
  v2: "/assets/editions/v2-console.webp",
};

export function shell({
  site,
  title,
  description,
  lang = "en",
  page = "",
  url,
  body,
  other,
  noindex = false,
  social,
  assets,
}) {
  const w = words[lang];
  const publicUrl = url ?? route(lang, page);
  const alternate =
    other ??
    (["home", "v1", "v2"].includes(page)
      ? route(lang === "es" ? "en" : "es", page)
      : null);
  const nav = [
    ["home", w.home],
    ["v1", w.v1],
    ["v2", w.v2],
  ];
  const brand = `<img width="36" height="36" src="/assets/brand/robot-cat-48.png" alt=""><span>living in a cat world</span>`;
  return `<!doctype html><html lang="${lang}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>${esc(title)} · ${esc(site.name)}</title><meta name="description" content="${esc(description)}"><meta name="theme-color" content="#faf9f5"><link rel="canonical" href="${site.url + publicUrl}">${alternate ? `<link rel="alternate" hreflang="${lang}" href="${site.url + publicUrl}"><link rel="alternate" hreflang="${lang === "es" ? "en" : "es"}" href="${site.url + alternate}">` : ""}${noindex ? '<meta name="robots" content="noindex,follow">' : ""}<meta property="og:type" content="website"><meta property="og:site_name" content="living in a cat world"><meta property="og:title" content="${esc(title)}"><meta property="og:description" content="${esc(description)}"><meta property="og:url" content="${site.url + publicUrl}"><meta property="og:image" content="${site.url + (social ?? versionImage.v2)}"><meta name="twitter:card" content="summary_large_image"><link rel="icon" type="image/png" href="/assets/brand/robot-cat-48.png"><link rel="stylesheet" href="${assets.css}"><script src="${assets.js}" defer></script></head>
<body><a class="skip" href="#main">${w.skip}</a><header class="mast"><div class="wrap mast-inner"><a class="wordmark" href="${route(lang)}">${brand}</a><nav class="primary" aria-label="${t(lang, "Main navigation", "Navegación principal")}">${nav.map(([p, label]) => `<a href="${route(lang, p)}"${page === p ? ' aria-current="page"' : ""}>${label}</a>`).join("")}</nav><div class="mast-tools"><a class="manual-link" href="/documentation/assembly/">${w.guide}</a>${alternate ? `<a class="lang" href="${alternate}" hreflang="${lang === "es" ? "en" : "es"}" aria-label="${w.lang}">${lang === "es" ? "EN" : "ES"}</a>` : ""}</div></div></header>
<main id="main">${body}</main><footer class="foot"><div class="wrap foot-inner"><div><a class="foot-brand" href="${route(lang)}">living in a cat world</a><p>${w.footer}</p></div><nav aria-label="${t(lang, "Resources", "Recursos")}"><a href="${route(lang, "v1")}">${w.v1}</a><a href="${route(lang, "v2")}">V2</a><a href="${route(lang, "documentation")}">${w.files}</a><a href="/documentation/attribution/">${w.license}</a></nav></div></footer></body></html>`;
}
function link(href, label, secondary = false, download = false) {
  return `<a class="button${secondary ? " quiet" : ""}" href="${esc(href)}"${download ? " download" : ""}>${esc(label)}</a>`;
}
function image(version, alt, priority = false) {
  return `<img src="${versionImage[version]}" alt="${esc(alt)}" width="1600" height="1200" ${priority ? 'fetchpriority="high"' : 'loading="lazy"'} decoding="async">`;
}
function navCrumb(lang, label) {
  return `<div class="crumb"><a href="${route(lang)}">FT412</a><span aria-hidden="true">/</span><span>${esc(label)}</span></div>`;
}
const models = {
  en: {
    v1: {
      title: v1Name,
      detail: "Aluminum frame · CoreXY drive",
      alt: "CAD view of Alfonsito with its open aluminum frame and an iPhone bed in the center.",
    },
    v2: {
      title: "Integrated console",
      detail: "196 × 302 × 231 mm · nominal height",
      alt: "Three-quarter CAD view of the V2 console with a front display, iPhone bed and overhead camera.",
    },
  },
  es: {
    v1: {
      title: v1Name,
      detail: "Marco de aluminio · transmisión CoreXY",
      alt: "Vista CAD de Alfonsito con su marco abierto de aluminio y la cama del iPhone en el centro.",
    },
    v2: {
      title: "Consola integrada",
      detail: "196 × 302 × 231 mm · altura nominal",
      alt: "Vista en perspectiva de la consola V2 con la pantalla frontal, la cama del iPhone y la cámara superior.",
    },
  },
};
function modelStage(lang, initial = "v2", selectable = false) {
  const labels = models[lang],
    versions = selectable ? ["v2", "v1"] : [initial];
  return `<figure class="model-stage" data-model-stage><div class="stage-bar"><span class="drawing-key">${t(lang, "CAD study", "Estudio CAD")}</span>${selectable ? `<div class="segments" role="group" aria-label="${t(lang, "Compare designs", "Comparar diseños")}">${versions.map((k) => `<button type="button" data-model="${k}" aria-controls="drawing-${k}" aria-pressed="${k === initial}">${k.toUpperCase()}</button>`).join("")}</div>` : `<span class="model-id">FT412 / ${initial.toUpperCase()}</span>`}</div>
${versions.map((k) => `<div class="model-view" id="drawing-${k}" data-drawing="${k}"${k === initial ? "" : " hidden"}><div class="render">${image(k, labels[k].alt, k === initial)}</div><div class="drawing-caption"><strong>${labels[k].title}</strong><span>${labels[k].detail}</span></div></div>`).join("")}</figure>`;
}
export function homePage(lang) {
  const es = lang === "es",
    tr = (a, b) => t(lang, a, b);
  return `<div class="wrap"><section class="hero home-hero"><div class="hero-copy"><p class="kicker">FT412 <span>/</span> ${tr("Open hardware", "Hardware abierto")}</p><h1>${es ? "Un robot que usa <em>un iPhone.</em>" : "A robot that uses <em>an iPhone.</em>"}</h1><p class="lead">${tr("A camera reads the screen. Two motors move a conductive tip to tap the glass. Alfonsito is the working V1 prototype. V2 brings the mechanism into a printed console.", "Una cámara observa la pantalla. Dos motores mueven una punta conductora para tocar el vidrio. Alfonsito es el prototipo V1 en funcionamiento. La V2 integra el mecanismo en una consola impresa.")}</p><div class="actions">${link(route(lang, "v2"), tr("Explore V2", "Explorar la V2"))}${link(route(lang, "v1"), tr("See Alfonsito", "Ver a Alfonsito"), true)}</div></div>${modelStage(lang, "v2", true)}</section>
<section class="section versions" aria-labelledby="versions"><div class="section-head"><h2 id="versions">${tr("The two versions", "Las dos versiones")}</h2><p>${tr("The same motion system, built around two different frames.", "El mismo sistema de movimiento en dos estructuras distintas.")}</p></div><div class="edition-grid">
<article class="edition"><div class="edition-top"><span class="edition-id">V1</span><span>${tr("Built & tested", "Construida y probada")}</span></div><h3><a href="${route(lang, "v1")}">${v1Name}</a></h3><p>${tr("Aluminum profiles carry the rails and printed mounts. The machine has tapped the iPhone and operated its calculator.", "Los perfiles de aluminio sostienen los rieles y las piezas impresas. La máquina ya tocó el iPhone y operó su calculadora.")}</p><div class="row-links"><a href="${route(lang, "v1")}#parts">${tr("Parts & cost", "Piezas e inversión")}</a><a href="/documentation/assembly/">${words[lang].guide}</a></div></article>
<article class="edition"><div class="edition-top"><span class="edition-id">V2</span><span>${tr("CAD design", "Diseño en CAD")}</span></div><h3><a href="${route(lang, "v2")}">${tr("The integrated console", "La consola integrada")}</a></h3><p>${tr("A printed chassis carries the camera, phone and electronics in one enclosure. The model shows how the hardware fits and how the carriage travels.", "Un chasis impreso reúne la cámara, el teléfono y la electrónica. El modelo muestra cómo encajan las piezas y por dónde se desplaza el carro.")}</p><div class="row-links"><a href="${route(lang, "v2")}#budget">${tr("Parts & budget", "Piezas y presupuesto")}</a><a href="${route(lang, "v2")}#viewer">${tr("3D viewer", "Visor 3D")}</a><a href="${route(lang, "v2")}#fasteners">${tr("Fastener guide", "Guía de tornillería")}</a></div></article></div></section></div>`;
}
function partsSection(lang, catalog) {
  const tr = (a, b) => t(lang, a, b);
  const groups = catalog.groups;
  const head = `<div class="section-head"><h2>${tr("Parts & workshop equipment", "Componentes y herramientas")}</h2><p>${tr("Quantities are those listed for purchase. A pack counts as one unit.", "Las cantidades corresponden a la lista de compras. Un paquete cuenta como una unidad.")}</p></div>`;
  const rows = groups
    .map((group) => {
      const items = catalog.items.filter((item) => item.group === group.id);
      return `<tbody data-part-group="${esc(group.id)}"><tr class="group-label"><th colspan="2" scope="rowgroup">${esc(group.name[lang])}</th></tr>${items.map((i) => `<tr data-part-row><td>${esc(i.name[lang])}${i.note ? `<small>${esc(i.note[lang])}</small>` : ""}</td><td>${esc(i.quantity)}</td></tr>`).join("")}</tbody>`;
    })
    .join("");
  return `<section id="parts" class="section parts-section"><div class="cost-band"><div><p class="kicker">${tr("V1 investment", "Inversión de la V1")}</p><p class="price">≈ US$${new Intl.NumberFormat(lang === "es" ? "es-CR" : "en-US", { useGrouping: true }).format(catalog.estimate.roundUSD)}</p></div><div><h2>${tr("Cost of the build", "Costo del proyecto")}</h2><p>${esc(catalog.estimate.note[lang])}</p></div></div>${head}
<form class="parts-controls" role="search" data-parts-controls hidden><label>${tr("Find a part", "Buscar una pieza")}<input type="search" data-part-search placeholder="${tr("Name or reference", "Nombre o referencia")}" autocomplete="off"></label><label>${tr("Group", "Grupo")}<select data-group-select><option value="">${tr("All groups", "Todos los grupos")}</option>${groups.map((g) => `<option value="${esc(g.id)}">${esc(g.name[lang])}</option>`).join("")}</select></label></form>
<div class="list-meta"><output data-part-count data-en="lines" data-es="referencias" aria-live="polite">${catalog.items.length} ${tr("lines", "referencias")}</output><a href="/downloads/v1-${lang}.csv" download>${tr("Download list (CSV)", "Descargar lista (CSV)")}</a></div>
<table class="parts-table"><thead><tr><th scope="col">${tr("Item", "Artículo")}</th><th scope="col">${tr("Qty.", "Cant.")}</th></tr></thead>${rows}</table><p class="empty" data-empty hidden>${tr("No parts match this search.", "Ninguna pieza coincide con la búsqueda.")} <button type="button" data-reset>${tr("Clear filters", "Borrar filtros")}</button></p></section>`;
}
export function v1Page(lang, catalog, hardware) {
  const tr = (a, b) => t(lang, a, b);
  return `<div class="wrap">${navCrumb(lang, v1Label)}<section class="hero version-hero"><div class="hero-copy"><p class="kicker">V1 <span>/</span> ${tr("Working prototype", "Prototipo en funcionamiento")}</p><h1>${v1Name}</h1><p class="lead">${tr("Printed mounts and aluminum profiles hold a CoreXY carriage over an iPhone 14. A solenoid lowers the mesh tip for each tap.", "Piezas impresas y perfiles de aluminio sostienen el carro CoreXY sobre un iPhone 14. Un solenoide baja la punta de malla en cada toque.")}</p><div class="actions">${link("#parts", tr("See the parts list", "Ver lista de piezas"))}${link("/documentation/assembly/", words[lang].guide, true)}</div></div>${modelStage(lang, "v1")}</section>
<section class="section resource-block" aria-labelledby="bench"><div class="section-head"><h2 id="bench">${tr("At the workbench", "En la mesa de montaje")}</h2><p>${tr("Start with the illustrated sequence. The two revisions replace the original cradle and tip coupler.", "Empezá con la secuencia ilustrada. Las dos revisiones sustituyen la cuna y el acoplador de punta originales.")}</p></div><div class="resources">
${resource("/documentation/assembly/", tr("Illustrated assembly guide", "Guía ilustrada de montaje"), tr("30 operations in Spanish, with hardware and diagrams for each step.", "30 operaciones con la tornillería y las ilustraciones de cada paso."))}
${resource("/downloads/" + hardware.filename, tr("Original print files", "Piezas originales para imprimir"), tr("STL and STEP for 16 designs, 22 installed pieces and three fit coupons.", "STL y STEP de 16 diseños, 22 piezas instaladas y tres cupones de prueba."))}
${resource(route(lang, "documentation") + "#revisions", tr("Cradle and coupler revisions", "Correcciones de cuna y punta"), tr("Replacement geometry for the solenoid cradle and the mesh tip.", "Geometría de reemplazo para la cuna del solenoide y la punta de malla."))}</div></section>
${partsSection(lang, catalog)}</div>`;
}
export function resource(href, title, desc) {
  return `<a class="resource" href="${esc(href)}"><strong>${esc(title)}</strong><span>${esc(desc)}</span></a>`;
}
function v2Budget(lang, { estimate, groups }) {
  const tr = (en, es) => t(lang, en, es);
  const number = (value, decimals = 0) =>
    new Intl.NumberFormat(lang === "es" ? "es-ES" : "en-US", {
      useGrouping: "always",
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals,
    }).format(value);
  const usd = (amount) => "US$" + number(amount, 2);
  const crc = (amount) => "₡" + number(amount);
  const freightCRC = estimate.shippingWeightLb * estimate.shippingCRCPerLb;
  const totalCRC = estimate.purchasesUSD * estimate.crcPerUSD + freightCRC;
  const shoppingRows = groups.map((group) =>
    `<tbody><tr class="group-label"><th colspan="2" scope="rowgroup">${esc(group[lang])}</th></tr>
    ${group.items.map((item) => `<tr><td>${esc(item[lang])}</td><td>${item.quantity}</td></tr>`).join("")}</tbody>`
  ).join("");
  return `<section id="budget" class="section" aria-labelledby="budget-title">
    <div class="section-head"><h2 id="budget-title">${tr("V2 build budget", "Presupuesto de la V2")}</h2>
    <p>${tr("This budget builds a second machine with its own iPhone, motors and electronics, so the V1 can stay in use.", "Este presupuesto permite armar una segunda máquina con su propio iPhone, motores y electrónica, mientras la V1 sigue funcionando.")}</p></div>
    <div class="cost-band v2-budget-band"><div><p class="kicker">${tr("Estimated total in Costa Rica", "Total estimado en Costa Rica")}</p>
    <p class="price">${usd(totalCRC / estimate.crcPerUSD)}</p><p class="budget-local">${crc(totalCRC)}</p></div>
    <dl class="budget-lines">
      <div><dt>${tr("Parts, including the iPhone", "Compras, incluido el iPhone")}</dt><dd>${usd(estimate.purchasesUSD)}</dd></div>
      <div><dt>${tr("Estimated packed weight", "Peso estimado con empaque")}</dt><dd>${estimate.packedWeightLb.join("–")} lb</dd></div>
      <div><dt>${tr("Shipping", "Envío")} · ${estimate.shippingWeightLb} lb × ${crc(estimate.shippingCRCPerLb)}/lb</dt><dd>${crc(freightCRC)} · ${usd(freightCRC / estimate.crcPerUSD)}</dd></div>
      <div><dt>${tr("Budget exchange rate", "Tipo de cambio usado")}</dt><dd>${crc(estimate.crcPerUSD)} / US$1</dd></div>
    </dl><p class="budget-terms">${tr("The shipping estimate assumes the rate covers import and delivery. Any tax or shipping charged separately by a retailer would add to the total.", "El cálculo supone que el flete cubre la importación y la entrega. Cualquier impuesto o envío que una tienda cobre aparte se sumaría al total.")}</p></div>
    <div class="budget-list-head"><h3 id="shopping-title">${tr("What to buy", "Qué comprar")}</h3>
    <a class="text-action" href="/downloads/v2-${lang}.csv" download>${tr("Download list (CSV)", "Descargar lista (CSV)")}</a></div>
    <table class="parts-table" aria-labelledby="shopping-title"><thead><tr><th scope="col">${tr("Item", "Artículo")}</th><th scope="col">${tr("Qty.", "Cant.")}</th></tr></thead>${shoppingRows}</table>
    <p class="spec-note"><strong>${tr("Already on hand.", "Ya disponibles.")}</strong> ${tr("The 3D printer, AMS and tools are shared with V1. The enclosure and camera frame use PETG already in stock. Spare touch tips, foam and wiring are also on hand.", "La impresora 3D, el AMS y las herramientas sirven para ambas versiones. La carcasa y el marco de la cámara se imprimen con el PETG disponible. También hay puntas táctiles de repuesto, espuma y cables.")}</p>
    <p class="spec-note"><strong>${tr("One external power lead.", "Un solo cable de alimentación.")}</strong> ${tr("The selected 12 V supply powers the MKS and solenoid. Inside the console, the Geekworm module supplies the Pi and the DFRobot module charges the iPhone. The budget assumes reuse of an IEC C13 mains lead and a 5 A USB-C cable for the Pi. Enclosure fit and temperature under load still need testing.", "La fuente elegida entrega 12 V a la MKS y al solenoide. Dentro de la consola, el módulo Geekworm alimenta la Pi y el DFRobot carga el iPhone. El presupuesto supone que se reutilizan un cable de corriente IEC C13 y un cable USB-C de 5 A para la Pi. Queda por comprobar el encaje en la caja y la temperatura bajo carga.")} <a href="https://www.meanwell.com/Upload/PDF/GST160A/GST160A-SPEC.PDF">${tr("Power supply datasheet", "Ficha de la fuente")}</a></p>
  </section>`;
}
export function v2Page(lang, catalog) {
  const tr = (a, b) => t(lang, a, b);
  return `<div class="wrap">${navCrumb(lang, tr("V2 · Console", "V2 · Consola"))}<section class="v2-intro"><div><p class="kicker">V2 <span>/</span> ${tr("Design in development", "Diseño en desarrollo")}</p><h1>${tr("The integrated", "La consola")} <em>${tr("console.", "integrada.")}</em></h1><p class="lead">${tr("The printed chassis replaces the aluminum frame. The electronics sit underneath the phone, with the display and power switch at the front.", "El chasis impreso reemplaza los perfiles de aluminio. La electrónica queda debajo del teléfono, con la pantalla y el interruptor al frente.")}</p><div class="row-links"><a href="#budget">${tr("Parts & budget", "Piezas y presupuesto")}</a><a href="#viewer">${tr("3D viewer", "Visor 3D")}</a></div></div><dl class="dimension"><dt>${tr("Exterior at nominal camera height", "Exterior a la altura nominal de cámara")}</dt><dd>196 × 302 × 231 <small>mm</small></dd><dt>${tr("Width × depth × height", "Ancho × fondo × alto")}</dt></dl></section>
<section id="viewer" class="viewer-section" aria-labelledby="viewer-title"><div class="viewer-title"><div><h2 id="viewer-title">${tr("Explore the model", "Explorá el modelo")}</h2><p>${tr("Rotate the assembly, move the carriage and inspect the two screw families. Viewer controls are in Spanish.", "Girá el conjunto, mové el carro y revisá las dos familias de tornillos.")}</p></div><a class="text-action" href="${viewer}">${tr("Open full viewer", "Abrir visor completo")}</a></div>
<div class="viewer-box" data-viewer-box data-src="${viewer}?embed=1" data-title="${tr("Interactive FT412 V2 CAD viewer", "Visor CAD interactivo FT412 V2")}"><div class="viewer-poster">${image("v2", models[lang].v2.alt, true)}<a class="button load-model" href="${viewer}" data-load>${tr("Load interactive 3D", "Cargar modelo 3D")}</a></div></div></section>
<div class="spec-strip"><div><b>100 mm</b><span>${tr("Glass to lens at nominal setting", "Del vidrio al lente a la altura nominal")}</span></div><div><b>${tr("106.1 × 206.1", "106,1 × 206,1")} mm</b><span>${tr("Usable XY travel with 2 mm at each end", "Recorrido XY con 2 mm de reserva en cada extremo")}</span></div><div><b>${tr("1.4", "1,4")} mm</b><span>${tr("Minimum modeled belt-to-screw clearance", "Separación mínima en CAD entre correa y tornillo")}</span></div></div>
${v2Budget(lang, catalog)}
<section id="fasteners" class="section"><div class="section-head"><h2>${tr("One hex key for the M3 screws", "Una llave para los tornillos M3")}</h2><p>${tr("Both M3 × 8 screws take a 2 mm hex key. The head shape follows the surface the screw bears against.", "Los dos M3 × 8 se aprietan con una llave Allen de 2 mm. La forma de la cabeza depende de la superficie donde apoya.")}</p></div><div class="fastener-layout"><figure><a href="/assets/v2/visor/herrajes.webp"><img loading="lazy" src="/assets/v2/visor/herrajes.webp" width="1575" height="762" alt="${tr("Section drawing of the countersunk plastic joint and the button-head screw recessed in the steel rail.", "Secciones del avellanado en el plástico y del tornillo de botón dentro del riel de acero.")}"></a></figure><dl class="fasteners"><div><dt>14</dt><dd><strong>${tr("Countersunk M3 × 8", "M3 × 8 avellanados")}</strong><span>#7213 · ${tr("Printed structural joints", "Uniones estructurales impresas")}</span></dd></div><div><dt>60</dt><dd><strong>${tr("Button-head M3 × 8", "M3 × 8 de botón")}</strong><span>#7219 · ${tr("Rails, carriages, motors and mounts", "Rieles, patines, motores y soportes")}</span></dd></div><div><dt>54</dt><dd><strong>${tr("Square M3 nuts", "Tuercas cuadradas M3")}</strong><span>${tr("Slide sideways into printed pockets", "Entran por el costado de la pieza impresa")}</span></dd></div></dl></div><p class="spec-note">${tr("The display keeps four M2.5 screws. The idler shafts, camera and switch retain their own fittings.", "La pantalla conserva cuatro tornillos M2,5. Los ejes de las poleas, la cámara y el interruptor conservan sus fijaciones propias.")}</p></section>
<section class="section closing"><div><h2>${tr("Design files", "Archivos de diseño")}</h2><p>${tr("The three carriages clear the modeled hardware throughout their travel. Belt tension, printed stiffness and physical fit still need a build test.", "Los tres patines completan su recorrido en CAD. Falta comprobar la tensión de las correas, la rigidez y el ajuste en una unidad impresa.")}</p></div><div class="actions">${link(mechanical, tr("Download STEP (ZIP)", "Descargar STEP (ZIP)"), false, true)}${link(viewer + "?vista=herrajes", tr("See each joint", "Ver cada unión"), true)}</div></section></div>`;
}
