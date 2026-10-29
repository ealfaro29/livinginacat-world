# Ledger maintenance

Public source: `data/ledger.json`. USD amounts are integer cents. `null` means unknown. Dates use YYYY-MM-DD. `updatedAt` is the review date, not a live query timestamp.

## Overlapping records: do not add together

- `items`: original equipment list and quotes. Quantity means purchase units, not always individual parts. Quoted total = quantity × quoted unit price.
- `equipmentAllowances`: owner-requested planning amounts, kept separate from item quotes, orders and verified payments. The equipment estimate is item quotes plus these allowances.
- `orders`: vendor-level quote, documentary order total and verified payment where evidence exists. `invoiceTotalCents` is the order amount; `shippingInvoicedCents`, `taxInvoicedCents` and `tariffInvoicedCents` describe its charges. An order confirmation alone does not establish payment. The owner may confirm shipped purchases are paid; record this as owner confirmation rather than bank verification. `actualPaidCents` and the `*PaidCents` fields remain unknown when a reliable amount is unavailable. For a partially shipped order, do not assume the whole order is paid or invent an allocation. For a vendor aggregate, `paymentPartial` marks a subtotal across confirmed paid orders. Paid tax and shipping are breakdowns of the paid total, not additional amounts to add again.
- An `awaiting_invoice` order acknowledges a request awaiting the vendor's final invoice. `invoiceTotalFinal: false` and `shippingChargeFinal: false` distinguish provisional amounts from final charges; neither establishes payment or dispatch.
- `amazonOrders`: anonymized extracts of five real orders. They include equipment and extras. Documentary order totals are distinct from reconciled bank payments.
- `otherExpenses`: domain and grouped **Taxes, tariffs, shipping and others** totals per vendor. `includedInVendorOrderTotals: true` prevents double counting. The grouped total includes documented vendor shipping, taxes, tariffs and other included costs. Keep the underlying actual tax and tariff evidence in the private records; do not describe other purchases as tax. Speedy charges in CRC are separate.
- `forwardingCharges`: dated Speedy amounts in CRC for exactly matched project shipments. Retain observations when amounts change; the latest observation per shipment is the current subtotal. Do not mark them paid or combine with USD totals without evidence, and do not assume the sum is the final consolidation charge. Exclude ambiguous or personal packages.
- `shipments`: real shipped package or preparation record. Planned dispatch is distinct from estimated arrival. Complete `deliveredAt` only with delivery evidence.
- `funding`: preserve unknown amounts until reconciled. Do not publish individual supporters or contributions without authorization.

## Initial evidence

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

Personal or non-itemized purchases belong only in the private owner records. Public records retain their exact amounts under Taxes, tariffs, shipping and others without product names, product identifiers, quantities, photos, invoices or descriptions that reveal those purchases. Preserve actual tax and tariff amounts; do not relabel other purchases as tax. Shipment updates for this category use a generic title. Never copy private admin data or original invoice contents into public source, posts, downloads, screenshots or commit messages. `npm run check` blocks restricted identities before publication.
