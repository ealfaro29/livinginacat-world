import assert from "node:assert/strict";
import test from "node:test";
import worker from "./worker.mjs";

const base = "https://entity.livinginacat.world";
const cookie = "__Host-entity_session=" + "a".repeat(64);
const request = (path, init = {}) => new Request(base + path, init);
function gateway(role, upstream) {
  return {
    SHORTCUT_KEY: "test-only-key",
    RELAY_KEY: "test-only-relay",
    SESSIONS: { prepare() { return { bind() { return { first: async () => ({ scope: role }) }; } }; } },
    ALFONSITO: { fetch: upstream || (async () => { throw new Error("unexpected upstream request"); }) },
  };
}
async function credential(env, purpose) {
  const response = await worker.fetch(request("/atajos/autorizacion/" + purpose, {
    method: "POST", headers: { Cookie: cookie, Origin: base },
  }), env);
  assert.equal(response.status, 200);
  return response.text();
}
test("direct phone links survive sign-in and a phone session cannot use operator routes", async () => {
  const unpaired = await worker.fetch(request("/iphone"), {});
  assert.equal(unpaired.status, 200);
  assert.match(await unpaired.text(), /iphone-pair\.js/);
  const phone = gateway("phone", async (url) => new Response(new URL(url).pathname));
  const withCookie = { headers: { Cookie: cookie } };
  assert.equal((await worker.fetch(request("/?next=%2Fiphone", withCookie), phone)).headers.get("location"), "/iphone?lang=es");
  assert.equal(await (await worker.fetch(request("/iphone", withCookie), phone)).text(), "/iphone");
  for (const path of ["/operator/camera", "/entity/state", "/control", "/api/connect-arm", "/control/start"]) {
    const method = path.endsWith("start") || path.endsWith("arm") ? "POST" : "GET";
    assert.equal((await worker.fetch(request(path, { method, headers: { Cookie: cookie, Origin: base } }), phone)).status, 403);
  }
  assert.equal((await worker.fetch(request("/api/bridge/state", withCookie), phone)).status, 200);
});
test("shortcut settings always use the canonical host and open the existing shortcuts for editing", async () => {
  for (const host of [base, "https://entity-alfonsito.pages.dev"]) {
    for (const lang of ["es", "en"]) {
      const page = await worker.fetch(new Request(host + "/atajos?lang=" + lang, {headers:{Cookie:cookie}}), gateway("phone"));
      assert.equal(page.status, 200);
      const html = await page.text();
      for (const [path, name] of [["screenshot", "PhysiClaw Upload Screenshot"], ["clipboard", "PhysiClaw Clipboard"]]) {
        assert.ok(html.includes('value="' + base + '/api/bridge/' + path + '"'));
        assert.ok(html.includes('href="shortcuts://open-shortcut?name=' + encodeURIComponent(name) + '"'));
      }
      assert.doesNotMatch(html, /Bearer [0-9a-f]{64}|\.local:8049|shortcuts:\/\/run-shortcut/i);
    }
  }
});
test("camera options, saved adjustments and preview require the operator", async () => {
  const path = "/entity/api/camera/options";
  const op = gateway("operator", async () => Response.json({ok:true}));
  for (const [lang, title] of [["es","Opciones de cámara"],["en","Camera settings"]]) {
    const page = await worker.fetch(request("/camara?lang=" + lang, {headers:{Cookie:cookie}}), op);
    assert.equal(page.status, 200);
    assert.ok((await page.text()).includes(title));
  }
  const guest = await worker.fetch(request("/camara"), op);
  assert.equal(guest.status, 303);
  assert.match(guest.headers.get("Location"), /next=%2Fcamara/);
  for (const [url, method] of [["/camara","GET"],[path,"GET"],[path,"POST"],["/entity/api/camera/preview","GET"]]) {
    assert.equal((await worker.fetch(request(url, {method, headers:{Cookie:cookie,Origin:base}}), gateway("phone"))).status,403);
  }
  assert.equal((await worker.fetch(request(path, {method:"POST",headers:{Cookie:cookie,Origin:"https://example.org"}}),op)).status,403);
  assert.equal((await worker.fetch(request(path, {method:"POST",headers:{Cookie:cookie,Origin:base},body:"{}"}),op)).status,200);
});
test("native shortcuts require the correct scoped credential, preserve binary files and empty responses", async () => {
  const image = new Uint8Array(520000).fill(162);
  let forwarded = 0;
  const phone = gateway("phone", async (url, options) => {
    forwarded++;
    assert.equal(options.headers.Cookie, undefined);
    assert.equal(options.headers.Authorization, undefined);
    if (new URL(url).pathname.endsWith("/clipboard")) return new Response(null, { status: 204 });
    assert.equal(options.headers["Content-Type"], "image/png");
    assert.deepEqual(options.body, image);
    return Response.json({ status: "ok" });
  });
  const screenshot = await credential(phone, "screenshot");
  const clipboard = await credential(phone, "clipboard");
  assert.notEqual(screenshot, clipboard);
  const shot = "/api/bridge/screenshot";
  const clip = "/api/bridge/clipboard";
  const send = (path, method, auth, extra = {}, body) => worker.fetch(request(path, {
    method, headers: { Authorization: auth, ...extra }, body,
  }), phone);
  assert.equal((await send(clip, "GET", screenshot)).status, 401);
  assert.equal((await send(clip, "POST", clipboard)).status, 405);
  assert.equal((await send(clip, "GET", clipboard, {Origin:"https://foreign.example"})).status, 403);
  assert.equal((await worker.fetch(request(clip, { headers: { Cookie: cookie } }), phone)).status, 401);
  assert.equal((await send(shot, "POST", screenshot, {"Content-Length": "10485761"})).status, 413);
  const empty = await send(clip, "GET", clipboard);
  assert.equal(empty.status, 204);
  assert.equal(await empty.text(), "");
  assert.equal((await send(shot, "POST", screenshot, {"Content-Type":"image/png"}, image)).status, 200);
  assert.equal(forwarded, 2);
});

