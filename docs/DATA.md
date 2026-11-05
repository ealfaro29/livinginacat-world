# Ledger maintenance

Public source: `data/ledger.json`. USD amounts are integer cents. `null` means unknown. Dates use YYYY-MM-DD. `updatedAt` is the review date, not a live query timestamp.

## Overlapping records: do not add together

- `items`: original equipment list and quotes. Quantity means purchase units, not always individual parts. Quoted total = quantity × quoted unit price.
- `equipmentAllowances`: owner-requested planning amounts, kept separate from item quotes, orders and verified payments. The equipment estimate is item quotes plus these allowances.
- `orders`: vendor-level quote, documentary order total and verified payment where evidence exists. `invoiceTotalCents` is the order amount; `shippingInvoicedCents`, `taxInvoicedCents` and `tariffInvoicedCents` describe its charges. An order confirmation alone does not establish payment. The owner may confirm shipped purchases are paid; record this as owner confirmation rather than bank verification. `actualPaidCents` and the `*PaidCents` fields remain unknown when a reliable amount is unavailable. For a partially shipped order, do not assume the whole order is paid or invent an allocation. For a vendor aggregate, `paymentPartial` marks a subtotal across confirmed paid orders. Paid tax and shipping are breakdowns of the paid total, not additional amounts to add again.
- An `awaiting_invoice` order acknowledges a request awaiting the vendor's final invoice. `invoiceTotalFinal: false` and `shippingChargeFinal: false` distinguish provisional amounts from final charges; neither establishes payment or dispatch.
- `amazonOrders`: anonymized extracts of confirmed orders. They include equipment and extras. Documentary order totals are distinct from reconciled bank payments. When complete carrier fulfillment is verified, the owner's existing confirmation that shipped purchases are paid can cover the documented total; retain the owner-confirmation source and the bank-settlement caveat.
- `otherExpenses`: domain and grouped **Taxes, tariffs, shipping and others** totals per vendor. `includedInVendorOrderTotals: true` prevents double counting. The grouped total includes documented vendor shipping, taxes, tariffs and other included costs. Keep the underlying actual tax and tariff evidence in the private records; do not describe other purchases as tax. Speedy charges in CRC are separate.
- `forwardingCharges`: one dated combined Speedy amount in CRC for **all current packages**, with no filter by project membership. Review the entire current account and all current consolidations, including packages not yet quoted. Review active `Recibido`, `En Costa Rica` and `Enviado` queues without filtering charges by a known consolidation, project match or earlier review. `Enviado` alone does not prove payment. Exclude records confirmed `Pagado` or `Entregado` unless newer evidence establishes an outstanding charge. Use `aggregateForwardingCharges` to sum every quoted current package once; unquoted packages keep `quoteStatus: awaiting_remaining_quotes` and must never be treated as free or omitted from the review. Publish only the combined amount, currency, observation date, coverage and payment/finality caveats. Package identities, counts, weights, individual charges, matching evidence and the complete observation history stay outside user-facing views. The owner explicitly requires this full scope. Do not add restricted package details to project records or location counts. Do not mark the amount paid or combine it with USD totals without evidence, and do not assume it is the final consolidated balance.
- `shipments`: real project shipment or preparation record. `trackingAssigned` records that the private project shipment has a verified assigned number; the number itself stays private. It does not establish carrier acceptance, Speedy receipt or recipient delivery. `status` describes the carrier; `speedyStatus` describes separately confirmed forwarder progress. `speedyLocation` is `miami` or `costa_rica` only when Speedy's exact tracking entry supports it; otherwise it is `null`. `speedyCheckedAt` records the review date, and `speedyConfirmedAt` records the latest affirmative observation. Planned dispatch is distinct from estimated arrival. Complete `deliveredAt` only with recipient-delivery evidence. A suffix-only tracking match is insufficient for a project location assertion.
- `funding`: preserve unknown amounts until reconciled. Do not publish individual supporters or contributions without authorization.

Cancelled orders retain their original documentary amounts and grouped charges, with unknown payments and refunds unchanged. Exclude them from active order totals, active grouped-cost summaries and the tracking queue. Cancellation does not itself establish a refund. The equipment list remains a planning record until a replacement order is confirmed.

## Initial evidence

Carrier returns use `shipments.status: returned` and remain separate from recipient delivery, refunds and replacements. Keep the original purchase and payment evidence. A return still counts as a reported shipment; it appears in the carrier-return group instead of the queue awaiting Speedy confirmation. The private carrier record uses `on_hold` with the verified return evidence.

FramingTech: payment email and PDF confirmation. GoDaddy: email receipt. Amazon: authenticated order details, order invoices and tracking pages. DigiKey and BoltDepot: vendor order confirmation emails, without shipment or settled-payment evidence. Walmart: confirmation email and authenticated order details; fulfillment groups at Placed status and estimated arrival windows are not dispatched packages. Private originals stay outside the repository. AMZ codes are public references independent of actual order numbers.

## Updating

1. Read current evidence and retain its original reference privately.
2. Update only verified fields, preserving uncertainty.
3. Add a `changes` entry with date, title and detail. Record verified cancellation, refund or return amounts explicitly; retain history rather than silently deleting records.
4. Run arithmetic and relationship tests. Expand checks when the data model changes.
5. Regenerate and compare CSV, JSON, Markdown and HTML against the same source.
6. Commit, publish and verify live. Journal posts remain dated snapshots; tables show the latest record.

Maintaining this ledger does not authorize purchases, payment-method changes, outgoing email or recurring monitoring.

## Public and private boundary

Never mention or display personal purchase details in messages, the public site, downloads or the interactive owner room. Preserve operational evidence outside those views; shared-order originals are not downloadable through the owner room. Public records retain their exact grouped amounts under Taxes, tariffs, shipping and others without product names, product identifiers, quantities, photos, invoices or descriptions that reveal those purchases. Preserve actual tax and tariff amounts; do not relabel other purchases as tax. Shipment updates for this category use a generic title. Never copy private admin data or original invoice contents into public source, posts, downloads, screenshots or commit messages. `npm run check` blocks restricted identities before publication.
