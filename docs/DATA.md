# Ledger maintenance

Public source: `data/ledger.json`. USD amounts are integer cents. `null` means unknown. Dates use YYYY-MM-DD. `updatedAt` is the review date, not a live query timestamp.

## Overlapping records: do not add together

- `items`: original equipment list and quotes. Quantity means purchase units, not always individual parts. Quoted total = quantity × quoted unit price.
- `equipmentAllowances`: owner-requested planning amounts, kept separate from item quotes, orders and verified payments. The equipment estimate is item quotes plus these allowances.
- `orders`: vendor-level quote and verified payment where evidence exists. Paid tax and shipping are breakdowns of the paid total, not additional amounts to add again.
- `amazonOrders`: anonymized extracts of five real orders. They include equipment and extras. Documentary order totals are distinct from reconciled bank payments.
- `otherExpenses`: domain and grouped additions. `includedInVendorOrderTotals: true` prevents duplicate counting. The “Taxes and others” category includes added items plus the documented Amazon tax, with a separate breakdown. Discounts are not allocated to that category without evidence.
- `shipments`: real shipped package or preparation record. Planned dispatch is distinct from estimated arrival. Complete `deliveredAt` only with delivery evidence.
- `funding`: preserve unknown amounts until reconciled. Do not publish individual supporters or contributions without authorization.

## Initial evidence

FramingTech: payment email and PDF confirmation. GoDaddy: email receipt. Amazon: authenticated order details, order invoices and tracking pages. Private originals stay outside the repository. AMZ codes are public references independent of actual order numbers.

## Updating

1. Read current evidence and retain its original reference privately.
2. Update only verified fields, preserving uncertainty.
3. Add a `changes` entry with date, title and detail. Record verified cancellation, refund or return amounts explicitly; retain history rather than silently deleting records.
4. Run arithmetic and relationship tests. Expand checks when the data model changes.
5. Regenerate and compare CSV, JSON, Markdown and HTML against the same source.
6. Commit, publish and verify live. Journal posts remain dated snapshots; tables show the latest record.

Maintaining this ledger does not authorize purchases, payment-method changes, outgoing email or recurring monitoring.
