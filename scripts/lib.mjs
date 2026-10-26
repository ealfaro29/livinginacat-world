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
export const labels = {
  pending: "Not ordered",
  deferred: "Deferred",
  ordered: "Order confirmed",
  shipped: "Shipped",
  preparing: "Preparing",
  payment_attention: "Payment review",
  partial_payment_attention: "3 orders: payment review",
  partially_shipped_payment_attention: "Mixed status",
};
export function totals(ledger) {
  return {
    quoted: ledger.items.reduce((n, x) => n + x.quotedTotalCents, 0),
    verifiedPaid: [...ledger.orders, ...ledger.otherExpenses].reduce(
      (n, x) => n + (x.actualPaidCents ?? 0),
      0,
    ),
    amazon: ledger.amazonOrders.reduce((n, x) => n + x.orderTotalCents, 0),
    shipped: ledger.shipments.filter((x) => x.status === "shipped").length,
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