test("only the operator can pair a new Home Screen device and it receives phone-only access", async () => {
  const { DatabaseSync } = await import("node:sqlite");
  const { readFileSync } = await import("node:fs");
  const { createHash } = await import("node:crypto");
  const db = new DatabaseSync(":memory:");
  try {
    db.exec(readFileSync(new URL("./schema.sql", import.meta.url), "utf8"));
    const ownerHash = createHash("sha256").update("a".repeat(64)).digest("hex");
    db.prepare("INSERT INTO sessions VALUES(?,?,'operator')").run(ownerHash, Math.floor(Date.now()/1000)+90);
    const env = gateway("", async () => Response.json({ mode: "bridge" }));
    env.SESSIONS = { prepare(sql) { return { bind(...values) { return {
      first: () => db.prepare(sql).get(...values),
      run: () => ({meta:db.prepare(sql).run(...values)}),
    }; } }; } };
    env.SESSIONS.batch = async statements => statements.map(stmt => stmt.run());
    env.LOGIN_LIMIT = { limit: async () => ({success:true}) };
    const submit = (path, options = {}) => worker.fetch(request(path, {
      method: "POST", headers: { Origin: base, Cookie: options.cookie || "", "Content-Type": "application/json" },
      body: JSON.stringify(options.body || {}),
    }), env);
    const start = await submit("/iphone/pair/start");
    const challenge = start.headers.getSetCookie()[0].split(";",1)[0];
    const {code} = await start.json();
    assert.match(code,/^\d{8}$/);
    const status = (c = challenge) => submit("/iphone/pair/status",{cookie:c});
    assert.ok(!(await (await status()).json()).linked);
    assert.equal((await status("")).status,410);
    assert.equal((await submit("/operator/pair-phone",{body:{code}})).status,401);
    assert.equal((await submit("/operator/pair-phone",{cookie,body:{code:"no"}})).status,400);
    assert.equal((await submit("/operator/pair-phone",{cookie,body:{code}})).status,200);
    const approved = await status();
    assert.equal((await approved.json()).linked,true);
    const device = approved.headers.getSetCookie().find(c=>c.startsWith("__Host-entity_session="));
    assert.ok(device.includes("HttpOnly") && device.includes("Secure"));
    const phoneCookie = device.split(";",1)[0];
    assert.equal((await worker.fetch(request("/entity/state",{headers:{Cookie:phoneCookie}}),env)).status,403);
    assert.equal((await submit("/operator/pair-phone",{cookie:phoneCookie,body:{code}})).status,403);
    assert.equal((await worker.fetch(request("/api/bridge/state",{headers:{Cookie:phoneCookie}}),env)).status,200);
    assert.equal((await (await status()).json()).linked,true);
    assert.equal((await submit("/auth/logout",{cookie:phoneCookie})).status,303);
    assert.equal((await status()).status,410);
    const newer = await submit("/iphone/pair/start");
    const other = newer.headers.getSetCookie()[0].split(";",1)[0];
    db.exec("UPDATE phone_pairing SET expires=0");
    assert.equal((await status(other)).status,410);
  } finally { db.close(); }
});
