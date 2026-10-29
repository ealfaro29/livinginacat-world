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
  assert.equal(totals(ledger).quotedItems, 239888);
  assert.equal(totals(ledger).equipmentAllowance, 50000);
  assert.equal(totals(ledger).quoted, 289888);
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
  const amazonTax = ledger.amazonOrders.reduce((n, x) => n + x.taxCents, 0);
  assert.equal(
    ledger.amazonOrders.reduce((n, x) => n + x.invoiceItemsCents, 0),
    ledger.orders.find((x) => x.id === "amazon").quotedSubtotalCents +
      extra.categoryTotalCents - amazonTax,
  );
  assert.equal(totals(ledger).amazon, 153450);
  assert.equal(
    ledger.orders.find((x) => x.id === "amazon").invoiceTotalCents,
    totals(ledger).amazon,
  );
  assert.equal(ledger.amazonOrders.flatMap((x) => x.itemIds).length, 36);
});
test("owner-confirmed shipped payments are included without assuming delivery", () => {
  assert.equal(totals(ledger).verifiedPaid, 221797);
  assert.equal(totals(ledger).shipped, 16);
  assert.equal(
    ledger.amazonOrders.filter((x) => x.status === "payment_attention").length,
    0,
  );
  assert.equal(ledger.amazonOrders.filter((x) => x.actualPaidCents != null).length, 5);
  assert.equal(ledger.amazonOrders.find((x) => x.id === "AMZ-04").actualPaidCents, null);
  assert.equal(ledger.orders.find((x) => x.id === "amazon").actualPaidCents, ledger.amazonOrders.reduce((n, x) => n + (x.actualPaidCents ?? 0), 0));
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
test("BoltDepot receipt reconciles owner-selected spares and charges", () => {
  const order = ledger.orders.find((x) => x.id === "boltdepot");
  const items = ledger.items.filter((x) => x.orderId === order.id);
  assert.equal(items.length, 13);
  assert.equal(items.reduce((sum, x) => sum + x.quantity, 0), 182);
  assert.equal(items.reduce((sum, x) => sum + x.quotedTotalCents, 0), 1604);
  assert.equal(order.status, "shipped");
  assert.equal(order.invoiceTotalCents, 2616);
  assert.equal(
    order.invoiceTotalCents,
    1604 + order.shippingInvoicedCents + order.taxInvoicedCents + order.tariffInvoicedCents,
  );
  assert.equal(order.actualPaidCents, 2616);
});
test("Walmart grouped costs remain included in the order total", () => {
  const order = ledger.orders.find((x) => x.id === "walmart");
  const extra = ledger.otherExpenses.find((x) => x.id === "walmart-additions-grouped");
  assert.equal(order.status, "partially_shipped");
  assert.equal(order.invoiceItemsCents, order.quotedSubtotalCents + extra.categoryTotalCents - order.taxInvoicedCents);
  assert.equal(order.invoiceTotalCents, order.invoiceItemsCents + order.taxInvoicedCents);
  assert.equal(order.invoiceTotalCents, 5331);
  assert.equal(extra.includedInVendorOrderTotals, true);
  assert.ok(extra.categoryTotalCents >= order.taxInvoicedCents);
  assert.equal(totals(ledger).taxesAndOthers, 70671);
  assert.equal(order.actualPaidCents, null);
  assert.equal(extra.actualPaidCents, null);
});
test("Bambu order and grouped costs reconcile without double counting", () => {
  const order = ledger.orders.find((x) => x.id === "bambu-lab");
  const extra = ledger.otherExpenses.find((x) => x.id === "bambu-additions-grouped");
  assert.equal(order.invoiceTotalCents, order.invoiceItemsCents - order.discountCents + order.shippingInvoicedCents + order.taxInvoicedCents);
  assert.equal(order.invoiceTotalCents, 88186);
  assert.ok(extra.categoryTotalCents >= order.taxInvoicedCents + order.shippingInvoicedCents);
  assert.equal(extra.includedInVendorOrderTotals, true);
  const confirmedOrders = ledger.orders.reduce((sum, x) => sum + x.invoiceTotalCents, 0);
  assert.equal(confirmedOrders + 419, 299936);
  assert.equal(totals(ledger).confirmedOrderTotal, confirmedOrders + 419);
  assert.equal(order.actualPaidCents, 88186);
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

test("forwarder charge snapshot stays in colones and matches known shipments", () => {
  const f = ledger.forwardingCharges;
  assert.equal(f.currency, "CRC");
  assert.ok(f.observations.every((x) => ledger.shipments.some((s) => s.id === x.shipmentId)));
  const latest = [...new Map([...f.observations].sort((a,b) => a.observedAt.localeCompare(b.observedAt)).map((x) => [x.shipmentId, x])).values()];
  assert.ok(latest.every((x) => Number.isInteger(x.amountCRC) && x.amountCRC >= 0));
  assert.equal(new Set(latest.map((x) => x.shipmentId)).size, latest.length);
});
