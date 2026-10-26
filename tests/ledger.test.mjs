import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs/promises";
import { createHash } from "node:crypto";
import { readJSON, root, totals } from "../scripts/lib.mjs";
const ledger = await readJSON("data/ledger.json");
test("equipment estimate reconciles item quotes, vendors and planning allowances", () => {
  assert.equal(
    new Set(ledger.items.map((x) => x.id)).size,
    ledger.items.length,
  );
  assert.equal(ledger.items.length, 74);
  for (const x of ledger.items)
    assert.equal(x.quotedUnitCents * x.quantity, x.quotedTotalCents, x.id);
  for (const o of ledger.orders)
    assert.equal(
      ledger.items
        .filter((x) => x.orderId === o.id)
        .reduce((n, x) => n + x.quotedTotalCents, 0),
      o.quotedSubtotalCents,
      o.vendor,
    );
  assert.equal(totals(ledger).quotedItems, 238587);
  assert.equal(totals(ledger).equipmentAllowance, 50000);
  assert.equal(totals(ledger).quoted, 288587);
  assert.equal(totals(ledger).quoted, ledger.equipmentQuotedTotalCents);
  assert.ok(
    ledger.equipmentAllowances.every((x) => x.actualPaidCents === null),
  );
});
test("Amazon invoices reconcile without counting grouped extras twice", () => {
  for (const o of ledger.amazonOrders)
    assert.equal(
      o.invoiceItemsCents +
        o.shippingCents -
        o.shippingCreditCents -
        o.discountCents +
        o.taxCents,
      o.orderTotalCents,
      o.id,
    );
  const extra = ledger.otherExpenses.find(
    (x) => x.id === "amazon-additions-grouped",
  );
  assert.equal(extra.includedInVendorOrderTotals, true);
  assert.equal(
    extra.categoryTotalCents,
    extra.quotedTotalCents + extra.amazonTaxCents,
  );
  assert.equal(
    extra.amazonTaxCents,
    ledger.amazonOrders.reduce((n, x) => n + x.taxCents, 0),
  );
  assert.equal(
    ledger.amazonOrders.reduce((n, x) => n + x.invoiceItemsCents, 0),
    ledger.orders.find((x) => x.id === "amazon").quotedSubtotalCents +
      extra.quotedTotalCents,
  );
  assert.equal(totals(ledger).amazon, 152435);
  assert.equal(
    ledger.orders.find((x) => x.id === "amazon").invoiceTotalCents,
    totals(ledger).amazon,
  );
  assert.equal(ledger.amazonOrders.flatMap((x) => x.itemIds).length, 35);
});
test("unverified payments stay unknown, shipping is not delivery", () => {
  assert.equal(totals(ledger).verifiedPaid, 30485);
  assert.equal(totals(ledger).shipped, 2);
  assert.equal(
    ledger.amazonOrders.filter((x) => x.status === "payment_attention").length,
    3,
  );
  assert.ok(ledger.amazonOrders.every((x) => x.actualPaidCents === null));
  assert.ok(ledger.shipments.every((x) => x.deliveredAt === null));
  assert.equal(ledger.funding.receivedCents, null);
  const ft = ledger.orders.find((x) => x.id === "framingtech");
  assert.equal(
    ft.actualPaidCents,
    ft.quotedSubtotalCents + ft.shippingPaidCents + ft.taxPaidCents,
  );
  assert.equal(ft.shippingChargeFinal, false);
});
test("DigiKey order charges reconcile without establishing settled payment", () => {
  const order = ledger.orders.find((x) => x.id === "digikey");
  assert.equal(order.status, "ordered");
  assert.equal(order.invoiceTotalCents, 9697);
  assert.equal(
    order.invoiceTotalCents,
    7736 + order.shippingInvoicedCents + order.taxInvoicedCents + order.tariffInvoicedCents,
  );
  assert.equal(order.actualPaidCents, null);
  assert.equal(order.shippingPaidCents, null);
  assert.equal(order.taxPaidCents, null);
  assert.equal(order.tariffPaidCents, null);
});
test("published CAD archive matches its manifest hash", async () => {
  const release = await readJSON("data/hardware-release.json");
  const b = await fs.readFile(
    new URL("public/downloads/" + release.filename, root),
  );
  assert.equal(b.length, release.bytes);
  assert.equal(createHash("sha256").update(b).digest("hex"), release.sha256);
  assert.equal(release.physicalTested, false);
});
