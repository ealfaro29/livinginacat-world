import {
  ApiError,
  text,
  id,
  tracking,
  day,
  cents,
  ready,
  mergeImport,
  editPackage,
} from "./model.mjs";
const encoder = new TextEncoder();
const COOKIE = "__Host-lica_session";
const SESSION_SECONDS = 43200;
export const hex = (bytes) =>
  [...new Uint8Array(bytes)]
    .map((x) => x.toString(16).padStart(2, "0"))
    .join("");
export const digest = async (value) =>
  hex(
    await crypto.subtle.digest(
      "SHA-256",
      typeof value === "string" ? encoder.encode(value) : value,
    ),
  );
const random = () => hex(crypto.getRandomValues(new Uint8Array(32)));
export function equal(a, b) {
  if (typeof a !== "string" || typeof b !== "string" || a.length !== b.length)
    return false;
  let diff = 0;
  for (let i = 0; i < a.length; i++) diff |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return diff === 0;
}
export async function passwordHash(password, salt) {
  const key = await crypto.subtle.importKey(
    "raw",
    encoder.encode(password),
    "PBKDF2",
    false,
    ["deriveBits"],
  );
  return hex(
    await crypto.subtle.deriveBits(
      {
        name: "PBKDF2",
        salt: encoder.encode(salt),
        iterations: 100000,
        hash: "SHA-256",
      },
      key,
      256,
    ),
  );
}
const now = () => new Date().toISOString();
const json = (data, status = 200, headers = {}) =>
  new Response(JSON.stringify(data), {
    status,
    headers: { "Content-Type": "application/json; charset=utf-8", ...headers },
  });
const cookie = (value) =>
  `${COOKIE}=${value}; Path=/; Secure; HttpOnly; SameSite=Strict; Max-Age=${value ? SESSION_SECONDS : 0}`;
async function body(request, limit = 1000000) {
  if (!request.headers.get("Content-Type")?.includes("application/json"))
    throw new ApiError(415, "Use JSON.");
  const raw = await request.text();
  if (encoder.encode(raw).length > limit)
    throw new ApiError(413, "Request too large.");
  try {
    return JSON.parse(raw);
  } catch {
    throw new ApiError(400, "Invalid JSON.");
  }
}
async function owner(env) {
  return env.DB.prepare("SELECT * FROM owner WHERE id=1 AND username=?")
    .bind(env.OWNER_USERNAME || "ealfaro29")
    .first();
}
async function rate(request, env) {
  if (!env.LOGIN_RATE) throw new ApiError(503, "Login protection unavailable.");
  const result = await env.LOGIN_RATE.limit({
    key: request.headers.get("CF-Connecting-IP") || "local",
  });
  if (!result.success)
    throw new ApiError(429, "Too many attempts. Try again in a minute.");
}
async function auth(request, env, serviceAllowed = false) {
  const bearer = request.headers.get("Authorization");
  if (
    serviceAllowed &&
    bearer?.startsWith("Bearer ") &&
    env.INGEST_TOKEN_HASH &&
    equal(await digest(bearer.slice(7)), env.INGEST_TOKEN_HASH)
  )
    return "mail-sync";
  const token = request.headers
    .get("Cookie")
    ?.split(";")
    .map((x) => x.trim())
    .find((x) => x.startsWith(COOKIE + "="))
    ?.slice(COOKIE.length + 1);
  if (!token || !/^[a-f0-9]{64}$/.test(token))
    throw new ApiError(401, "Sign in to continue.");
  const session = await env.DB.prepare(
    "SELECT token_hash FROM sessions WHERE token_hash=? AND expires_at>?",
  )
    .bind(await digest(token), Date.now())
    .first();
  if (!session) throw new ApiError(401, "Your session expired. Sign in again.");
  if (!(await owner(env))) throw new ApiError(403, "Owner access only.");
  return "owner";
}
async function startSession(env) {
  const token = random();
  await env.DB.batch([
    env.DB.prepare("DELETE FROM sessions WHERE expires_at<?").bind(Date.now()),
    env.DB.prepare(
      "INSERT INTO sessions(token_hash,expires_at) VALUES(?,?)",
    ).bind(await digest(token), Date.now() + SESSION_SECONDS * 1000),
  ]);
  return json({ ok: true }, 200, { "Set-Cookie": cookie(token) });
}
const audit = (env, actor, action, entity, detail = {}) =>
  env.DB.prepare(
    "INSERT INTO audit(actor,action,entity_id,detail,created_at) VALUES(?,?,?,?,?)",
  ).bind(actor, action, entity, JSON.stringify(detail), now());
