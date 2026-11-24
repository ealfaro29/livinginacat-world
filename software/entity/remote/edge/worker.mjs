import { tasksPage, cameraPage, homePage, loginPage, shortcutsPage, phoneOfflinePage, phonePairPage, phoneHead } from "./views.mjs";

import { approvePhone, phonePairing, PHONE_LIFETIME } from "./pairing.mjs";

const COOKIE = "__Host-entity_session";
const WEEK = 7 * 24 * 60 * 60;
const MAX_BYTES = 16384;
const utf8 = new TextEncoder();
const hosts = new Set(["entity.livinginacat.world", "entity-alfonsito.pages.dev"]);
const entryPages = new Set(["/", "/entity/", "/setup-hardware", "/entity/travel", "/control", "/jugar", "/iphone", "/bridge", "/atajos", "/camara", "/tareas"]);
const phoneEntries = new Set(["/iphone", "/bridge", "/jugar", "/atajos"]);
const phoneReads = new Set([...phoneEntries, "/api/bridge/state", "/pulse.js", "/pulse.css", "/sentient.svg", "/space-grotesk.ttf"]);
const phoneWrites = new Set(["/api/bridge/screen-dimension", "/api/bridge/touch", "/api/bridge/tapped", "/api/phone"]);
const shortcutMethods = new Map([["/api/bridge/screenshot", "POST"], ["/api/bridge/clipboard", "GET"]]);
const MAX_SCREENSHOT_BYTES = 10 * 1024 * 1024;
const flags = "Path=/; Secure; HttpOnly; SameSite=Lax";
const baseHeaders = {
  "Cache-Control": "private, no-store",
  "Strict-Transport-Security": "max-age=31536000",
  // Native form POSTs need their same-origin Origin header to pass the CSRF check.
  "Referrer-Policy": "same-origin",
  "X-Content-Type-Options": "nosniff",
  "X-Frame-Options": "DENY",
  "X-Robots-Tag": "noindex, nofollow, noarchive",
  "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
};
const portalCsp = "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; font-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'; object-src 'none'";
// The pre-existing local setup wizard and LCD use inline scripts and styling.
const deviceCsp = portalCsp.replace("script-src 'self'", "script-src 'self' 'unsafe-inline'").replace("style-src 'self'", "style-src 'self' 'unsafe-inline'");

