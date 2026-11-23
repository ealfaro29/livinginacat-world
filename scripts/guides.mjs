import path from "node:path";
import { Marked } from "marked";
import { esc } from "./lib.mjs";

export const guideGroups = [
  {
    id: "build",
    title: "Build guides",
    description:
      "The plan, the parts and the technical details for project 001.",
  },
  {
    id: "records",
    title: "Records and contributions",
    description: "How the data, source and shared work are maintained.",
  },
  {
    id: "design",
    title: "Design and assets",
    description: "The visual identity, artwork and prompts behind the journal.",
  },
];

export const guides = [
  {
    slug: "assembly",
    source: "docs/ASSEMBLY-ES.md",
    group: "build",
    lang: "es",
    title: "Guía de ensamblaje",
    description:
      "30 operaciones ilustradas. Cada paso empieza con las piezas y los herrajes y termina con una comprobación para seguir el montaje.",
  },
  {
    slug: "cradle-rev01",
    source: "hardware/ft412-cradle-rev01/README.md",
    group: "build",
    title: "Cradle REV01 correction",
    description:
      "Replacement cradle for the original rib interference: STL, STEP and CAD checks. Physical fit testing remains pending.",
  },
  {
    slug: "coupler-rev01",
    source: "hardware/ft412-coupler-rev01/README.md",
    group: "build",
    title: "Tip coupler REV01",
    description:
      "Two printed halves fit the measured mesh tip. Includes STEP, STL and the original dimensional checks.",
  },
  {
    slug: "project-guide",
    source: "docs/PROJECT.md",
    group: "build",
    title: "Project guide",
    description:
      "Architecture, build sequence, contact limits and planned acceptance tests.",
  },
  {
    slug: "shopping-list",
    source: "@shopping-list",
    group: "build",
    title: "Parts and equipment",
    description:
      "All 74 equipment lines, current quote totals, the equipment allowance and product links.",
  },
  {
    slug: "hardware",
    source: "hardware/ft412/README.md",
    group: "build",
    title: "Frame, motion and touch",
    description:
      "The FramingTech 355/250 and Adafruit 412 variant: configuration, printing and planned assembly.",
  },
  {
    slug: "motor-mounts",
    source: "hardware/ft412/MOTOR-MOUNTS.md",
    group: "build",
    title: "Printed motor mounts",
    description:
      "Mounts A and B, fasteners, pulley positions, print orientation and prototype checks.",
  },
  {
    slug: "electronics",
    source: "hardware/ft412/ELECTRONICS.md",
    group: "build",
    title: "Electronics mount",
    description:
      "The DLC32, MOSFET driver and cutoff-switch holder, with installation and insulation notes.",
  },
  {
    slug: "fit-checks",
    source: "docs/FIT-CHECKS.md",
    group: "build",
    title: "Initial fit checks",
    description:
      "Owner-reported M3, M4 and M5 checks in PLA Silk, current print progress and remaining tests.",
  },
  {
    slug: "release-scope",
    source: "hardware/ft412/PUBLIC-RELEASE.md",
    group: "build",
    title: "Print files and release scope",
    description:
      "What is included in the public CAD release, quantities and the limits of digital validation.",
  },
  {
    slug: "data",
    source: "docs/DATA.md",
    group: "records",
    title: "Maintaining the ledger",
    description:
      "Quotes, allowances, orders, payments and shipments: how evidence becomes a public record.",
  },
  {
    slug: "contributing",
    source: "CONTRIBUTING.md",
    group: "records",
    title: "Contributing",
    description:
      "Share a reproducible issue, a design improvement, a test result or an anonymized data correction.",
  },
  {
    slug: "attribution",
    source: "docs/ATTRIBUTION.md",
    group: "records",
    title: "Attribution and licenses",
    description:
      "The mechanical foundation, original notices, font license and publication scope.",
  },
  {
    slug: "repository",
    source: "README.md",
    group: "records",
    title: "Source and development",
    description:
      "Repository layout, local preview, checks and the GitHub Pages publication workflow.",
  },
  {
    slug: "visual-identity",
    source: "docs/BRAND.md",
    group: "design",
    title: "Visual identity",
    description:
      "The robot cat mark, CAD illustrations, colors and type used across both editions.",
  },
  {
    slug: "hardware-art",
    source: "docs/ART-PROMPTS.md",
    group: "design",
    title: "Hardware illustration",
    description:
      "The reusable visual brief for raw concept sketches, kept separate from manufacturing CAD.",
  },
  {
    slug: "robot-cat-logo",
    source: "docs/ROBOT-CAT-PROMPT.md",
    group: "design",
    title: "Robot cat logo",
    description:
      "The original logo prompt, generation mode and transparent image files.",
  },
];

export const guideUrl = (guide) => `/documentation/${guide.slug}/`;
const bySource = new Map(
  guides.filter((g) => !g.source.startsWith("@")).map((g) => [g.source, g]),
);
const sourceAliases = new Map([
  [
    "/downloads/project-guide.md",
    guides.find((g) => g.slug === "project-guide"),
  ],
  [
    "/downloads/shopping-list.md",
    guides.find((g) => g.slug === "shopping-list"),
  ],
]);

