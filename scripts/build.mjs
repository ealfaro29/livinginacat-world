import fs from "node:fs/promises";
import path from "node:path";
import { createHash } from "node:crypto";
import { rootPath, readJSON, csv, esc } from "./lib.mjs";
import { publishedGuides, guideUrl, renderGuidePage } from "./guides.mjs";
import {
  shell,
  homePage,
  v1Page,
  v1Label,
  v2Page,
  route,
  resource,
} from "./presentation.mjs";

const [site, hardware, catalog, v2Catalog] = await Promise.all([
  readJSON("data/site.json"),
  readJSON("data/hardware-release.json"),
  readJSON("data/v1-catalog.json"),
  readJSON("data/v2-catalog.json"),
]);
const out = path.join(rootPath, "dist");
const assets = {};
const urls = new Set();
const sourceContext = {
  siteUrl: site.url,
  repo: `https://github.com/${site.repoOwner}/${site.repoName}`,
};
await fs.rm(out, { recursive: true, force: true });
await fs.mkdir(out, { recursive: true });

async function write(filename, content) {
  const destination = path.join(out, filename);
  await fs.mkdir(path.dirname(destination), { recursive: true });
  await fs.writeFile(destination, content);
}
function fileFor(url) {
  return url.endsWith("/") ? url.slice(1) + "index.html" : url.slice(1);
}
async function page(url, options) {
  if (!options.noindex) urls.add(url);
  await write(fileFor(url), shell({ site, url, assets, ...options }));
}

// Only these assets and the edition catalog are eligible for publication.
const publicAssets = [
  "assets/brand",
  "assets/fonts",
  "assets/assembly",
  "assets/editions",
  "assets/v2/visor",
  "assets/printed-parts.png",
  "assets/style.css",
  "assets/site.js",
  "downloads/guia-ensamblaje-ft412-es.pdf",
  "downloads/" + hardware.filename,
  "downloads/ft412-cradle-rev01",
  "downloads/ft412-cradle-rev01.zip",
  "downloads/ft412-coupler-rev01",
  "downloads/ft412-coupler-rev01.zip",
  "downloads/ft412-control-module-designer.html",
  "tools/control-module/index.html",
];
for (const name of publicAssets) {
  await fs.cp(path.join(rootPath, "public", name), path.join(out, name), {
    recursive: true,
  });
}
for (const [key, file] of Object.entries({ css: "style.css", js: "site.js" })) {
  const hash = createHash("sha256")
    .update(await fs.readFile(path.join(out, "assets", file)))
    .digest("hex")
    .slice(0, 12);
  assets[key] = `/assets/${file}?v=${hash}`;
}

const titles = {
  en: [
    "FT412 · A robot that uses an iPhone",
    v1Label,
    "V2 · Integrated console",
  ],
  es: [
    "FT412 · Un robot que usa un iPhone",
    v1Label,
    "V2 · Consola integrada",
  ],
};
const descriptions = {
  en: [
    "Meet Alfonsito, the working FT412 iPhone robot, and explore the design for the V2 printed console.",
    "Explore Alfonsito, the working V1 CoreXY prototype, with its parts list, illustrated assembly guide and approximate build cost.",
    "Explore the FT412 console in 3D, see which parts to buy for a second machine and estimate its cost in Costa Rica.",
  ],
  es: [
    "Conocé a Alfonsito, el robot FT412 que usa un iPhone, y explorá el diseño de la consola impresa V2.",
    "Consultá las piezas de Alfonsito, el prototipo CoreXY de la V1, su manual ilustrado y el costo aproximado de construcción.",
    "Explorá la consola FT412 en 3D, consultá qué comprar para una segunda máquina y cuánto cuesta tenerla en Costa Rica.",
  ],
};

const groupNames = new Map(catalog.groups.map((g) => [g.id, g.name]));
for (const lang of ["en", "es"]) {
  for (const [index, edition] of ["home", "v1", "v2"].entries()) {
    const body =
      edition === "home"
        ? homePage(lang)
        : edition === "v1"
          ? v1Page(lang, catalog, hardware)
          : v2Page(lang, v2Catalog);
    await page(route(lang, edition), {
      title: titles[lang][index],
      description: descriptions[lang][index],
      lang,
      page: edition,
      body,
      social:
        edition === "v1"
          ? "/assets/editions/v1-corexy.webp"
          : "/assets/editions/v2-console.webp",
    });
  }
  const headers =
    lang === "es"
      ? ["Grupo", "Artículo", "Cantidad", "Nota"]
      : ["Group", "Item", "Quantity", "Note"];
  const rows = catalog.items.map((i) => [
    groupNames.get(i.group)[lang],
    i.name[lang],
    i.quantity,
    i.note?.[lang] ?? "",
  ]);
  await write(`downloads/v1-${lang}.csv`, csv([headers, ...rows]));
  const v2Rows = v2Catalog.groups.flatMap((group) =>
    group.items.map((item) => [group[lang], item[lang], item.quantity]),
  );
  await write(`downloads/v2-${lang}.csv`, csv([headers.slice(0, 3), ...v2Rows]));
}

