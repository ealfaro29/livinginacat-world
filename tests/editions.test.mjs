import assert from "node:assert/strict";
import test from "node:test";
import { readJSON } from "../scripts/lib.mjs";
import { v1Page, v2Page, homePage } from "../scripts/presentation.mjs";
import { shoppingPlanner } from "../scripts/shopping-planner.mjs";

const catalog = await readJSON("data/v1-catalog.json");
const hardware = await readJSON("data/hardware-release.json");
const v2Catalog = await readJSON("data/v2-catalog.json");

test("the shopping planner carries the same V2 kits, power selection and budget as the site", () => {
  for (const lang of ["en", "es"]) {
    const fragment = shoppingPlanner(lang, v2Catalog);
    const embedded = fragment.match(/<script type="application\/json" data-catalog>([^<]+)<\/script>/);
    assert.deepEqual(JSON.parse(embedded[1]), v2Catalog);
    assert.ok(fragment.includes('id="ft412-segunda-maquina" lang="' + lang + '"'));
    assert.ok(v2Page(lang, v2Catalog).includes('id="power"'));
  }
  const power = v2Catalog.groups.find(group => group.id === "power");
  for (const model of ["GST160A12-R7B", "KPJX-PM-4S", "Pi5-5V5APD", "DFR0758"]) {
    assert.ok(power.items.some(item => item.en.includes(model) && item.es.includes(model)));
  }
});

test("the edition catalog contains only public parts, quantities, notes and one rounded build cost", () => {
  assert.deepEqual(Object.keys(catalog).sort(), [
    "estimate",
    "groups",
    "items",
  ]);
  assert.ok(
    catalog.estimate.roundUSD > 0 && catalog.estimate.roundUSD % 100 === 0,
  );
  assert.equal(catalog.items.length, 74);
  const groups = new Set(catalog.groups.map((g) => g.id));
  for (const item of catalog.items) {
    assert.ok(
      Object.keys(item).every((key) =>
        ["group", "name", "quantity", "note"].includes(key),
      ),
    );
    assert.ok(groups.has(item.group));
    assert.ok(Number.isInteger(item.quantity) && item.quantity > 0);
    for (const lang of ["en", "es"]) {
      assert.ok(item.name[lang]);
      assert.doesNotMatch(
        item.name[lang] + " " + (item.note?.[lang] ?? ""),
        /(?:US\$|\$\s*\d|tracking number|número de rastreo)/i,
      );
    }
  }
});

for (const lang of ["en", "es"]) {
  test(`${lang} edition pages render all parts, the CAD viewer and the corresponding language's routes`, () => {
    const parts = v1Page(lang, catalog, hardware);
    assert.equal(
      [...parts.matchAll(/<tr data-part-row>/g)].length,
      catalog.items.length,
    );
    assert.equal([...parts.matchAll(/US\$/g)].length, 1);
    assert.ok(parts.includes(`/downloads/v1-${lang}.csv`));
    const model = v2Page(lang, v2Catalog);
    assert.match(model, /data-src="\/assets\/v2\/visor\/\?embed=1"/);
    assert.match(model, /href="\/assets\/v2\/visor\/ft412-v2-step.zip"/);
    assert.ok(model.includes(`href="/assets/v2/visor/?home=${lang}"`));
    assert.ok(homePage(lang).includes(`href="${lang === "es" ? "/es" : ""}/v2/#budget"`));
    assert.ok(model.includes(`/downloads/v2-${lang}.csv`));
    assert.ok(model.includes(lang === "es" ? "US$1.017,44" : "US$1,017.44"));
    assert.ok(model.includes(lang === "es" ? "₡457.850" : "₡457,850"));
    for (const group of v2Catalog.groups) {
      for (const item of group.items) {
        const note = item.note ? `<small>${item.note[lang]}</small>` : "";
        assert.ok(model.includes(`<td>${item[lang]}${note}</td><td>${item.quantity}</td>`));
      }
    }
    assert.doesNotMatch(
      parts + model + homePage(lang),
      /\/(?:purchases|shipments)\/|\/downloads\/ledger\.json/,
    );
  });
}