function reply(body, status, type, extra = {}) {
  return new Response(body, {
    status, headers: { ...baseHeaders, "Content-Type": type, "Content-Security-Policy": portalCsp, ...extra },
  });
}
function html(body, status = 200) {
  return reply(body, status, "text/html; charset=utf-8");
}
function error(status, code) {
  return reply(JSON.stringify({ error: code }), status, "application/json");
}
function redirect(location, cookie) {
  const headers = { Location: location };
  if (cookie) headers["Set-Cookie"] = cookie;
  return reply(null, 303, "text/plain", headers);
}
function hex(bytes) {
  return Array.from(new Uint8Array(bytes), value => value.toString(16).padStart(2, "0")).join("");
}
function unhex(string) {
  return Uint8Array.from(string.match(/../g) ?? [], byte => parseInt(byte, 16));
}
export async function derive(password, salt) {
  const material = await crypto.subtle.importKey("raw", utf8.encode(password), "PBKDF2", false, ["deriveBits"]);
  return new Uint8Array(await crypto.subtle.deriveBits({
    name: "PBKDF2", hash: "SHA-256", salt: unhex(salt), iterations: 100000,
  }, material, 256));
}
function sameBytes(left, right) {
  if (left.length !== right.length) return false;
  let different = 0;
  for (let i = 0; i < left.length; i++) different |= left[i] ^ right[i];
  return different === 0;
}
function cookieToken(request, name) {
  const raw = (request.headers.get("Cookie") || "").split(";")
    .map(part => part.trim()).find(part => part.startsWith(name + "="))?.slice(name.length + 1);
  return raw && /^[0-9a-f]{64}$/.test(raw) ? raw : null;
}
const tokenHash = async token => hex(await crypto.subtle.digest("SHA-256", utf8.encode(token)));
const randomToken = () => hex(crypto.getRandomValues(new Uint8Array(32)));
const sessionCookie = (token, age) => COOKIE + "=" + token + "; " + flags + "; Max-Age=" + age;
async function readBody(request, limit = MAX_BYTES) {
  if (Number(request.headers.get("Content-Length")) > limit) return null;
  const reader = request.body?.getReader();
  if (!reader) return new Uint8Array();
  const chunks = [];
  let size = 0;
  for (;;) {
    const { value, done } = await reader.read();
    if (done) break;
    size += value.length;
    if (size > limit) { await reader.cancel(); return null; }
    chunks.push(value);
  }
  const result = new Uint8Array(size);
  let offset = 0;
  for (const chunk of chunks) { result.set(chunk, offset); offset += chunk.length; }
  return result;
}
function destination(value, lang) {
  return (entryPages.has(value) ? value : "/") + "?lang=" + lang;
}
async function login(request, env, url, lang) {
  const key = request.headers.get("CF-Connecting-IP") || "direct";
  const next = entryPages.has(url.searchParams.get("next")) ? url.searchParams.get("next") : "/";
  if (!(await env.LOGIN_LIMIT.limit({ key })).success) return html(loginPage(lang, next, "rate"), 429);
  if (!request.headers.get("Content-Type")?.startsWith("application/x-www-form-urlencoded")) return error(415, "form_required");
  const body = await readBody(request);
  if (body === null) return error(413, "too_large");
  const fields = new URLSearchParams(new TextDecoder().decode(body));
  const candidate = fields.get("password") ?? "";
  const owner = await env.SESSIONS.prepare("SELECT username, salt, verifier FROM operator WHERE id=1").first();
  if (!owner) return html(loginPage(lang, next, "unavailable"), 503);
  if (candidate.length > 256) return html(loginPage(lang, next, "wrong"), 401);
  const digest = await derive(candidate, owner.salt);
  if (!sameBytes(digest, unhex(owner.verifier)) || fields.get("username")?.trim() !== owner.username) {
    return html(loginPage(lang, next, "wrong"), 401);
  }
  const raw = randomToken();
  const hash = await tokenHash(raw);
  const now = Math.floor(Date.now() / 1000);
  const scope = phoneEntries.has(next) ? "phone" : "operator";
  const age = scope === "phone" ? PHONE_LIFETIME : WEEK;
  await env.SESSIONS.batch([
    env.SESSIONS.prepare("DELETE FROM sessions WHERE expires <= ?").bind(now),
    env.SESSIONS.prepare("INSERT INTO sessions(token_hash,expires,scope) VALUES(?,?,?)").bind(hash, now + age, scope),
  ]);
  return redirect(destination(next, lang), sessionCookie(raw, age));
}
async function shortcutCredential(env, path) {
  if (!env.SHORTCUT_KEY) throw new Error("Shortcut key unavailable");
  const key = await crypto.subtle.importKey("raw", utf8.encode(env.SHORTCUT_KEY), { name: "HMAC", hash: "SHA-256" }, false, ["sign"]);
  return "Bearer " + hex(await crypto.subtle.sign("HMAC", key, utf8.encode("entity-shortcut-v1:" + path)));
}
function offline(lang, path) {
  if (phoneEntries.has(path)) return html(phoneOfflinePage(lang, path), 503);
  return entryPages.has(path) ? html(homePage(lang, true), 503) : error(503, "device_offline");
}
async function visitDevice(request, env, url, lang) {
  const isPage = entryPages.has(url.pathname);
  const timeout = request.method === "POST" ? 90000 : isPage ? 60000 : 12000;
  const options = {
    method: request.method, redirect: "manual", headers: { "X-Entity-Relay": env.RELAY_KEY },
    signal: AbortSignal.timeout(timeout),
  };
  if (request.method === "POST") {
    const screenshot = url.pathname === "/api/bridge/screenshot";
    const body = await readBody(request, screenshot ? MAX_SCREENSHOT_BYTES : MAX_BYTES);
    if (body === null) return error(413, "too_large");
    options.body = body;
    options.headers["Content-Type"] = screenshot ? request.headers.get("Content-Type") || "application/octet-stream" : "application/json";
  }
  try {
    const target = "http://127.0.0.1:8052" + url.pathname + url.search;
    const upstream = await env.ALFONSITO.fetch(target, options);
    if (upstream.status >= 502 || (upstream.status >= 300 && upstream.status < 400 && upstream.status !== 304)) return offline(lang, url.pathname);
    if (upstream.ok && ["/iphone", "/jugar"].includes(url.pathname) && upstream.headers.get("Content-Type")?.startsWith("text/html")) {
      const page = (await upstream.text()).replace("</head>", phoneHead + '<script defer src="/ui/iphone-ready.js"></script></head>');
      return reply(page, 200, "text/html; charset=utf-8", { "Content-Security-Policy": deviceCsp });
    }
    if (upstream.ok && ["/entity/", "/entity/travel", "/setup-hardware", "/control"].includes(url.pathname)
        && upstream.headers.get("Content-Type")?.startsWith("text/html")) {
      const back = `<nav class="entity-home-nav" aria-label="${lang === "es" ? "Navegación" : "Navigation"}"><a href="/?lang=${lang}">← ${lang === "es" ? "Volver al inicio" : "Back to dashboard"}</a></nav>`;
      const page = (await upstream.text()).replace("</head>", '<link rel="stylesheet" href="/ui/dashboard-nav.css"></head>')
        .replace(/<body(?:\s[^>]*)?>/i, (body) => body + back);
      return reply(page, 200, "text/html; charset=utf-8", {"Content-Security-Policy": deviceCsp});
    }
    // Return the payload only. Internal cookies, headers and redirects stay on the Pi.
    return reply([204, 205, 304].includes(upstream.status) ? null : upstream.body, upstream.status, upstream.headers.get("Content-Type") || "application/octet-stream", {
      "Content-Security-Policy": deviceCsp,
    });
  } catch {
    return offline(lang, url.pathname);
  }
}
export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const lang = url.searchParams.get("lang") === "en" ? "en" : "es";
    if (url.protocol !== "https:" || !hosts.has(url.hostname)) return error(404, "not_found");
    if (!["GET", "POST", "HEAD"].includes(request.method)) return error(405, "method");
    if (shortcutMethods.has(url.pathname)) {
      if (request.method !== shortcutMethods.get(url.pathname)) return error(405, "method");
      const origin = request.headers.get("Origin");
      if ((origin !== null && origin !== url.origin) || request.headers.get("Sec-Fetch-Site") === "cross-site") return error(403, "origin");
      const given = request.headers.get("Authorization") || "";
      if (!/^Bearer [0-9a-f]{64}$/.test(given)) return error(401, "shortcut_auth");
      if (!env.SHORTCUT_KEY) return error(503, "shortcut_unavailable");
      const expected = await shortcutCredential(env, url.pathname);
      if (!sameBytes(utf8.encode(given), utf8.encode(expected))) return error(401, "shortcut_auth");
      return visitDevice(request, env, url, lang);
    }
    const isAuthForm = url.pathname === "/auth/login" || url.pathname === "/auth/logout";
    if (isAuthForm && request.method === "GET") {
      const next = url.searchParams.get("next");
      return redirect("/?lang=" + lang + (entryPages.has(next) ? "&next=" + encodeURIComponent(next) : ""));
    }
    if (request.method === "POST" && (request.headers.get("Origin") !== url.origin ||
        request.headers.get("Sec-Fetch-Site") === "cross-site")) {
      if (isAuthForm && request.headers.get("Accept")?.includes("text/html")) {
        const next = url.searchParams.get("next");
        return html(loginPage(lang, entryPages.has(next) ? next : "/", "retry"), 403);
      }
      return error(403, "origin");
    }
    if (url.pathname === "/auth/login" && request.method === "POST") return login(request, env, url, lang);
    const raw = cookieToken(request, COOKIE);
    const hash = raw && await tokenHash(raw);
    if (url.pathname === "/auth/logout" && request.method === "POST") {
      if (hash) await env.SESSIONS.prepare("DELETE FROM sessions WHERE token_hash=?").bind(hash).run();
      return redirect("/?lang=" + lang, COOKIE + "=; " + flags + "; Max-Age=0");
    }
    const signedIn = hash && await env.SESSIONS.prepare("SELECT scope FROM sessions WHERE token_hash=? AND expires>?")
      .bind(hash, Math.floor(Date.now()/1000)).first();
    if (request.method === "POST" && ["/iphone/pair/start", "/iphone/pair/status"].includes(url.pathname)) {
      if (signedIn) return reply('{"linked":true}', 200, "application/json");
      return phonePairing(request, env, { cookieToken, tokenHash, flags, reply, error, randomToken, sessionCookie });
    }
    if (url.pathname === "/iphone" && !signedIn && request.method === "GET") return html(phonePairPage(lang));
    if (url.pathname === "/bridge" && request.method === "GET") return redirect(destination("/iphone", lang));
    if (url.pathname === "/" && (request.method === "GET" || request.method === "HEAD")) {
      if (request.method === "HEAD") return html(null);
      const next = entryPages.has(url.searchParams.get("next")) ? url.searchParams.get("next") : "/";
      if (!signedIn) return html(loginPage(lang, next));
      if (next !== "/" && (signedIn.scope === "operator" || phoneEntries.has(next))) return redirect(destination(next, lang));
      if (signedIn.scope === "phone") return html(loginPage(lang, next));
      return html(homePage(lang));
    }
    if (!signedIn) {
      return entryPages.has(url.pathname) && request.method === "GET"
        ? redirect("/?lang=" + lang + "&next=" + encodeURIComponent(url.pathname)) : error(401, "sign_in");
    }
    if (request.method === "HEAD") return error(405, "method");
    if (url.pathname === "/atajos" && request.method === "GET") return html(shortcutsPage(lang));
    const credential = /^\/atajos\/autorizacion\/(screenshot|clipboard)$/.exec(url.pathname);
    if (credential && request.method === "POST") {
      if (!env.SHORTCUT_KEY) return error(503, "shortcut_unavailable");
      return reply(await shortcutCredential(env, "/api/bridge/" + credential[1]), 200, "text/plain; charset=utf-8");
    }
    if (signedIn.scope !== "operator" && !(request.method === "GET" ? phoneReads : phoneWrites).has(url.pathname)) {
      return error(403, "operator_required");
    }
    if (url.pathname === "/tareas" && request.method === "GET") return html(tasksPage(lang));
    if (url.pathname === "/camara" && request.method === "GET") {
      return reply(cameraPage(lang), 200, "text/html; charset=utf-8", {
        "Content-Security-Policy": portalCsp.replace("img-src 'self' data:", "img-src 'self' data: blob:"),
      });
    }
    if (url.pathname === "/operator/pair-phone" && request.method === "POST") {
      return approvePhone(request, env, { readBody, error, reply });
    }
    return visitDevice(request, env, url, lang);
  },
};