const docsLabels = {
  en: {
    title: "Documentation",
    text: "Use the illustrated manual at the workbench or download the drawings for a particular assembly.",
    sets: ["Assemble Alfonsito", "Replacement parts", "Project resources"],
    prototype: v1Label,
    source: "Source files",
    cad: "FT412 V2 model",
    cadText:
      "Rotate the console, inspect its hardware or download the editable STEP model.",
    planner: "Control module layout tool",
    plannerText:
      "Arrange the V1 electronics on a scaled work surface. Includes the earlier external enclosure design.",
  },
  es: {
    title: "Documentación",
    text: "Seguí el manual ilustrado en la mesa de montaje o descargá los planos del conjunto que estás armando.",
    sets: ["Armar a Alfonsito", "Piezas de reemplazo", "Recursos del proyecto"],
    prototype: v1Label,
    source: "Archivos de diseño",
    cad: "Modelo de la consola V2",
    cadText:
      "Girá la consola, inspeccioná la tornillería o descargá el modelo STEP editable.",
    planner: "Editor del módulo de control",
    plannerText:
      "Distribuí la electrónica de V1 a escala. Incluye el diseño anterior de la caja lateral.",
  },
};
const guideES = {
  assembly: [
    "Guía ilustrada de ensamblaje",
    "Las piezas y los herrajes de cada uno de los 30 pasos.",
  ],
  "project-guide": [
    "Descripción de la máquina",
    "Arquitectura, secuencia de montaje y pruebas del prototipo.",
  ],
  hardware: [
    "Marco, movimiento y punta",
    "Perfiles de aluminio y soportes impresos para el carro y el solenoide.",
  ],
  "motor-mounts": [
    "Soportes de motor",
    "Montaje, posición de las poleas y orientación de impresión.",
  ],
  electronics: [
    "Soporte de electrónica",
    "Ubicación de la placa, el controlador y el interruptor.",
  ],
  "fit-checks": [
    "Comprobaciones de encaje",
    "Mediciones y pruebas realizadas con la V1.",
  ],
  "release-scope": [
    "Archivos de impresión",
    "Diseños, cantidades y alcance de la entrega original.",
  ],
  "cradle-rev01": [
    "Cuna del solenoide REV01",
    "Cambio de los refuerzos y archivos STL y STEP de reemplazo.",
  ],
  "coupler-rev01": [
    "Acoplador de la punta REV01",
    "Dos mitades para la punta de malla y su geometría corregida.",
  ],
  attribution: [
    "Créditos y licencias",
    "Autores de la mecánica original, modificaciones y licencias.",
  ],
  contributing: [
    "Cómo contribuir",
    "Documentación de mejoras mecánicas y pruebas reproducibles.",
  ],
  "visual-identity": [
    "Identidad del proyecto",
    "La marca, las ilustraciones CAD y la tipografía de la web.",
  ],
};
const guideSections = [
  [
    "guides",
    [
      "assembly",
      "project-guide",
      "hardware",
      "motor-mounts",
      "electronics",
      "fit-checks",
      "release-scope",
    ],
  ],
  ["revisions", ["cradle-rev01", "coupler-rev01"]],
  ["resources", ["attribution", "contributing", "visual-identity"]],
];
const docUrl = (lang) =>
  lang === "es" ? "/es/documentation/" : "/documentation/";
for (const lang of ["en", "es"]) {
  const d = docsLabels[lang];
  const groups = guideSections
    .map(([id, slugs], index) => {
      const links = slugs.map((slug) => {
        const guide = publishedGuides.find((g) => g.slug === slug);
        const [name, detail] =
          lang === "es" ? guideES[slug] : [guide.title, guide.description];
        const langHint = lang === "es" && !guide.lang ? " · EN" : "";
        return resource(guideUrl(guide), name + langHint, detail);
      });
      if (id === "resources")
        links.unshift(
          resource(route(lang, "v2") + "#viewer", d.cad, d.cadText),
          resource(
            route(lang, "v2") + "#budget",
            lang === "es" ? "V2 · Piezas y presupuesto" : "V2 · Parts and budget",
            lang === "es" ? "Lista de compras y envío estimado a Costa Rica." : "Shopping list and estimated shipping to Costa Rica.",
          ),
          resource("/tools/control-module/", d.planner, d.plannerText),
        );
      return `<section class="section" id="${id}"><h2>${d.sets[index]}</h2><div class="resources">${links.join("")}</div></section>`;
    })
    .join("");
  await page(docUrl(lang), {
    lang,
    title: d.title,
    description: d.text,
    other: docUrl(lang === "es" ? "en" : "es"),
    body: `<div class="wrap doc-index"><div class="crumb"><a href="${route(lang)}">FT412</a></div><h1>${d.title}</h1><p class="lead">${d.text}</p>${groups}</div>`,
  });
}

