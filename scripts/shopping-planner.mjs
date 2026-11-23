import { readFile } from "node:fs/promises";
import { pathToFileURL } from "node:url";
import { readJSON } from "./lib.mjs";

const template = await readFile(new URL("../tools/v2-shopping/fragment.html", import.meta.url), "utf8");

export function shoppingPlanner(lang, catalog) {
  // Protect the JSON script element if a future part description contains markup.
  const data = JSON.stringify(catalog).replaceAll("<", "\\u003c");
  return template.replace('lang="es"', () => 'lang="' + lang + '"')
    .replace("__CATALOG__", () => data);
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  const lang = process.argv[2] ?? "es";
  if (!["es", "en"].includes(lang)) throw new Error("Use es or en.");
  process.stdout.write(shoppingPlanner(lang, await readJSON("data/v2-catalog.json")));
}
