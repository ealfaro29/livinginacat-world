import fs from "node:fs/promises";
import { fileURLToPath } from "node:url";
export const root = new URL("../", import.meta.url);
export const rootPath = fileURLToPath(root);
export const readJSON = async (p) =>
  JSON.parse(await fs.readFile(new URL(p, root), "utf8"));
export const money = (cents) =>
  cents == null
    ? "Unconfirmed"
    : new Intl.NumberFormat("en-US", {
        style: "currency",
        currency: "USD",
        currencyDisplay: "narrowSymbol",
      }).format(cents / 100);
export const esc = (s) =>
  String(s ?? "").replace(
    /[&<>"']/g,
    (c) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[
        c
      ],
  );
export const date = (value) =>
  value
    ? new Intl.DateTimeFormat("en-US", {
        day: "numeric",
        month: "long",
        year: "numeric",
        timeZone: "UTC",
      }).format(new Date(value + "T12:00:00Z"))
    : "Unconfirmed";
export const dateTime = (value, timeZone = "America/Costa_Rica") =>
  value
    ? new Intl.DateTimeFormat("en-US", {
        dateStyle: "long",
        timeStyle: "short",
        timeZone,
      }).format(new Date(value)) +
      ` (${timeZone === "America/Costa_Rica" ? "Costa Rica" : timeZone})`
    : "Unconfirmed";
export function shipmentCarrierDate(shipment) {
  if (shipment.status === "carrier_delivered")
    return { label: "Carrier delivery", value: shipment.carrierDeliveredDate ?? null, confirmed: true };
  if (shipment.status === "returned")
    return { label: "Carrier return", value: shipment.carrierReturnedDate ?? null, confirmed: true };
  if (shipment.expectedDeliveryDate)
    return { label: "Estimated carrier arrival", value: shipment.expectedDeliveryDate, confirmed: false };
  return { label: "Planned dispatch", value: shipment.expectedShipDate ?? null, confirmed: false };
}
export const labels = {
  pending: "Not ordered",
  deferred: "Deferred",
  awaiting_invoice: "Awaiting final invoice",
  ordered: "Order confirmed",
  shipped: "Shipped",
  carrier_delivered: "Carrier reports delivery",
  returned: "Returned to sender",
  on_hold: "Carrier exception",
  cancelled: "Cancelled",
  canceled: "Cancelled",
  preparing: "Preparing",
  payment_attention: "Payment review",
  partial_payment_attention: "3 orders: payment review",
  partially_shipped_payment_attention: "Mixed status",
  partially_shipped: "Partially shipped",
};
export function activeShipments(ledger) {
  const cancelledOrders = new Set(ledger.orders
    .filter((order) => ["cancelled", "canceled"].includes(order.status))
    .map((order) => order.id));
  return ledger.shipments.filter((shipment) =>
    !cancelledOrders.has(shipment.orderRef) &&
    !["cancelled", "canceled"].includes(shipment.status));
}
export function totals(ledger) {
  const shipments = activeShipments(ledger);
  const quotedItems = ledger.items.reduce((n, x) => n + (x.quotedTotalCents ?? 0), 0);
  const unquotedItems = ledger.items.filter((x) => x.quotedTotalCents == null).length;
  const equipmentAllowance = (ledger.equipmentAllowances ?? []).reduce(
    (n, x) => n + x.amountCents,
    0,
  );
  return {
    quotedItems,
    unquotedItems,
    confirmedOrderTotal:
      ledger.orders
        .filter((x) => x.invoiceTotalCents != null && x.invoiceTotalFinal !== false && !["pending", "deferred", "awaiting_invoice", "cancelled", "canceled"].includes(x.status))
        .reduce((n, x) => n + x.invoiceTotalCents, 0) +
      ledger.otherExpenses
        .filter((x) => !x.includedInVendorOrderTotals && x.actualPaidCents != null)
        .reduce((n, x) => n + x.actualPaidCents, 0),
    equipmentAllowance,
    quoted: quotedItems + equipmentAllowance,
    taxesAndOthers: ledger.otherExpenses
      .filter((x) => x.name === "Taxes, tariffs, shipping and others" && !["cancelled", "canceled"].includes(x.status))
      .reduce((sum, x) => sum + x.categoryTotalCents, 0),
    verifiedPaid: [...ledger.orders, ...ledger.otherExpenses].reduce(
      (n, x) => n + (x.actualPaidCents ?? 0),
      0,
    ),
    amazon: ledger.amazonOrders.reduce((n, x) => n + x.orderTotalCents, 0),
    shipped: shipments.filter((x) => ["shipped", "carrier_delivered", "returned"].includes(x.status)).length,
    tracked: shipments.filter((x) => x.trackingAssigned === true).length,
  };
}
export function csv(rows) {
  return (
    "\uFEFF" +
    rows
      .map((row) =>
        row
          .map((value) => '"' + String(value ?? "").replaceAll('"', '""') + '"')
          .join(","),
      )
      .join("\r\n") +
    "\r\n"
  );
}
