import fs from "node:fs/promises";
import path from "node:path";
import { rootPath, readJSON } from "./lib.mjs";
import { assertPublicText } from "./privacy.mjs";

const base = path.join(rootPath, "dist");
const { url: siteUrl } = await readJSON("data/site.json");
async function walk(dir) {
  const entries = await fs.readdir(dir, { withFileTypes: true });
  const paths = await Promise.all(
    entries.map((entry) => {
      const absolute = path.join(dir, entry.name);
      return entry.isDirectory() ? walk(absolute) : [absolute];
    }),
  );
  return paths.flat();
}
const files = (await walk(base)).map((file) => path.relative(base, file));
const paths = new Set(files);
const html = new Map(),
  errors = [];
const forbidden =
  /^(?:assets\/(?:shopping-list|social-cat-world-dark)|downloads\/(?:ledger|build-progress|orders|purchases|shipments|expenses|forwarding|quotes|post-0?[23]|(?:guides\/)?data\.md)|private\/|backend\/|data\/)/i;
for (const file of files) {
  if (forbidden.test(file))
    errors.push(`Operational or superseded material in public output: ${file}`);
  if (!/\.(html|m?js|css|json|md|csv|xml|txt|svg)$/i.test(file)) continue;
  const value = await fs.readFile(path.join(base, file), "utf8");
  try {
    assertPublicText(value, file);
  } catch (error) {
    errors.push(error.message);
  }
  if (
    /\/Users\/|\/var\/folders\/|access_token|[\w.+-]+@(?:gmail|outlook|hotmail)\.com|\b\d{3}-\d{7}-\d{7}\b/i.test(
      value,
    )
  ) {
    errors.push(`Private data marker in ${file}`);
  }
  if (!file.endsWith(".html")) continue;
  if (!/<html\s+lang="(?:en|es)"/.test(value))
    errors.push(`Missing language in ${file}`);
  const markup = value.replace(
    /(<(?:script|style)\b[^>]*>)[\s\S]*?<\/(?:script|style)>/gi,
    "$1",
  );
  html.set(file, {
    markup,
    ids: new Set([...markup.matchAll(/\sid="([^"]+)"/g)].map((m) => m[1])),
  });
}
for (const [file, { markup }] of html) {
  const from = new URL(file, siteUrl + "/");
  for (const match of markup.matchAll(
    /\s(?:href|src|data-src)=["']([^"']*)["']/gi,
  )) {
    const href = match[1].replaceAll("&amp;", "&");
    const url = new URL(href, from);
    if (url.origin !== siteUrl) continue;
    const pathname = decodeURIComponent(url.pathname).slice(1);
    const dest =
      !pathname || pathname.endsWith("/") ? pathname + "index.html" : pathname;
    if (!paths.has(dest)) errors.push(`Broken link: ${file} -> ${href}`);
    else if (
      url.hash &&
      html.has(dest) &&
      !html.get(dest).ids.has(decodeURIComponent(url.hash.slice(1)))
    ) {
      errors.push(`Broken section link: ${file} -> ${href}`);
    }
  }
}
for (const file of [
  "index.html",
  "es/index.html",
  "v1/index.html",
  "v2/index.html",
  "es/v1/index.html",
  "es/v2/index.html",
  "documentation/assembly/index.html",
  "assets/v2/visor/index.html",
  "assets/v2/visor/consola.glb",
  "assets/v2/visor/ft412-v2-step.zip",
  "downloads/ft412-v2-completa.3mf",
]) {
  if (!paths.has(file))
    errors.push(`Missing required edition resource: ${file}`);
}
if (errors.length) {
  console.error([...new Set(errors)].join("\n"));
  process.exitCode = 1;
} else {
  console.log(
    `Checked ${files.length} public files. Edition routes, links, anchors and privacy checks passed.`,
  );
}
