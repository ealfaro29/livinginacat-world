import fs from "node:fs/promises";
import { readJSON, root, esc, money, totals } from "./lib.mjs";
const d = await readJSON("data/ledger.json"),
  t = totals(d);
const names = {
  "iPhone 14 · 128 GB · unlocked · Renewed Excellent":
    "iPhone 14 · 128 GB · Renewed Excellent",
  "CanaKit Raspberry Pi 5 PRO · 4 GB / 128 GB":
    "CanaKit Raspberry Pi 5 PRO · 4 GB / 128 GB",
  "MECCANIXITY · 26 shoulder screws · Ø5×20 mm · M4":
    "MECCANIXITY · Ø5×20 mm M4 shoulder screws",
  "uxcell · 150 mm X rail with MGN9H carriage":
    "uxcell · X 150 mm rail + MGN9H carriage",
  "uxcell · two 250 mm Y rails with MGN9H carriages":
    "uxcell · two Y 250 mm rails + MGN9H",
  "Landtek MILA34300N · dual-channel contact thermometer":
    "Landtek MILA34300N · contact thermometer",
};
function column(vendors, x) {
  let y = 226,
    svg = "";
  for (const vendor of vendors) {
    const o = d.orders.find((o) => o.vendor === vendor);
    svg += `<rect x="${x}" y="${y - 16}" width="480" height="24" rx="3" fill="#e4dcd1"/><text x="${x + 9}" y="${y}" font-size="13" font-weight="700">${esc(vendor.toUpperCase())}</text><text x="${x + 470}" y="${y}" text-anchor="end" font-size="12" font-family="monospace">${esc(money(o.quotedSubtotalCents))}</text>`;
    y += 25;
    for (const item of d.items.filter((i) => i.vendor === vendor)) {
      let name = names[item.name] ?? item.name;
      if (name.length > 46) name = name.slice(0, 45) + "…";
      svg += `<text x="${x + 2}" y="${y}" font-size="12">${esc(name)}</text><text x="${x + 400}" y="${y}" text-anchor="end" font-size="11" fill="#69645f">×${item.quantity}</text><text x="${x + 477}" y="${y}" text-anchor="end" font-size="12" font-family="monospace">${esc(money(item.quotedTotalCents))}</text><path d="M${x} ${y + 7}h480" stroke="#d6cdc2"/>`;
      y += 19.5;
    }
    y += 8;
  }
  return svg;
}
const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="1080" height="1440" viewBox="0 0 1080 1440"><rect width="1080" height="1440" fill="#f3eee5"/><g fill="#141414" font-family="Arial,Helvetica,sans-serif"><text x="44" y="49" font-size="12" letter-spacing="2">LIVING IN A CAT WORLD · OPEN BUILD JOURNAL</text><text x="42" y="105" font-family="Georgia,serif" font-size="43">Equipment shopping list</text><text x="44" y="140" font-size="14" fill="#69645f">74 equipment lines · USD · quoted items only · tax and shipping excluded</text><text x="44" y="170" font-size="12" fill="#69645f">Quantity means purchase units. Prices are line subtotals. Full specifications and product links are in the ledger.</text><text x="1035" y="48" text-anchor="end" font-family="monospace" font-size="12">OCTOBER 26, 2026</text><path d="M44 188h992" stroke="#bdb4a9"/>${column(["Amazon", "Bambu Lab"], 44)}${column(
  d.orders
    .filter((x) => !["Amazon", "Bambu Lab"].includes(x.vendor))
    .map((x) => x.vendor),
  556,
)}<rect x="44" y="1272" width="992" height="118" rx="8" fill="#141414"/><text x="66" y="1304" font-size="12" fill="#efc0bb" letter-spacing="1">TOTAL EQUIPMENT QUOTE</text><text x="66" y="1355" font-family="Georgia,serif" font-size="40" fill="#f3eee5">${money(t.quoted)}</text><text x="440" y="1305" font-size="13" fill="#f3eee5">A quote is not a payment receipt.</text><text x="440" y="1330" font-size="12" fill="#c7d6c4">See the ledger for taxes, extras and shipping.</text><text x="440" y="1356" font-size="13" fill="#efc0bb">livinginacat.world/purchases/</text><text x="44" y="1418" font-size="11" fill="#69645f">Prices may change. Purchases paused. Prototype not physically tested. Shortened labels; see the ledger for exact specifications.</text></g></svg>`;
await fs.writeFile(new URL("public/assets/shopping-list.svg", root), svg);
console.log("Generated 1080 × 1440 shopping-list.svg");