function guideReference(href, source, { repo, siteUrl }) {
  let local = href;
  for (const prefix of [`${repo}/blob/main/`, `${repo}/tree/main/`]) {
    if (local.startsWith(prefix)) local = "/" + local.slice(prefix.length);
  }
  if (local.startsWith(siteUrl + "/")) local = local.slice(siteUrl.length);
  if (/^[a-z][a-z0-9+.-]*:/i.test(local) || local.startsWith("//")) return null;
  if (local.startsWith("#") || !local) return null;
  const match = local.match(/^([^?#]*)(.*)$/);
  const pathname = decodeURIComponent(match[1]);
  const suffix = match[2];
  const alias = sourceAliases.get(pathname);
  if (alias) return guideUrl(alias) + suffix;
  const resolved = pathname.startsWith("/")
    ? pathname.slice(1)
    : path.posix.normalize(
        path.posix.join(
          source.startsWith("@") ? "" : path.posix.dirname(source),
          pathname,
        ),
      );
  const guide = bySource.get(resolved);
  return guide ? guideUrl(guide) + suffix : null;
}

export function resolveGuideLink(href, source, context) {
  const internal = guideReference(href, source, context);
  if (internal) return internal;
  if (href.startsWith(context.siteUrl + "/"))
    return href.slice(context.siteUrl.length);
  if (/^(?:[a-z][a-z0-9+.-]*:|\/\/|#|\/)/i.test(href)) return href;
  const match = href.match(/^([^?#]*)(.*)$/);
  const resolved = path.posix.normalize(
    path.posix.join(
      source.startsWith("@") ? "" : path.posix.dirname(source),
      decodeURIComponent(match[1]),
    ),
  );
  if (resolved.startsWith("public/")) return "/" + resolved.slice(7) + match[2];
  return `${context.repo}/blob/main/${resolved.split("/").map(encodeURIComponent).join("/")}${match[2]}`;
}

export function renderGuideMarkdown(markdown, guide, context) {
  const headings = [],
    seen = new Map();
  let removedTitle = false;
  const renderer = {
    heading({ tokens, depth }) {
      const html = this.parser.parseInline(tokens);
      if (depth === 1 && !removedTitle) {
        removedTitle = true;
        return "";
      }
      const text = html
        .replace(/<[^>]*>/g, "")
        .replace(/&amp;/g, "&")
        .replace(/&quot;/g, '"')
        .replace(/&#39;/g, "'");
      const base =
        text
          .normalize("NFKD")
          .replace(/[\u0300-\u036f]/g, "")
          .toLowerCase()
          .replace(/[^a-z0-9]+/g, "-")
          .replace(/^-|-$/g, "") || "section";
      const count = (seen.get(base) ?? 0) + 1;
      seen.set(base, count);
      const id = count === 1 ? base : base + "-" + count;
      if (depth === 2 || depth === 3) headings.push({ id, text, depth });
      return `<h${depth} id="${id}">${html}<a class="heading-anchor" href="#${id}" aria-label="Link to ${esc(text)}">#</a></h${depth}>\n`;
    },
    link({ href, title, tokens }) {
      const target = resolveGuideLink(href, guide.source, context);
      return `<a href="${esc(target)}"${title ? ` title="${esc(title)}"` : ""}>${this.parser.parseInline(tokens)}</a>`;
    },
    codespan({ text }) {
      const target = guideReference(text, guide.source, context);
      return target
        ? `<a href="${esc(target)}"><code>${esc(text)}</code></a>`
        : `<code>${esc(text)}</code>`;
    },
    image({ href, title, text }) {
      const target = resolveGuideLink(href, guide.source, context).replace(
        `${context.repo}/blob/main/`,
        `${context.repo}/raw/refs/heads/main/`,
      );
      const img = `<img src="${esc(target)}" alt="${esc(text)}"${title ? ` title="${esc(title)}"` : ""} loading="lazy">`;
      return guide.slug === "assembly"
        ? `<a class="assembly-figure" href="${esc(target)}" aria-label="Ampliar: ${esc(text)}">${img}<span>Ampliar ilustración ↗</span></a>`
        : img;
    },
  };
  const html = new Marked({ renderer, gfm: true }).parse(markdown);
  return { html, headings };
}

export const publishedGuideSlugs = [
  "assembly",
  "project-guide",
  "hardware",
  "motor-mounts",
  "electronics",
  "fit-checks",
  "release-scope",
  "cradle-rev01",
  "coupler-rev01",
  "attribution",
  "contributing",
  "visual-identity",
];
export const publishedGuides = publishedGuideSlugs.map((slug) =>
  guides.find((guide) => guide.slug === slug),
);

export function renderGuidePage(guide, markdown, context) {
  const { html, headings } = renderGuideMarkdown(markdown, guide, context);
  const es = guide.lang === "es";
  const contents = es ? "En esta guía" : "On this page";
  const toc = headings
    .map(
      (h) =>
        `<a href="#${h.id}" class="${h.depth === 3 ? "sub" : "top"}">${esc(h.text)}</a>`,
    )
    .join("");
  const download = `/downloads/guides/${guide.slug}.md`;
  const parent = es ? "/es/v1/" : "/documentation/";
  return `<article class="wrap guide-page"><header class="guide-header">
    <div class="crumb"><a href="${parent}">${es ? "V1 · Prototipo" : "Documentation"}</a></div>
    <h1>${esc(guide.title)}</h1><p class="lead">${esc(guide.description)}</p>
    <div class="guide-actions">${es ? '<a href="/downloads/guia-ensamblaje-ft412-es.pdf">Abrir el manual en PDF</a>' : ""}
    <a href="${download}" download>${es ? "Descargar Markdown" : "Download Markdown"}</a></div></header>
    ${toc ? `<details class="guide-toc-mobile"><summary>${contents}</summary><nav aria-label="${contents}">${toc}</nav></details>` : ""}
    <div class="guide-layout"><aside class="guide-sidebar">${toc ? `<nav class="guide-toc" aria-label="${contents}"><h2>${contents}</h2>${toc}</nav>` : ""}</aside>
    <div class="guide-prose">${html}</div></div></article>`;
}
