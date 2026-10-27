import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs/promises";
import path from "node:path";
import { createHash } from "node:crypto";
import { Miniflare, convertV4MiniflareOptions } from "miniflare";
import { ready, mergeImport, editPackage } from "../backend/model.mjs";
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
  const schema = await fs.readFile("backend/migrations/0001_admin.sql", "utf8");
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
  assert.equal(
    (await request("/api/logout", { method: "POST", cookie, payload: {} }))
      .status,
    200,
  );
  assert.equal((await request("/api/snapshot", { cookie })).status, 401);
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