const record = (row) =>
  row
    ? {
        ...JSON.parse(row.data),
        id: row.id,
        orderId: row.order_id,
        version: row.version,
        updatedAt: row.updated_at,
      }
    : null;
async function snapshot(env) {
  const [orders, packages, history] = await env.DB.batch([
    env.DB.prepare("SELECT * FROM orders ORDER BY id"),
    env.DB.prepare("SELECT * FROM packages ORDER BY id"),
    env.DB.prepare("SELECT * FROM audit ORDER BY id DESC LIMIT 100"),
  ]);
  return {
    orders: orders.results.map((x) => ({
      ...JSON.parse(x.data),
      id: x.id,
      updatedAt: x.updated_at,
    })),
    packages: packages.results.map((x) => {
      const p = record(x);
      return { ...p, readiness: ready(p) };
    }),
    history: history.results.map((x) => ({
      ...x,
      detail: JSON.parse(x.detail),
    })),
    syncedAt: now(),
  };
}
async function packageRow(env, key) {
  const row = await env.DB.prepare("SELECT * FROM packages WHERE id=?")
    .bind(id(key))
    .first();
  if (!row) throw new ApiError(404, "Package not found.");
  return row;
}
async function updatePackage(env, row, next, actor, action) {
  const data = { ...next };
  delete data.id;
  delete data.orderId;
  delete data.version;
  delete data.updatedAt;
  delete data.readiness;
  const result = await env.DB.batch([
    env.DB.prepare(
      "UPDATE packages SET data=?,tracking_normalized=?,version=version+1,updated_at=? WHERE id=? AND version=?",
    ).bind(
      JSON.stringify(data),
      tracking(data.tracking) || null,
      now(),
      row.id,
      row.version,
    ),
    env.DB.prepare(
      "INSERT INTO audit(actor,action,entity_id,detail,created_at) SELECT ?,?,?,?,? WHERE changes()=1",
    ).bind(
      actor,
      action,
      row.id,
      JSON.stringify({ version: row.version + 1 }),
      now(),
    ),
  ]);
  if (!result[0].meta.changes)
    throw new ApiError(
      409,
      "This package changed on another device. Refresh and try again.",
    );
  return json({ ok: true, version: row.version + 1 });
}
function orderFacts(input) {
  return {
    vendor: text(input.vendor, 80),
    orderReference: text(input.orderReference, 160),
    title: text(input.title, 160),
    orderedAt: day(input.orderedAt),
    totalCents: cents(input.totalCents),
    status: text(input.status, 80),
    notes: text(input.notes, 5000),
    source: text(input.source, 500),
    sourceCheckedAt: text(input.sourceCheckedAt, 50),
  };
}
async function handle(request, env) {
  const url = new URL(request.url),
    path = url.pathname,
    method = request.method;
  if (path === "/api/health" && method === "GET")
    return json({ ok: true, service: "livinginacat-admin", schema: 1 });
  if (!path.startsWith("/api/")) {
    if (method !== "GET" && method !== "HEAD")
      throw new ApiError(405, "Method not allowed.");
    return env.ASSETS.fetch(request);
  }
  if (!["GET", "HEAD"].includes(method)) {
    const origin = request.headers.get("Origin");
    if (origin && origin !== url.origin)
      throw new ApiError(403, "Request origin rejected.");
    if (request.headers.get("Sec-Fetch-Site") === "cross-site")
      throw new ApiError(403, "Request origin rejected.");
  }
  if (path === "/api/session" && method === "GET") {
    let signedIn = false;
    try {
      await auth(request, env);
      signedIn = true;
    } catch {}
    return json({
      signedIn,
      setupAvailable: env.OWNER_SETUP_ENABLED === "true" && !(await owner(env)),
      username: signedIn ? (await owner(env)).username : undefined,
    });
  }
  if (path === "/api/setup" && method === "POST") {
    if (env.OWNER_SETUP_ENABLED !== "true")
      throw new ApiError(403, "Owner registration is closed.");
    await rate(request, env);
    const input = await body(request, 2000);
    if (
      !env.SETUP_TOKEN_HASH ||
      !equal(await digest(String(input.key || "")), env.SETUP_TOKEN_HASH)
    )
      throw new ApiError(403, "Invalid setup link.");
    if (await owner(env))
      throw new ApiError(409, "This admin is already configured. Sign in.");
    if (
      typeof input.password !== "string" ||
      input.password.length < 14 ||
      input.password.length > 128
    )
      throw new ApiError(400, "Use a password with 14–128 characters.");
    const salt = random(),
      hash = await passwordHash(input.password, salt);
    const result = await env.DB.prepare(
      "INSERT OR IGNORE INTO owner(id,username,password_hash,salt,created_at) VALUES(1,?,?,?,?)",
    )
      .bind("ealfaro29", hash, salt, now())
      .run();
    if (!result.meta.changes)
      throw new ApiError(409, "This admin is already configured. Sign in.");
    await audit(env, "owner", "Admin activated", "owner").run();
    return startSession(env);
  }
  if (path === "/api/login" && method === "POST") {
    await rate(request, env);
    const input = await body(request, 2000),
      user = await owner(env);
    const candidate = await passwordHash(
      String(input.password || "").slice(0, 129),
      user?.salt || "unconfigured-owner",
    );
    if (
      !user ||
      user.username !== (env.OWNER_USERNAME || "ealfaro29") ||
      text(input.username, 80) !== user.username ||
      !equal(candidate, user.password_hash)
    )
      throw new ApiError(401, "Username or password is incorrect.");
    return startSession(env);
  }
  const service = path.startsWith("/api/ingest");
  const actor = await auth(request, env, service);
  if (path === "/api/logout" && method === "POST") {
    const token = request.headers
      .get("Cookie")
      ?.match(/__Host-lica_session=([a-f0-9]{64})/)?.[1];
    if (token)
      await env.DB.prepare("DELETE FROM sessions WHERE token_hash=?")
        .bind(await digest(token))
        .run();
    return json({ ok: true }, 200, { "Set-Cookie": cookie("") });
  }
  if (
    (path === "/api/snapshot" ||
      path === "/api/export" ||
      path === "/api/ingest/snapshot") &&
    method === "GET"
  ) {
    return json(
      await snapshot(env),
      200,
      path === "/api/export"
        ? {
            "Content-Disposition":
              'attachment; filename="livinginacat-private-orders.json"',
          }
        : {},
    );
  }
  if (path === "/api/ingest" && method === "POST") {
    const input = await body(request),
      results = [];
    if (
      !Array.isArray(input.orders || []) ||
      !Array.isArray(input.packages || []) ||
      (input.orders?.length || 0) > 100 ||
      (input.packages?.length || 0) > 200
    )
      throw new ApiError(400, "Invalid import.");
    for (const item of input.orders || []) {
      const key = id(item.id),
        data = orderFacts(item),
        old = await env.DB.prepare("SELECT data FROM orders WHERE id=?")
          .bind(key)
          .first();
      if (old && JSON.parse(old.data).sourceCheckedAt > data.sourceCheckedAt)
        continue;
      if (old?.data === JSON.stringify(data)) continue;
      await env.DB.batch([
        env.DB.prepare(
          "INSERT INTO orders(id,data,updated_at) VALUES(?,?,?) ON CONFLICT(id) DO UPDATE SET data=excluded.data,updated_at=excluded.updated_at",
        ).bind(key, JSON.stringify(data), now()),
        audit(env, actor, "Order evidence updated", key),
      ]);
      results.push(key);
    }
    for (const item of input.packages || []) {
      const key = id(item.id),
        orderId = id(item.orderId);
      const row = await env.DB.prepare("SELECT * FROM packages WHERE id=?")
        .bind(key)
        .first();
      const next = mergeImport(row ? JSON.parse(row.data) : null, item),
        serialized = JSON.stringify(next);
      if (row && row.order_id !== orderId)
        throw new ApiError(
          409,
          "Package order cannot be reassigned by import.",
        );
      if (row?.data === serialized) continue;
      if (row)
        await updatePackage(env, row, next, actor, "Shipment evidence updated");
      else
        await env.DB.batch([
          env.DB.prepare(
            "INSERT INTO packages(id,order_id,tracking_normalized,data,updated_at) VALUES(?,?,?,?,?)",
          ).bind(key, orderId, next.tracking || null, serialized, now()),
          audit(env, actor, "Package created", key),
        ]);
      results.push(key);
    }
    return json({ ok: true, updated: results });
  }
  if (path === "/api/ingest/speedy" && method === "POST") {
    const input = await body(request, 20000);
    if (!Array.isArray(input.events) || input.events.length > 50)
      throw new ApiError(400, "Invalid Speedy evidence.");
    for (const event of input.events) {
      if (
        !["prealert_confirmed", "consolidation_confirmed", "status_confirmed"].includes(
          event.type,
        ) ||
        (event.type !== "status_confirmed" && !text(event.reference, 160)) ||
        !text(event.source, 500)
      )
        throw new ApiError(
          400,
          "A verified Speedy reference and source are required.",
        );
      const verifiedAt = new Date(event.verifiedAt);
      if (!Number.isFinite(verifiedAt.getTime()))
        throw new ApiError(400, "A verification date is required.");
      const row = await packageRow(env, event.packageId),
        next = JSON.parse(row.data);
      if (!next.tracking)
        throw new ApiError(400, "A Speedy event requires a tracking number.");
      if (event.tracking !== next.tracking)
        throw new ApiError(409, "Speedy tracking does not match this package.");
      if (event.type === "status_confirmed") {
        const allowed = ["received", "in_transit", "delivered"];
        if (!allowed.includes(event.status))
          throw new ApiError(400, "Invalid Speedy status.");
        if (next.speedyStatusVerifiedAt && Date.parse(next.speedyStatusVerifiedAt) >= verifiedAt.getTime()) continue;
        if (next.speedyStatus && allowed.indexOf(event.status) < allowed.indexOf(next.speedyStatus)) continue;
        next.speedyStatus = event.status;
        next.speedyStatusVerifiedAt = verifiedAt.toISOString();
        next.speedyStatusSource = text(event.source, 500);
        if (event.status === "received") next.lockerArrivedAt ||= verifiedAt.toISOString();
        await updatePackage(env, row, next, actor, "Speedy package status verified");
        continue;
      }
      if (event.type === "prealert_confirmed") {
        if (
          next.prealertedAt &&
          next.prealertReference === text(event.reference, 160)
        )
          continue;
        next.prealertedAt ||= verifiedAt.toISOString();
        next.prealertReference = text(event.reference, 160);
      } else {
        if (next.consolidationReference === text(event.reference, 160))
          continue;
        next.consolidationReference = text(event.reference, 160);
        next.consolidatedAt = verifiedAt.toISOString();
      }
      next.speedyEvidence = {
        source: text(event.source, 500),
        verifiedAt: verifiedAt.toISOString(),
      };
      await updatePackage(
        env,
        row,
        next,
        actor,
        event.type === "prealert_confirmed"
          ? "Speedy prealert verified"
          : "Speedy consolidation verified",
      );
    }
    return json({ ok: true });
  }
  if (path === "/api/packages" && method === "POST") {
    const input = await body(request, 10000),
      key = "pkg-" + random().slice(0, 16),
      orderId = id(input.orderId);
    const data = mergeImport(null, {
      ...input,
      source: "Manual entry",
      sourceCheckedAt: now(),
    });
    await env.DB.batch([
      env.DB.prepare(
        "INSERT INTO packages(id,order_id,tracking_normalized,data,updated_at) VALUES(?,?,?,?,?)",
      ).bind(key, orderId, data.tracking || null, JSON.stringify(data), now()),
      audit(env, actor, "Package created", key),
    ]);
    return json({ ok: true, id: key }, 201);
  }
  const edit = path.match(/^\/api\/packages\/([a-zA-Z0-9_-]+)$/);
  if (edit && method === "PATCH") {
    const input = await body(request, 15000),
      row = await packageRow(env, edit[1]);
    if (input.version !== row.version)
      throw new ApiError(
        409,
        "This package changed on another device. Refresh and try again.",
      );
    return updatePackage(
      env,
      row,
      editPackage(JSON.parse(row.data), input),
      actor,
      "Package updated",
    );
  }
  const upload = path.match(
    /^\/api\/(?:ingest\/)?packages\/([a-zA-Z0-9_-]+)\/document$/,
  );
  if (upload && method === "POST") {
    const row = await packageRow(env, upload[1]);
    if (Number(request.headers.get("X-Record-Version")) !== row.version)
      throw new ApiError(
        409,
        "This package changed. Refresh before attaching the PDF.",
      );
    if (!request.headers.get("Content-Type")?.startsWith("application/pdf"))
      throw new ApiError(415, "Upload a PDF file.");
    const bytes = await request.arrayBuffer();
    if (bytes.byteLength > 8 * 1024 * 1024)
      throw new ApiError(413, "Maximum PDF size is 8 MB.");
    if (!new TextDecoder().decode(bytes.slice(0, 5)).startsWith("%PDF-"))
      throw new ApiError(400, "This file is not a PDF.");
    const kind = url.searchParams.get("kind");
    if (
      !["invoice", "order_confirmation", "provisional_invoice"].includes(kind)
    )
      throw new ApiError(400, "Choose the document type.");
    const documentId = random(),
      fileKey = "pdf/" + documentId;
    const filename = (
      text(url.searchParams.get("name"), 150) || "invoice.pdf"
    ).replace(/[^a-zA-Z0-9._ -]/g, "_");
    const sha256 = await digest(bytes);
    await env.DOCUMENTS.put(fileKey, bytes);
    // Keep every original file immutable; replacing the active attachment never
    // removes earlier evidence or its audit record.
    await env.DB.prepare(
      "INSERT INTO documents(id,package_id,file_key,filename,kind,sha256,bytes,created_at) VALUES(?,?,?,?,?,?,?,?)",
    )
      .bind(
        documentId,
        row.id,
        fileKey,
        filename,
        kind,
        sha256,
        bytes.byteLength,
        now(),
      )
      .run();
    return updatePackage(
      env,
      row,
      {
        ...JSON.parse(row.data),
        document: {
          id: documentId,
          filename,
          kind,
          sha256,
          bytes: bytes.byteLength,
          createdAt: now(),
        },
      },
      actor,
      "PDF attached",
    );
  }
  const download = path.match(/^\/api\/documents\/([a-f0-9]{64})$/);
  if (download && method === "GET") {
    const doc = await env.DB.prepare("SELECT * FROM documents WHERE id=?")
      .bind(download[1])
      .first();
    if (!doc) throw new ApiError(404, "Document not found.");
    const file = await env.DOCUMENTS.get(doc.file_key, { type: "arrayBuffer" });
    if (!file)
      throw new ApiError(503, "The PDF is synchronizing. Try again shortly.");
    return new Response(file, {
      headers: {
        "Content-Type": "application/pdf",
        "Content-Disposition": `attachment; filename="${doc.filename}"`,
      },
    });
  }
  throw new ApiError(404, "Endpoint not found.");
}
export default {
  async fetch(request, env) {
    let response;
    try {
      response = await handle(request, env);
    } catch (error) {
      const duplicate = String(error.message).includes(
        "UNIQUE constraint failed",
      );
      response = json(
        {
          error: duplicate
            ? "This tracking number or record already exists. Check the existing package."
            : error instanceof ApiError
              ? error.message
              : "The request could not be saved. Try again.",
        },
        duplicate ? 409 : error instanceof ApiError ? error.status : 500,
      );
      if (!(error instanceof ApiError) && !duplicate)
        console.error("Admin request failed", error.name);
    }
    const headers = new Headers(response.headers);
    headers.set("Cache-Control", "no-store");
    headers.set("X-Content-Type-Options", "nosniff");
    headers.set("Referrer-Policy", "no-referrer");
    headers.set("X-Frame-Options", "DENY");
    headers.set("X-Robots-Tag", "noindex, nofollow, noarchive");
    headers.set("Strict-Transport-Security", "max-age=31536000");
    headers.set(
      "Content-Security-Policy",
      "default-src 'none'; script-src 'self'; style-src 'self'; img-src 'self' data:; font-src 'self'; connect-src 'self'; form-action 'self'; base-uri 'none'; frame-ancestors 'none'",
    );
    return new Response(response.body, { status: response.status, headers });
  },
};
