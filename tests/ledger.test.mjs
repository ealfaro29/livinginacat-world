import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs/promises";
import { createHash } from "node:crypto";
import { readJSON, root, totals, activeShipments } from "../scripts/lib.mjs";
const ledger = await readJSON("data/ledger.json");
test("equipment estimate reconciles item quotes, vendors and planning allowances", () => {
  assert.equal(
    new Set(ledger.items.map((x) => x.id)).size,
    ledger.items.length,
  );
  assert.equal(ledger.items.length, 74);
  for (const x of ledger.items) {
    if (x.quotedUnitCents == null) assert.equal(x.quotedTotalCents, null, x.id);
    else assert.equal(x.quotedUnitCents * x.quantity, x.quotedTotalCents, x.id);
  }
  for (const o of ledger.orders) {
    if (["cancelled", "canceled"].includes(o.status)) continue;
    if (o.quotedSubtotalCents == null) {
      assert.ok(ledger.items.filter((x) => x.orderId === o.id).every((x) => x.quotedTotalCents === null));
      continue;
    }
    assert.equal(
      ledger.items
        .filter((x) => x.orderId === o.id)
        .reduce((n, x) => n + x.quotedTotalCents, 0),
      o.quotedSubtotalCents,
      o.vendor,
    );
  }
  assert.equal(totals(ledger).quotedItems, 236451);
  assert.equal(totals(ledger).unquotedItems, 1);
  assert.equal(totals(ledger).equipmentAllowance, 50000);
  assert.equal(totals(ledger).quoted, 286451);
  assert.equal(totals(ledger).quoted, ledger.equipmentQuotedTotalCents);
  assert.ok(
    ledger.equipmentAllowances.every((x) => x.actualPaidCents === null),
  );
});
test("Amazon invoices reconcile without counting grouped extras twice", () => {
  for (const o of ledger.amazonOrders.filter((o) => o.costVisibility !== "vendor_grouped"))
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
    totals(ledger).amazon - extra.categoryTotalCents,
    115266,
  );
  assert.equal(totals(ledger).amazon, 159816);
  assert.equal(
    ledger.orders.find((x) => x.id === "amazon").invoiceTotalCents,
    totals(ledger).amazon,
  );
  assert.equal(ledger.amazonOrders.flatMap((x) => x.itemIds).length, 37);
});
test("Amazon controller Speedy receipt stays separate from carrier delivery and bank settlement", () => {
  const order = ledger.amazonOrders.find((o) => o.id === "AMZ-07");
  const item = ledger.items.find((i) => i.id === "vxb-044");
  const shipment = ledger.shipments.find((s) => s.orderRef === order.id);
  assert.equal(order.status, "carrier_delivered");
  assert.equal(order.orderTotalCents, 6366);
  assert.equal(order.actualPaidCents, null);
  assert.equal(order.invoiceVerified, false);
  assert.equal(order.purchaseReceiptVerified, true);
  assert.equal(order.merchantChargeStatus, "completed");
  assert.equal(order.bankSettlementConfirmed, false);
  assert.equal(order.costVisibility, "vendor_grouped");
  for (const key of ["invoiceItemsCents", "shippingCents", "shippingCreditCents", "discountCents", "taxCents"])
    assert.equal(Object.hasOwn(order, key), false, "shared-order components stay private");
  assert.equal(item.orderId, "amazon");
  assert.equal(item.orderUnitCents, 3950);
  assert.equal(item.previousProcurement.orderId, "vxb");
  assert.equal(item.previousProcurement.quotedTotalCents, 6095);
  assert.equal(ledger.orders.find((o) => o.id === "vxb").status, "cancelled");
  assert.equal(ledger.orders.find((o) => o.id === "amazon").paymentPartial, true);
  assert.equal(shipment.status, "carrier_delivered");
  assert.equal(shipment.carrierDeliveredDate, "2026-11-10");
  assert.equal(shipment.trackingAssigned, true);
  assert.equal(shipment.carrier, "Amazon");
  assert.equal(shipment.expectedDeliveryDate, "2026-11-10");
  assert.equal(shipment.prealertStatus, "confirmed");
  assert.equal(shipment.consolidationStatus, "confirmed");
  assert.equal(shipment.speedyStatus, "received");
  assert.equal(shipment.speedyLocation, "miami");
  assert.equal(shipment.speedyCheckedAt, "2026-11-11");
  assert.equal(shipment.deliveredAt, null);
});
test("owner-confirmed shipped payments are included without assuming delivery", () => {
  assert.equal(totals(ledger).verifiedPaid, 340808);
  assert.equal(totals(ledger).shipped, 22);
  assert.equal(
    ledger.amazonOrders.filter((x) => x.status === "payment_attention").length,
    0,
  );
  assert.equal(ledger.amazonOrders.filter((x) => x.actualPaidCents != null).length, 6);
  assert.equal(ledger.amazonOrders.find((x) => x.id === "AMZ-04").actualPaidCents, ledger.amazonOrders.find((x) => x.id === "AMZ-04").orderTotalCents);
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
test("DigiKey cancellation preserves documentary charges without assuming a payment or refund", () => {
  const order = ledger.orders.find((x) => x.id === "digikey");
  assert.equal(order.status, "cancelled");
  assert.equal(order.invoiceTotalCents, 9697);
  assert.equal(
    order.invoiceTotalCents,
    7736 + order.shippingInvoicedCents + order.taxInvoicedCents + order.tariffInvoicedCents,
  );
  assert.equal(order.actualPaidCents, null);
  assert.equal(order.refundCents, null);
  assert.equal(totals(ledger).confirmedOrderTotal, 352505);
  assert.equal(order.shippingPaidCents, null);
  assert.equal(order.taxPaidCents, null);
  assert.equal(order.tariffPaidCents, null);
});
test("VXB cancellation retains its original amounts and vendor-reported refund outside active tracking", () => {
  const order = ledger.orders.find((x) => x.id === "vxb");
  const historicalShipment = ledger.shipments.find((x) => x.id === "VXB-PKG-01");
  assert.equal(order.status, "cancelled");
  assert.equal(order.invoiceTotalCents, 6522);
  assert.equal(order.refundCents, 6522);
  assert.equal(order.refundStatus, "vendor_reported");
  assert.equal(order.refundBankSettlementConfirmed, false);
  assert.equal(order.actualPaidCents, null);
  assert.equal(historicalShipment.status, "cancelled");
  assert.equal(historicalShipment.trackingAssigned, true);
  assert.ok(!activeShipments(ledger).some((x) => x.id === historicalShipment.id));
  assert.equal(ledger.otherExpenses.find((x) => x.vendor === "VXB").status, "cancelled");
  assert.equal(totals(ledger).taxesAndOthers, 126677);
});
test("Walmart receipt advances only the independently verified fulfillment group", () => {
  assert.equal(ledger.orders.find((x) => x.id === "walmart").status, "carrier_delivered");
  for (const id of ["WMT-PKG-02", "WMT-PKG-03"]) {
    const shipment = ledger.shipments.find((x) => x.id === id);
    assert.equal(shipment.status, "carrier_delivered");
    assert.equal(shipment.deliveredAt, null);
  }
  const wrap = ledger.shipments.find((x) => x.id === "WMT-PKG-03");
  assert.equal(wrap.speedyStatus, "received");
  assert.equal(wrap.speedyLocation, "miami");
  assert.match(wrap.speedyConfirmedAt, /^2026-11-10T/);
  const foam = ledger.shipments.find((x) => x.id === "WMT-PKG-02");
  assert.equal(foam.speedyStatus, "delivered");
  assert.equal(foam.speedyLocation, null);
  assert.equal(foam.recipientDeliverySource, "owner_confirmation");
  assert.equal(foam.recipientDeliveryConfirmedAt, "2026-11-11");
  assert.match(foam.notes, /date.*not specified/i);
  assert.equal(ledger.shipments.find((x) => x.id === "WMT-PKG-03").carrierDeliveredDate, "2026-11-06");
  assert.equal(ledger.shipments.find((x) => x.id === "WMT-PKG-02").carrierDeliveredDate, undefined);
});
test("BoltDepot receipt reconciles owner-selected spares and charges", () => {
  const order = ledger.orders.find((x) => x.id === "boltdepot");
  const items = ledger.items.filter((x) => x.orderId === order.id);
  assert.equal(items.length, 13);
  assert.equal(items.reduce((sum, x) => sum + x.quantity, 0), 182);
  assert.equal(items.reduce((sum, x) => sum + x.quotedTotalCents, 0), 1604);
  assert.equal(order.status, "carrier_delivered");
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
  assert.equal(order.status, "carrier_delivered");
  assert.equal(order.invoiceItemsCents, order.quotedSubtotalCents + extra.categoryTotalCents - order.taxInvoicedCents);
  assert.equal(order.invoiceTotalCents, order.invoiceItemsCents + order.taxInvoicedCents);
  assert.equal(order.invoiceTotalCents, 5331);
  assert.equal(extra.includedInVendorOrderTotals, true);
  assert.ok(extra.categoryTotalCents >= order.taxInvoicedCents);
  assert.equal(totals(ledger).taxesAndOthers, 126677);
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
  assert.equal(confirmedOrders + 419, 315024);
  assert.equal(totals(ledger).confirmedOrderTotal, confirmedOrders + 419 + 53700 - ledger.orders.find((x) => x.id === "digikey").invoiceTotalCents - ledger.orders.find((x) => x.id === "vxb").invoiceTotalCents);
  assert.equal(order.actualPaidCents, 88186);
});
test("Mouser Speedy receipt preserves invoice, cancellation and unconfirmed recipient delivery", () => {
  const order = ledger.orders.find((x) => x.id === "mouser");
  const replaced = ledger.orders.find((x) => x.id === order.replacesOrderId);
  const items = ledger.items.filter((x) => x.orderId === order.id);
  const costs = ledger.otherExpenses.find((x) => x.id === "mouser-charges-grouped");
  assert.equal(order.status, "shipped");
  assert.equal(replaced.status, "cancelled");
  assert.equal(replaced.quotedSubtotalCents, 7736);
  assert.equal(replaced.invoiceTotalCents, 9697);
  assert.equal(items.length, 10);
  assert.ok(items.every((x) => x.quantity === 1 && x.procurementStatus === "shipped" && x.previousProcurement.orderId === "digikey"));
  assert.equal(items.reduce((sum, x) => sum + x.orderUnitCents, 0), 6444);
  assert.match(items.find((x) => x.id === "digikey-045").name, /S301T/);
  assert.equal(order.orderConfirmationTotalCents, 8207);
  assert.equal(order.invoiceTotalCents, 8722);
  assert.equal(order.invoiceTotalFinal, true);
  assert.equal(costs.name, "Taxes, tariffs, shipping and others");
  assert.equal(costs.categoryTotalCents, 2278);
  assert.equal(order.invoiceItemsCents + costs.categoryTotalCents, order.invoiceTotalCents);
  assert.equal(costs.includedInVendorOrderTotals, true);
  assert.equal(order.actualPaidCents, 8722);
  assert.equal(order.bankSettlementConfirmed, false);
  assert.match(order.paymentEvidence, /vendor final invoice/);
  assert.equal(costs.actualPaidCents, null);
  const shipment = ledger.shipments.find((x) => x.orderRef === "MOUSER-01");
  assert.equal(shipment.status, "carrier_delivered");
  assert.equal(shipment.carrierDeliveredDate, "2026-11-09");
  assert.equal(shipment.carrier, "FedEx");
  assert.equal(shipment.trackingAssigned, true);
  assert.equal(shipment.invoiceVerified, true);
  assert.equal(shipment.speedyLocation, "miami");
  assert.equal(shipment.speedyStatus, "received");
  assert.match(shipment.speedyConfirmedAt, /^2026-11-10T/);
  assert.equal(shipment.deliveredAt, null);
});
test("planned local wire purchase remains unquoted, unbought and outside the import queue", () => {
  const wire = ledger.items.find((x) => x.id === "digikey-048");
  const plan = ledger.orders.find((x) => x.id === wire.orderId);
  assert.equal(wire.procurementStatus, "pending");
  assert.equal(wire.plannedPurchaseDate, "2026-11-06");
  assert.equal(wire.quotedUnitCents, null);
  assert.equal(wire.quotedTotalCents, null);
  assert.equal(wire.actualPaidCents, null);
  assert.equal(plan.status, "pending");
  assert.equal(plan.orderedAt, null);
  assert.equal(plan.invoiceTotalCents, null);
  assert.equal(wire.previousProcurement.quotedTotalCents, 1715);
  assert.ok(ledger.shipments.every((x) => !x.itemIds.includes(wire.id)));
});
test("standalone project costs are counted once without adding an order or shipment", () => {
  const expense = ledger.otherExpenses.find((x) => x.id === "techstorex-project-others");
  assert.equal(expense.categoryTotalCents, 53700);
  assert.equal(expense.actualPaidCents, 53700);
  assert.equal(expense.includedInVendorOrderTotals, false);
  assert.equal(expense.shippingRequired, false);
  const before = totals({ ...ledger, otherExpenses: ledger.otherExpenses.filter((x) => x.id !== expense.id) });
  const after = totals(ledger);
  assert.equal(after.verifiedPaid - before.verifiedPaid, 53700);
  assert.equal(after.confirmedOrderTotal - before.confirmedOrderTotal, 53700);
  assert.equal(after.taxesAndOthers - before.taxesAndOthers, 53700);
  assert.ok(ledger.orders.every((x) => x.vendor !== expense.vendor));
  assert.ok(ledger.shipments.every((x) => x.vendor !== expense.vendor));
  assert.equal(after.shipped, before.shipped);
  assert.equal(after.tracked, before.tracked);
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

test("combined forwarder total stays in colones without exposing package details", () => {
  const f = ledger.forwardingCharges;
  assert.equal(f.currency, "CRC");
  assert.ok(f.quoteStatus === "reconciliation_pending"
    ? f.amountCRC === null
    : Number.isInteger(f.amountCRC) && f.amountCRC >= 0);
  assert.equal(f.scope, "all_current_packages");
  assert.ok(["currently_quoted", "awaiting_remaining_quotes", "reconciliation_pending"].includes(f.quoteStatus));
  assert.equal(f.payment, "unconfirmed");
  assert.equal(f.finalConsolidatedChargeConfirmed, false);
  const allowed = new Set(["currency", "amountCRC", "source", "observedAt", "verifiedAt", "scope", "quoteStatus", "payment", "finalConsolidatedChargeConfirmed", "notes"]);
  assert.ok(Object.keys(f).every((key) => allowed.has(key)), "individual forwarding records must stay private");
  assert.ok(Object.values(f).every((value) => value === null || typeof value !== "object"));
});

test("project locations distinguish Speedy progress from carrier delivery", () => {
  assert.equal(totals(ledger).tracked, 22);
  for (const s of ledger.shipments) {
    assert.equal(typeof s.trackingAssigned, "boolean");
    assert.ok(["received", "in_transit", "delivered", "unconfirmed"].includes(s.speedyStatus));
    assert.match(s.speedyCheckedAt, /^\d{4}-\d{2}-\d{2}$/);
    if (s.speedyLocation === "miami") assert.equal(s.speedyStatus, "received");
    else if (s.speedyLocation === "costa_rica") assert.equal(s.speedyStatus, "in_transit");
    else assert.equal(s.speedyLocation, null);
    if (s.speedyLocation) assert.ok(s.speedyConfirmedAt);
    if (s.speedyStatus !== "delivered") assert.equal(s.deliveredAt, null);
  }
});

test("a confirmed carrier return keeps recipient delivery and reimbursement unconfirmed", () => {
  const shipment = ledger.shipments.find((x) => x.id === "BAMBU-PKG-01");
  assert.equal(shipment.status, "returned");
  assert.equal(shipment.speedyStatus, "unconfirmed");
  assert.equal(shipment.deliveredAt, null);
  assert.equal(shipment.expectedDeliveryDate, null);
  assert.equal(shipment.replacementStatus, "shipped");
  assert.equal(shipment.replacementTrackingAssigned, true);
  assert.equal(shipment.trackingAssigned, true);
  assert.ok(ledger.orders.find((x) => x.id === "bambu-lab").actualPaidCents > 0);
  assert.equal(totals(ledger).shipped, 22);
});
