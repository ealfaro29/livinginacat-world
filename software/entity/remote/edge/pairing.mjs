const PAIR_COOKIE = "__Host-entity_pair";
const PAIR_SECONDS = 600;
export const PHONE_LIFETIME = 90 * 24 * 60 * 60;

export async function phonePairing(request, env, helpers) {
  const { cookieToken, tokenHash, flags, reply, error, sessionCookie } = helpers;
  const path = new URL(request.url).pathname;
  const now = Math.floor(Date.now() / 1000);
  let token = cookieToken(request, PAIR_COOKIE);
  let hash = token && await tokenHash(token);
  const record = hash && await env.SESSIONS.prepare("SELECT code, expires, approved FROM phone_pairing WHERE token_hash=? AND expires>?").bind(hash, now).first();
  if (record?.approved) {
    await env.SESSIONS.batch([
      env.SESSIONS.prepare("INSERT OR IGNORE INTO sessions(token_hash,expires,scope) SELECT token_hash,?,'phone' FROM phone_pairing WHERE token_hash=? AND approved=1 AND expires>?")
        .bind(now + PHONE_LIFETIME, hash, now),
      env.SESSIONS.prepare("DELETE FROM phone_pairing WHERE token_hash=? AND approved=1").bind(hash),
    ]);
  }
  // Recover a lost acknowledgement from a live phone session. Signing out also
  // revokes this recovery path because the one-time code has been consumed.
  if (hash && (!record || record.approved)) {
    const linked = await env.SESSIONS.prepare("SELECT expires FROM sessions WHERE token_hash=? AND scope='phone' AND expires>?").bind(hash, now).first();
    if (linked) {
      const res = reply('{"linked":true}', 200, "application/json");
      res.headers.append("Set-Cookie", sessionCookie(token, linked.expires - now));
      res.headers.append("Set-Cookie", PAIR_COOKIE + "=; " + flags + "; Max-Age=0");
      return res;
    }
    if (record?.approved) return error(410, "pairing_expired");
  }
  if (record) {
    return reply(JSON.stringify({ code: record.code, expires: record.expires }), 200, "application/json");
  }
  if (path.endsWith("/status")) return error(410, "pairing_expired");
  const ip = request.headers.get("CF-Connecting-IP") || "direct";
  if (!(await env.LOGIN_LIMIT.limit({ key: "phone-pair:" + ip })).success) return error(429, "retry");
  token = helpers.randomToken();
  hash = await tokenHash(token);
  await env.SESSIONS.prepare("DELETE FROM phone_pairing WHERE expires<=?").bind(now).run();
  for (let attempt = 0; attempt < 3; attempt++) {
    const code = String(crypto.getRandomValues(new Uint32Array(1))[0] % 100000000).padStart(8, "0");
    const insert = await env.SESSIONS.prepare("INSERT OR IGNORE INTO phone_pairing(token_hash, code, expires) VALUES(?,?,?)")
      .bind(hash, code, now + PAIR_SECONDS).run();
    if (insert.meta.changes === 1) {
      return reply(JSON.stringify({ code, expires: now + PAIR_SECONDS }), 200, "application/json", {
        "Set-Cookie": PAIR_COOKIE + "=" + token + "; " + flags + "; Max-Age=" + PAIR_SECONDS,
      });
    }
  }
  return error(503, "retry");
}

export async function approvePhone(request, env, { readBody, error, reply }) {
  const body = await readBody(request);
  if (body === null) return error(413, "too_large");
  let code;
  try {
    code = JSON.parse(new TextDecoder().decode(body)).code.replace(/[\s-]/g, "");
  } catch { return error(400, "invalid_code"); }
  if (!/^\d{8}$/.test(code)) return error(400, "invalid_code");
  const ip = request.headers.get("CF-Connecting-IP") || "direct";
  if (!(await env.LOGIN_LIMIT.limit({ key: "approve-phone:" + ip })).success) return error(429, "retry");
  const result = await env.SESSIONS.prepare("UPDATE phone_pairing SET approved=1 WHERE code=? AND expires>?")
    .bind(code, Math.floor(Date.now()/1000)).run();
  if (result.meta.changes !== 1) return error(404, "invalid_code");
  return reply('{"approved":true}', 200, "application/json");
}
