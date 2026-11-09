# Private dispatch room

The public journal remains on GitHub Pages. `/admin/` links to a separate HTTPS Cloudflare Worker. D1 stores orders, packages and changes; a private KV namespace stores original PDFs. No private records are committed or built into `dist/`.

## Private item tracker

On November 9 the owner explicitly requested a complete, editable HTML tracker in the private admin, separated into **Proyecto** and **Personal**, with **Shipped**, **Miami**, **Costa Rica** and **Entregado** checkboxes. This is a targeted authorization to display item descriptions to the existing authenticated owner `ealfaro29`. It does not authorize public disclosure, personal details in GitHub or project exports, or exposing the protected originals.

The tracker uses a separate `tracking_items` table and owner-only `/api/tracking` endpoints. Its data never enters public source, static assets, the project snapshot/export or project accounting. Checkbox edits use the existing secure owner session, origin checks and optimistic version checks. Owner corrections are stored separately from imported evidence and survive future synchronization. Signing out clears the item view. A blank checkbox means unconfirmed; Miami means receipt by Speedy, and Entregado means receipt by the owner. Local purchases show no shipping phases.

```sh
node backend/sync.mjs tracking-import private/item-tracking-import.json
node backend/sync.mjs tracking-snapshot
```

Keep the item payload and its protected evidence under ignored `private/`. Only an explicit ingestion import can add factual rows; no item data is embedded in the HTML or JavaScript. Apply `0002_item_tracking.sql` before deploying the tracker.

The owner also requested source links and dates beside tracker comments. Each `evidence` entry contains a label, HTTPS source URL, `observedAt`, optional `eventDate` and `eventTime`, and a short explanation. These references are served only with the authenticated item data, never in static assets or project exports. Verification times display in Costa Rica; event times retain the source's stated timezone. A current status without an event date is explicitly undated, and an estimate is labelled as an estimate. Imports that omit evidence preserve existing links. Original attachments remain protected separately.

Outside the explicitly authorized private item tracker, shared-order records use generic titles and omit restricted descriptions, notes, item values and original-document links from owner snapshots and exports. Saved document URLs are also blocked for these records. Stored originals and owner fields are preserved outside the interactive view for authorized ingestion; redaction does not change shipping evidence or readiness. The public site shows only the combined Speedy amount for all current packages, without a project-membership filter or a package-level breakdown. Unquoted charges remain pending.

Empty imported `*-AWAIT` preparation records for fully carrier-delivered orders are excluded from the interactive package view once tracked shipments exist for that order. Manual records and records containing owner notes, documents, prealerts, consolidations or arrivals remain visible. Stored records and the ingestion snapshot are preserved. An untracked portion of a partially fulfilled order stays pending.

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
