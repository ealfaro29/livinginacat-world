import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs/promises";
import path from "node:path";
import { createHash } from "node:crypto";
import { Miniflare, convertV4MiniflareOptions } from "miniflare";
import { ready, mergeImport, editPackage, projectRoomSnapshot, trackingItemFacts, mergeTrackingFacts } from "../backend/model.mjs";
import worker from "../backend/worker.mjs";
const hash = (x) => createHash("sha256").update(x).digest("hex");
test("private admin protects evidence and persists versioned changes", async (t) => {
  const mf = new Miniflare(
    convertV4MiniflareOptions({
      modules: [
        { type: "ESModule", path: path.resolve("backend/worker.mjs") },
        { type: "ESModule", path: path.resolve("backend/model.mjs") },
      ],
      compatibilityDate: "2026-10-26",
      d1Databases: ["DB"],
      kvNamespaces: ["DOCUMENTS"],
      bindings: {
        SETUP_TOKEN_HASH: hash("test-setup-only"),
        OWNER_SETUP_ENABLED: "true",
        INGEST_TOKEN_HASH: hash("test-ingest-only"),
      },
      ratelimits: {
        LOGIN_RATE: {
          simple: { limit: 100, period: 60 },
          namespace_id: "63840",
        },
      },
    }),
  );
  t.after(() => mf.dispose());
  const db = await mf.getD1Database("DB");
  const schema = (await Promise.all(["0001_admin.sql", "0002_item_tracking.sql"].map((file) => fs.readFile("backend/migrations/" + file, "utf8")))).join("\n");
  for (const statement of schema
    .split(";")
    .map((x) => x.trim())
    .filter(Boolean))
    await db.prepare(statement).run();
  const request = async (
    route,
    { cookie, service, method = "GET", payload, headers = {}, raw } = {},
  ) => {
    const r = await mf.dispatchFetch("https://admin.test" + route, {
      method,
      headers: {
        ...(cookie ? { Cookie: cookie } : {}),
        ...(service ? { Authorization: "Bearer test-ingest-only" } : {}),
        ...(payload ? { "Content-Type": "application/json" } : {}),
        ...headers,
      },
      body: raw ?? (payload ? JSON.stringify(payload) : undefined),
    });
    return { r, status: r.status, json: () => r.json() };
  };
  for (const route of [
    "/api/snapshot",
    "/api/export",
    "/api/ingest/snapshot",
    "/api/tracking",
    "/api/ingest/tracking",
    "/api/documents/" + "a".repeat(64),
  ])
    assert.equal((await request(route)).status, 401, route);
  assert.equal(
    (await request("/api/ingest", { method: "POST", payload: { orders: [] } }))
      .status,
    401,
  );
  assert.equal(
    (
      await request("/api/setup", {
        method: "POST",
        payload: { key: "wrong", password: "test-only-long-password" },
      })
    ).status,
    403,
  );
  assert.equal(
    (
      await request("/api/setup", {
        method: "POST",
        payload: { key: "test-setup-only", password: "short" },
      })
    ).status,
    400,
  );
  const setup = await request("/api/setup", {
    method: "POST",
    payload: { key: "test-setup-only", password: "test-only-long-password" },
  });
  assert.equal(setup.status, 200);
  const cookie = setup.r.headers.get("set-cookie").split(";")[0];
  for (const flag of ["Secure", "HttpOnly", "SameSite=Strict", "Path=/"])
    assert.ok(setup.r.headers.get("set-cookie").includes(flag));
  assert.equal(
    (
      await request("/api/setup", {
        method: "POST",
        payload: {
          key: "test-setup-only",
          password: "test-only-long-password",
        },
      })
    ).status,
    409,
  );
  assert.equal(
    (
      await request("/api/login", {
        method: "POST",
        payload: { username: "ealfaro29", password: "incorrect" },
      })
    ).status,
    401,
  );
  const login = await request("/api/login", {
    method: "POST",
    payload: { username: "ealfaro29", password: "test-only-long-password" },
  });
  assert.equal(login.status, 200);
  const device2 = login.r.headers.get("set-cookie").split(";")[0];
  const itemImport = { items: [
    { id: "fixture-project-item", scope: "project", title: "Project fixture item", vendor: "Fixture store", quantity: "1", stages: { shipped: true }, source: "Fixture evidence", sourceCheckedAt: "2026-11-09T00:00:00Z", evidence: [{ label: "Carrier confirmation", url: "https://carrier.example/track/fixture", eventLabel: "Carrier delivery", eventDate: "2026-10-31", eventTime: "9:40 AM (Miami)", observedAt: "2026-11-09T00:00:00Z" }] },
    { id: "fixture-personal-item", scope: "personal", title: "Private fixture item", vendor: "Fixture store", quantity: "1", stages: { shipped: true, miami: true }, source: "Fixture evidence", sourceCheckedAt: "2026-11-09T00:00:00Z", tracking: "MUST_NOT_APPEAR", document: { url: "MUST_NOT_APPEAR" } },
    { id: "fixture-local-item", scope: "project", title: "Local fixture item", shippingRequired: false, sourceCheckedAt: "2026-11-09T00:00:00Z" },
  ] };
  assert.equal((await request("/api/ingest/tracking", { method: "POST", service: true, payload: itemImport })).status, 200);
  assert.equal((await request("/api/tracking", { service: true })).status, 401, "ingestion token cannot access owner endpoint");
  let itemView = await (await request("/api/tracking", { cookie })).json();
  assert.equal(itemView.items.length, 3);
  assert.equal(itemView.items.find((x) => x.id === "fixture-project-item").evidence[0].eventDate, "2026-10-31");
  assert.equal(itemView.items.find((x) => x.id === "fixture-project-item").evidence[0].url, "https://carrier.example/track/fixture");
  assert.equal(itemView.items.find((x) => x.scope === "personal").title, "Private fixture item");
  assert.equal(JSON.stringify(itemView).includes("MUST_NOT_APPEAR"), false, "raw tracking and original documents are not part of the item view");
  const itemPatch = (cookie, phase, value, version, headers = {}) => request("/api/tracking/fixture-project-item", { method: "PATCH", cookie, payload: { phase, value, version }, headers });
  assert.equal((await itemPatch(cookie, "miami", true, 1, { Origin: "https://hostile.example" })).status, 403);
  assert.equal((await request("/api/tracking/fixture-project-item", { method: "PATCH", service: true, payload: { version: 1, phase: "miami", value: true } })).status, 401);
  assert.equal((await itemPatch(cookie, "miami", true, 1)).status, 200);
  assert.equal((await itemPatch(device2, "delivered", true, 1)).status, 409, "stale second-device edits cannot overwrite a mark");
  itemView = await (await request("/api/tracking", { cookie: device2 })).json();
  assert.equal(itemView.items.find((x) => x.id === "fixture-project-item").stages.miami, true, "saved checkbox is visible on another session");
  assert.equal((await request("/api/ingest/tracking", { method: "POST", service: true, payload: itemImport })).status, 200);
  assert.equal((await itemPatch(device2, "miami", false, 2)).status, 200, "owner can correct a checkbox without deleting source evidence");
  const advancedImport = { items: [{ ...itemImport.items[0], stages: { shipped: true, miami: true, costa_rica: true }, sourceCheckedAt: "2026-11-09T02:00:00Z" }] };
  assert.equal((await request("/api/ingest/tracking", { method: "POST", service: true, payload: advancedImport })).status, 200);
  itemView = await (await request("/api/tracking", { cookie })).json();
  const savedItem = itemView.items.find((x) => x.id === "fixture-project-item");
  assert.equal(savedItem.stages.miami, false, "imports preserve the owner's explicit correction");
  assert.equal(savedItem.stages.costa_rica, true, "new verified phases are imported independently");
  assert.equal((await itemPatch(cookie, "arbitrary", true, savedItem.version)).status, 400);
  assert.equal((await itemPatch(cookie, "shipped", "true", savedItem.version)).status, 400);
  assert.equal((await request("/api/tracking/fixture-local-item", { method: "PATCH", cookie, payload: { version: 1, phase: "miami", value: true } })).status, 400);
  assert.equal((await request("/api/tracking/fixture-local-item", { method: "PATCH", cookie, payload: { version: 1, phase: "delivered", value: true } })).status, 200);
  assert.equal(JSON.stringify(await (await request("/api/export", { cookie })).json()).includes("Private fixture item"), false, "personal inventory is separate from project exports");
  const input = {
    orders: [
      {
        id: "test-order",
        vendor: "Test vendor",
        orderReference: "private-order",
        title: "Test items",
        orderedAt: "2026-10-26",
        totalCents: 1234,
        status: "ordered",
        sourceCheckedAt: "2026-10-26T18:00:00Z",
      },
    ],
    packages: [
      {
        id: "test-pkg",
        orderId: "test-order",
        title: "Test parcel",
        contents: "One test part",
        carrier: "FedEx",
        tracking: "123456789012",
        shippingStatus: "shipped",
        source: "Test evidence",
        sourceCheckedAt: "2026-10-26T18:00:00Z",
        lockerArrivedAt: "2026-10-26T18:00:00Z",
        prealertedAt: "2026-10-26T18:00:00Z",
      },
    ],
  };
  assert.equal(
    (
      await request("/api/ingest", {
        method: "POST",
        service: true,
        payload: input,
      })
    ).status,
    200,
  );
  let snap = await (await request("/api/snapshot", { cookie })).json();
  assert.equal(
    snap.packages[0].lockerArrivedAt,
    null,
    "import cannot mark arrival",
  );
  assert.equal(
    snap.packages[0].prealertedAt,
    null,
    "import cannot submit prealert",
  );
  assert.equal(snap.packages[0].readiness.ready, false);
  assert.equal(
    (
      await request("/api/packages/test-pkg", {
        method: "PATCH",
        cookie,
        payload: { version: 1, notes: "Shared note" },
        headers: { Origin: "https://hostile.example" },
      })
    ).status,
    403,
  );
  assert.equal(
    (
      await request("/api/packages/test-pkg", {
        method: "PATCH",
        service: true,
        payload: { version: 1, notes: "Unauthorized" },
      })
    ).status,
    401,
    "ingestion credential cannot edit owner fields",
  );
  assert.equal(
    (
      await request("/api/packages/test-pkg", {
        method: "PATCH",
        cookie,
        payload: {
          version: 1,
          lockerArrivedAt: "2026-10-26T18:00:00Z",
          notes: "Shared note",
        },
      })
    ).status,
    200,
  );
  assert.equal(
    (
      await request("/api/packages/test-pkg", {
        method: "PATCH",
        cookie: device2,
        payload: { version: 1, notes: "Stale overwrite" },
      })
    ).status,
    409,
  );
  snap = await (await request("/api/snapshot", { cookie: device2 })).json();
  assert.equal(
    snap.packages[0].notes,
    "Shared note",
    "second device reads persisted state",
  );
  assert.ok(snap.packages[0].lockerArrivedAt);
  assert.equal(
    (
      await request("/api/ingest", {
        method: "POST",
        service: true,
        payload: input,
      })
    ).status,
    200,
  );
  snap = await (await request("/api/snapshot", { cookie })).json();
  assert.equal(snap.packages[0].notes, "Shared note");
  assert.ok(snap.packages[0].lockerArrivedAt);
  const duplicate = { ...input.packages[0], id: "duplicate-pkg" };
  assert.equal(
    (
      await request("/api/ingest", {
        method: "POST",
        service: true,
        payload: { packages: [duplicate] },
      })
    ).status,
    409,
  );
  let version = snap.packages[0].version;
  assert.equal(
    (
      await request(
        "/api/packages/test-pkg/document?kind=invoice&name=test.pdf",
        {
          method: "POST",
          cookie,
          raw: "not a PDF",
          headers: {
            "Content-Type": "application/pdf",
            "X-Record-Version": String(version),
          },
        },
      )
    ).status,
    400,
  );
  assert.equal(
    (
      await request(
        "/api/packages/test-pkg/document?kind=invoice&name=test.pdf",
        {
          method: "POST",
          cookie,
          raw: "%PDF-1.7\ntest fixture\n%%EOF",
          headers: {
            "Content-Type": "application/pdf",
            "X-Record-Version": String(version),
          },
        },
      )
    ).status,
    200,
  );
  snap = await (await request("/api/snapshot", { cookie })).json();
  assert.equal(snap.packages[0].readiness.ready, true);
  const pdfPath = "/api/documents/" + snap.packages[0].document.id;
  assert.equal(
    (
      await request("/api/ingest/speedy", {
        method: "POST",
        service: true,
        payload: {
          events: [
            {
              type: "prealert_confirmed",
              packageId: "test-pkg",
              tracking: "different",
              reference: "test-ref",
              source: "Speedy test UI",
              verifiedAt: "2026-10-26T20:00:00Z",
            },
          ],
        },
      })
    ).status,
    409,
  );
  const speedyEvents = {
    events: [
      {
        type: "prealert_confirmed",
        packageId: "test-pkg",
        tracking: "123456789012",
        reference: "test-ref",
        source: "Speedy test UI",
        verifiedAt: "2026-10-26T20:00:00Z",
      },
      {
        type: "consolidation_confirmed",
        packageId: "test-pkg",
        tracking: "123456789012",
        reference: "TEST-CONSOLIDATION",
        source: "Speedy test UI",
        verifiedAt: "2026-10-26T20:00:00Z",
      },
    ],
  };
  assert.equal(
    (
      await request("/api/ingest/speedy", {
        method: "POST",
        service: true,
        payload: speedyEvents,
      })
    ).status,
    200,
  );
  snap = await (await request("/api/snapshot", { cookie: device2 })).json();
  assert.equal(snap.packages[0].consolidationReference, "TEST-CONSOLIDATION");
  assert.equal(snap.packages[0].prealertReference, "test-ref");
  assert.equal(snap.packages[0].notes, "Shared note");
  const eventVersion = snap.packages[0].version;
  assert.equal(
    (
      await request("/api/ingest/speedy", {
        method: "POST",
        service: true,
        payload: speedyEvents,
      })
    ).status,
    200,
  );
  snap = await (await request("/api/snapshot", { cookie: device2 })).json();
  assert.equal(
    snap.packages[0].version,
    eventVersion,
    "verified Speedy events are idempotent",
  );
  const statusEvent = (status, verifiedAt, tracking = "123456789012") => ({
    events: [{ type: "status_confirmed", packageId: "test-pkg", tracking, status, verifiedAt, source: "Speedy test UI" }],
  });
  assert.equal((await request("/api/ingest/speedy", { method: "POST", service: true, payload: statusEvent("received", "2026-10-26T21:00:00Z", "wrong") })).status, 409);
  assert.equal((await request("/api/ingest/speedy", { method: "POST", service: true, payload: statusEvent("received", "2026-10-26T21:00:00Z") })).status, 200);
  snap = await (await request("/api/snapshot", { cookie: device2 })).json();
  assert.equal(snap.packages[0].speedyStatus, "received");
  assert.ok(snap.packages[0].lockerArrivedAt);
  assert.equal(snap.packages[0].shippingStatus, "shipped");
  assert.equal(snap.packages[0].notes, "Shared note");
  assert.equal((await request("/api/ingest/speedy", { method: "POST", service: true, payload: statusEvent("in_transit", "2026-10-26T22:00:00Z") })).status, 200);
  assert.equal((await request("/api/ingest/speedy", { method: "POST", service: true, payload: statusEvent("received", "2026-10-26T23:00:00Z") })).status, 200);
  snap = await (await request("/api/snapshot", { cookie: device2 })).json();
  assert.equal(snap.packages[0].speedyStatus, "in_transit", "older statuses do not overwrite progress");
  assert.equal((await request("/api/ingest/speedy", { method: "POST", service: true, payload: statusEvent("delivered", "2026-10-27T00:00:00Z") })).status, 200);
  snap = await (await request("/api/snapshot", { cookie: device2 })).json();
  assert.equal(snap.packages[0].speedyStatus, "delivered");
  assert.equal((await request(pdfPath)).status, 401);
  const file = await request(pdfPath, { cookie: device2 });
  assert.equal(file.status, 200);
  assert.equal(file.r.headers.get("content-type"), "application/pdf");
  assert.equal(file.r.headers.get("cache-control"), "no-store");
  assert.match(await file.r.text(), /^%PDF-/);
  const exported = await request("/api/export", { cookie });
  assert.equal(exported.status, 200);
  const out = await exported.json();
  assert.ok(out.history.length);
  assert.equal(JSON.stringify(out).includes("password_hash"), false);
  // A shared-order original must remain inaccessible from every owner view,
  // including export, the ingestion URL with an owner cookie, and a saved PDF URL.
  assert.equal((await request("/api/ingest", {
    method: "POST", service: true,
    payload: { orders: [{ ...input.orders[0], id: "AMZ-07" }] },
  })).status, 200);
  await db.prepare("UPDATE packages SET order_id=? WHERE id=?").bind("AMZ-07", "test-pkg").run();
  for (const route of ["/api/snapshot", "/api/export", "/api/ingest/snapshot"]) {
    const restrictedView = await (await request(route, { cookie: device2 })).json();
    const pkg = restrictedView.packages.find((p) => p.id === "test-pkg");
    assert.equal(pkg.title, "Project shipment");
    assert.equal(pkg.contents, "");
    assert.equal(pkg.notes, "");
    assert.equal(pkg.declaredValueCents, null);
    assert.equal(pkg.document, null);
    assert.equal(pkg.invoiceVerified, true);
    assert.equal(pkg.speedyStatus, "delivered");
  }
  assert.equal((await request(pdfPath, { cookie: device2 })).status, 403);
  const preserved = await (await request("/api/ingest/snapshot", { service: true })).json();
  assert.equal(preserved.packages[0].document.id, pdfPath.split("/").pop());
  assert.equal(preserved.packages[0].notes, "Shared note");
  assert.equal(
    (await request("/api/logout", { method: "POST", cookie, payload: {} }))
      .status,
    200,
  );
  assert.equal((await request("/api/snapshot", { cookie })).status, 401);
  assert.equal((await request("/api/tracking", { cookie })).status, 401);
  assert.equal(
    (await request("/api/snapshot", { cookie: device2 })).status,
    200,
  );
  await db
    .prepare("UPDATE owner SET username='another-owner' WHERE id=1")
    .run();
  assert.equal(
    (await request("/api/snapshot", { cookie: device2 })).status,
    403,
  );
  assert.equal((await request("/api/tracking", { cookie: device2 })).status, 403);
});
test("room redaction preserves original evidence and operational fields", () => {
  const original = {
    orders: [{ id: "AMZ-05", title: "RESTRICTED_FIXTURE", notes: "RESTRICTED_FIXTURE", source: "RESTRICTED_FIXTURE" }],
    packages: [{ id: "test", orderId: "AMZ-05", title: "RESTRICTED_FIXTURE", contents: "RESTRICTED_FIXTURE", notes: "RESTRICTED_FIXTURE", source: "RESTRICTED_FIXTURE", speedyEvidence: { note: "RESTRICTED_FIXTURE" }, declaredValueCents: 1234, tracking: "TEST-PROJECT-TRACKING", speedyStatus: "received", document: { id: "fixture", filename: "RESTRICTED_FIXTURE.pdf", kind: "invoice" } }],
    history: [{ action: "PDF attached", detail: { filename: "RESTRICTED_FIXTURE.pdf" } }],
  };
  const view = projectRoomSnapshot(original);
  assert.equal(JSON.stringify(view).includes("RESTRICTED_FIXTURE"), false);
  assert.equal(view.packages[0].tracking, "TEST-PROJECT-TRACKING");
  assert.equal(view.packages[0].speedyStatus, "received");
  assert.equal(original.packages[0].contents, "RESTRICTED_FIXTURE");
  assert.equal(original.packages[0].document.id, "fixture");
});
test("completed order summaries do not create false tracking gaps or discard owner evidence", () => {
  const original = {
    orders: [{ id: "complete", status: "carrier_delivered" }, { id: "partial", status: "partially_shipped" }],
    packages: [
      { id: "summary-AWAIT", orderId: "complete", tracking: "" },
      { id: "tracked", orderId: "complete", tracking: "FIXTURE12345" },
      { id: "noted-AWAIT", orderId: "complete", tracking: "", notes: "Owner note" },
      { id: "documented-AWAIT", orderId: "complete", tracking: "", document: { id: "original", kind: "invoice" } },
      { id: "prealerted-AWAIT", orderId: "complete", tracking: "", prealertedAt: "2026-10-26T20:00:00Z" },
      { id: "pending-AWAIT", orderId: "partial", tracking: "" },
      { id: "partial-tracked", orderId: "partial", tracking: "FIXTURE67890" },
      { id: "pkg-manual", orderId: "complete", tracking: "", source: "Manual entry" },
    ],
    history: [],
  };
  const before = JSON.stringify(original);
  const view = projectRoomSnapshot(original);
  assert.equal(view.packages.some((pkg) => pkg.id === "summary-AWAIT"), false);
  for (const id of ["tracked", "noted-AWAIT", "documented-AWAIT", "prealerted-AWAIT", "pending-AWAIT", "partial-tracked", "pkg-manual"])
    assert.ok(view.packages.some((pkg) => pkg.id === id), id);
  assert.equal(JSON.stringify(original), before);
});
test("closed registration rejects setup even when an activation key is supplied", async () => {
  const response = await worker.fetch(
    new Request("https://admin.test/api/setup", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ key: "unused" }),
    }),
    { OWNER_SETUP_ENABLED: "false" },
  );
  assert.equal(response.status, 403);
});
test("prealert readiness requires carrier, tracking and final purchase PDF", () => {
  assert.equal(
    ready({
      tracking: "123456",
      carrier: "FedEx",
      document: { kind: "provisional_invoice" },
    }).ready,
    false,
  );
  assert.equal(
    ready({
      tracking: "123456",
      carrier: "FedEx",
      document: { kind: "order_confirmation" },
    }).ready,
    false,
  );
  assert.equal(
    ready({
      tracking: "123456",
      carrier: "FedEx",
      document: { kind: "invoice" },
    }).ready,
    true,
  );
  const old = mergeImport(null, {
    title: "Example",
    sourceCheckedAt: "2026-10-26T18:00:00Z",
  });
  const edited = editPackage(old, {
    lockerArrivedAt: "2026-10-26T19:00:00Z",
    notes: "Owner note",
  });
  assert.deepEqual(
    mergeImport(edited, {
      title: "Stale",
      sourceCheckedAt: "2026-10-25T18:00:00Z",
    }),
    edited,
  );
});

test('tracker evidence validates links and dates and survives imports without sources', () => {
  const input = { scope: 'project', title: 'Fixture', sourceCheckedAt: '2026-11-09T00:00:00Z', evidence: [{ label: 'Original', url: 'https://carrier.example/proof', eventDate: '2026-10-31', observedAt: '2026-11-09T00:00:00Z' }] };
  const stored = trackingItemFacts(input);
  const { evidence, ...noLinks } = input;
  assert.deepEqual(mergeTrackingFacts(stored, noLinks).evidence, stored.evidence);
  for (const url of ['javascript:alert(1)', 'http://carrier.example/proof', 'https://user:secret@carrier.example/proof'])
    assert.throws(() => trackingItemFacts({ ...input, evidence: [{ ...evidence[0], url }] }), /HTTPS|link/);
  assert.throws(() => trackingItemFacts({ ...input, evidence: [{ ...evidence[0], eventDate: '2026-02-30' }] }), /valid date/);
  assert.throws(() => trackingItemFacts({ ...input, evidence: [{ ...evidence[0], observedAt: null }] }), /verification date/);
});
