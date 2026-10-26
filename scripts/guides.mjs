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
      "The blog name, Real World hero, robot cat mark, palette, typography and editorial voice.",
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
      return `<img src="${esc(target)}" alt="${esc(text)}"${title ? ` title="${esc(title)}"` : ""} loading="lazy">`;
    },
  };
  const html = new Marked({ renderer, gfm: true }).parse(markdown);
  return { html, headings };
}

export function guideCards(groupId) {
  return `<div class="doc-grid">${guides
    .filter((g) => g.group === groupId)
    .map(
      (g) =>
        `<a class="note-card" href="${guideUrl(g)}"><span class="eyebrow">GUIDE ${String(guides.indexOf(g) + 1).padStart(2, "0")}</span><h3>${esc(g.title)} ↗</h3><p>${esc(g.description)}</p><span class="guide-card-action">Read the guide</span></a>`,
    )
    .join("")}</div>`;
}

export function guideCatalog() {
  return `<div class="guide-catalog" id="guides">${guideGroups.map((group) => `<section class="guide-group" id="${group.id}-guides"><div class="section-heading"><div><p class="eyebrow">READ IN YOUR BROWSER / MARKDOWN SOURCE AVAILABLE</p><h2>${esc(group.title)}</h2><p class="caption">${esc(group.description)}</p></div></div>${guideCards(group.id)}</section>`).join("")}</div>`;
}

export function renderGuidePage(guide, markdown, context) {
  const { html, headings } = renderGuideMarkdown(markdown, guide, context);
  const group = guideGroups.find((g) => g.id === guide.group);
  const peers = guides.filter((g) => g.group === guide.group),
    index = peers.indexOf(guide);
  const toc = headings
    .map(
      (h) =>
        `<a class="toc-depth-${h.depth}" href="#${h.id}">${esc(h.text)}</a>`,
    )
    .join("");
  const sourceHref = guide.source.startsWith("@")
    ? "/downloads/ledger.json"
    : `${context.repo}/blob/main/${guide.source}`;
  const sourceLabel = guide.source.startsWith("@")
    ? "View source data ↗"
    : "View Markdown on GitHub ↗";
  return `<article class="guide-page wrap">
    <header class="guide-header"><a class="back" href="/documentation/#guides">← All documentation</a><p class="eyebrow">GUIDE ${String(guides.indexOf(guide) + 1).padStart(2, "0")} / ${esc(group.title)}</p><h1>${esc(guide.title)}</h1><p class="lead">${esc(guide.description)}</p><div class="guide-actions"><a href="/downloads/guides/${guide.slug}.md" download>Download Markdown ↓</a><a href="${sourceHref}">${sourceLabel}</a></div></header>
    ${headings.length ? `<details class="guide-toc-mobile"><summary>In this guide <span>+</span></summary><nav aria-label="In this guide">${toc}</nav></details>` : ""}
    <div class="guide-layout"><aside class="guide-sidebar">${headings.length ? `<nav class="guide-toc" aria-label="On this page"><p class="eyebrow">ON THIS PAGE</p>${toc}</nav>` : ""}<nav class="guide-related" aria-label="${esc(group.title)}"><p class="eyebrow">${esc(group.title)}</p>${peers.map((g) => `<a href="${guideUrl(g)}"${g === guide ? ' aria-current="page"' : ""}>${esc(g.title)}</a>`).join("")}</nav></aside><div class="guide-content"><div class="prose guide-prose">${html}</div><nav class="guide-pagination" aria-label="Guide navigation">${index > 0 ? `<a href="${guideUrl(peers[index - 1])}"><small>← PREVIOUS GUIDE</small>${esc(peers[index - 1].title)}</a>` : `<a href="/documentation/#guides"><small>← DOCUMENTATION</small>All guides</a>`}${index < peers.length - 1 ? `<a href="${guideUrl(peers[index + 1])}"><small>NEXT GUIDE →</small>${esc(peers[index + 1].title)}</a>` : `<a href="/documentation/#guides"><small>DOCUMENTATION →</small>All guides</a>`}</nav></div></div>
  </article>`;
}
