# Private dispatch room

The public journal remains on GitHub Pages. `/admin/` links to a separate HTTPS Cloudflare Worker. D1 stores orders, packages and changes; a private KV namespace stores original PDFs. No private records are committed or built into `dist/`.

## Owner workflow

Open the one-time activation link locally and choose a password (14–128 characters). The owner username is `ealfaro29`. Subsequent visits use the sign-in form. Sessions last 12 hours. There is no public signup. Production is locked to owner `ealfaro29`; `OWNER_SETUP_ENABLED=false` also closes the original activation endpoint. A fresh deployment must explicitly enable one-time setup and close it after activation. Use **Add package** when a store splits an order, **Edit details** to record a submitted Speedy prealert or confirmed locker arrival, and **Attach PDF** to keep the original invoice. These actions synchronize across devices. A version conflict requires refreshing before saving; it does not silently overwrite another device.

**Ready to prealert** requires a carrier, tracking number and PDF classified as an invoice/purchase receipt. A provisional invoice or plain order confirmation remains visibly incomplete. An ETA is never treated as an arrival. Marking a prealert in this panel does not submit it to Speedy. Consolidation and prealert actions must be verified in Speedy's own UI.

## Deploy

```sh
npm ci
npm test
npx wrangler d1 migrations apply livinginacat-admin --remote --config backend/wrangler.jsonc
npx wrangler deploy --config backend/wrangler.jsonc
```

Worker secrets `SETUP_TOKEN_HASH` and `INGEST_TOKEN_HASH` contain only SHA-256 digests of independently generated 256-bit random tokens. Original tokens live in ignored `private/admin-credentials.json` (mode 0600). Do not paste them into issues, logs, URLs with query strings, public guides or Git. The setup key is sent to the browser in a URL fragment and removed immediately. Setup is disabled atomically after the first owner is created. A lost password requires an explicit, owner-authorized reset; there is no insecure public reset endpoint.

The ingestion token can read the private sync snapshot and import vendor evidence or PDFs. It cannot log into the owner UI, change owner notes, clear prealerts or mark locker arrivals. A separate `confirm-speedy` command can append tracking-matched prealert, consolidation and package-status evidence after verification in Speedy. A `status_confirmed` event carries `packageId`, matching `tracking`, `status` (`received`, `in_transit`, or `delivered`), `source`, and `verifiedAt`. It preserves owner fields, ignores older or regressive status updates, and uses the observation time for `lockerArrivedAt` when Speedy reports receipt. Carrier delivery and Speedy receipt are separate facts. Imports preserve those fields and ignore older vendor evidence. Tracking numbers are unique. PDF originals are immutable; replacing the active attachment preserves earlier evidence in private storage.

```sh
node backend/sync.mjs import private/order-import.json
node backend/sync.mjs upload PACKAGE-ID private/invoices/vendor.pdf invoice
node backend/sync.mjs snapshot
```

Keep import JSON and all PDF files under ignored `private/`. Use `order_confirmation` or `provisional_invoice` when appropriate. Do not fabricate vendor invoices. JSON export is authenticated and contains order/package metadata and recent activity; download PDFs separately. D1 Time Travel and immutable document keys provide recovery within the account's configured retention. No automatic email access is embedded in the website; a separately authorized Codex monitor can reconcile evidence using the ingestion helper.

## Verification

`tests/admin.test.mjs` exercises the Worker against isolated local D1 and KV: authentication, one-time setup, cookie settings, cross-device persistence, stale-save conflicts, CSRF rejection, ingestion permissions, duplicate tracking rejection, PDF access and sign-out. Tests contain disposable fixtures only. Do not insert test users or fake shipments into production.