for (const guide of publishedGuides) {
  const markdown = await fs.readFile(path.join(rootPath, guide.source), "utf8");
  await page(guideUrl(guide), {
    title: guide.title,
    description: guide.description,
    lang: guide.lang ?? "en",
    body: renderGuidePage(guide, markdown, sourceContext),
  });
  await write(`downloads/guides/${guide.slug}.md`, markdown);
  if (guide.slug === "project-guide")
    await write("downloads/project-guide.md", markdown);
}
const listMD = [
  "# Alfonsito (V1) · Parts and equipment",
  "",
  "| Group | Item | Quantity |",
  "| --- | --- | ---: |",
  ...catalog.items.map(
    (i) =>
      `| ${groupNames.get(i.group).en} | ${i.name.en.replaceAll("|", "\\|")} | ${i.quantity} |`,
  ),
  "",
  `[Build cost and searchable catalog](${site.url}/v1/#parts).`,
  "",
].join("\n");
await write("downloads/shopping-list.md", listMD);
await write("downloads/guides/shopping-list.md", listMD);

async function redirect(from, to, label, privateEntry = false) {
  const canonical = to.startsWith("https://") ? to : site.url + to;
  const target = esc(to);
  await write(
    fileFor(from),
    `<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex,${privateEntry ? "nofollow" : "follow"}"><meta http-equiv="refresh" content="0;url=${target}"><link rel="canonical" href="${esc(canonical)}"><link rel="stylesheet" href="${assets.css}"><title>${esc(label)} · ${esc(site.name)}</title></head><body><main class="wrap utility"><p class="crumb">living in a cat world</p><h1>${esc(label)}</h1><p><a href="${target}">Continue →</a></p></main></body></html>`,
  );
}
for (const source of [
  "/purchases/",
  "/shipments/",
  "/documentation/shopping-list/",
  "/documentation/data/",
  "/journal/first-purchases/",
  "/journal/parts-on-the-way/",
]) {
  await redirect(source, "/v1/#parts", "Alfonsito (V1) · Parts and equipment");
}
for (const source of ["/journal/", "/journal/project-begins/"])
  await redirect(source, "/v1/", v1Label);
for (const source of [
  "/brand-preview.html",
  "/documentation/hardware-art/",
  "/documentation/robot-cat-logo/",
])
  await redirect(source, "/documentation/visual-identity/", "Visual identity");
await redirect(
  "/documentation/repository/",
  "/documentation/",
  "Documentation",
);
await redirect(
  "/admin/",
  "https://livinginacat-admin.sentient-proposal-comments.workers.dev/",
  "Private workspace",
  true,
);
await page("/404.html", {
  title: "Page not found",
  description: "Find the FT412 prototype and console.",
  noindex: true,
  body: '<div class="wrap utility"><div class="crumb">404</div><h1>Page not found</h1><div class="actions"><a class="button" href="/">Overview</a><a class="button quiet" href="/es/">Inicio en español</a></div></div>',
});
urls.add("/assets/v2/visor/");
urls.add("/tools/control-module/");
await write("CNAME", site.domain + "\n");
await write(".nojekyll", "");
await write(
  "robots.txt",
  `User-agent: *\nAllow: /\nDisallow: /admin/\nSitemap: ${site.url}/sitemap.xml\n`,
);
await write(
  "sitemap.xml",
  `<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">${[...urls].map((url) => `<url><loc>${site.url}${url}</loc></url>`).join("")}</urlset>\n`,
);
await write(
  "feed.xml",
  `<?xml version="1.0" encoding="UTF-8"?><rss version="2.0"><channel><title>${esc(site.name)}</title><link>${site.url}</link><description>${esc(site.description)}</description><language>en</language>${["v1", "v2"].map((ed, i) => `<item><title>${esc(titles.en[i + 1])}</title><link>${site.url}/${ed}/</link><guid>${site.url}/${ed}/</guid><description>${esc(descriptions.en[i + 1])}</description></item>`).join("")}</channel></rss>\n`,
);
console.log(
  `Built ${urls.size} edition, documentation and design pages. V1 covers ${catalog.items.length} catalog entries.`,
);
