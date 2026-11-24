import assert from "node:assert/strict";
import test from "node:test";
import worker from "./worker.mjs";

const site = "https://entity.livinginacat.world";
const post = (path, headers) => worker.fetch(new Request(site + path, { method: "POST", headers }), {});

test("the sign-in document allows the browser to send Origin on its own form POST", async () => {
  const page = await worker.fetch(new Request(site + "/"), {});
  assert.equal(page.headers.get("Referrer-Policy"), "same-origin");
  assert.match(await page.text(), /<form method="post" action="\/auth\/login\?/);
});

test("the old form can recover in either language without accepting an opaque origin", async () => {
  for (const [language, notice] of [["en", "Please sign in again"], ["es", "Volvé a ingresar"]]) {
    const response = await post("/auth/login?lang=" + language + "&next=%2Fcontrol", {
      Origin: "null", Accept: "text/html", "Sec-Fetch-Site": "same-origin",
    });
    assert.equal(response.status, 403);
    assert.equal(response.headers.get("Set-Cookie"), null);
    assert.equal(response.headers.get("Referrer-Policy"), "same-origin");
    const page = await response.text();
    assert.ok(page.includes(notice));
    assert.ok(page.includes("next=%2Fcontrol"));
  }
});

test("reopening a login address returns to the local sign-in page", async () => {
  const response = await worker.fetch(new Request(site + "/auth/login?lang=en&next=%2Fcontrol"), {});
  assert.equal(response.status, 303);
  assert.equal(response.headers.get("Location"), "/?lang=en&next=%2Fcontrol");
});

test("an off-site POST cannot sign out or act on the device", async () => {
  for (const path of ["/auth/logout", "/api/connect-arm"]) {
    const response = await post(path, { Origin: "https://example.org", "Sec-Fetch-Site": "cross-site" });
    assert.equal(response.status, 403);
    assert.deepEqual(await response.json(), { error: "origin" });
    assert.equal(response.headers.get("Set-Cookie"), null);
  }
});
