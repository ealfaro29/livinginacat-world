import test from "node:test";
import assert from "node:assert/strict";
import { assertPublicText, identityHash } from "../scripts/privacy.mjs";
import { readJSON } from "../scripts/lib.mjs";
test("public ledger excludes private purchase identities while keeping totals", async () => {
  const ledger = await readJSON("data/ledger.json");
  assert.doesNotThrow(() => assertPublicText(JSON.stringify(ledger), "ledger"));
  assert.equal(
    ledger.otherExpenses
      .filter((x) => x.includedInVendorOrderTotals)
      .reduce((n, x) => n + x.categoryTotalCents, 0),
    52770,
  );
});
test("publication guard recognizes normalized phrases without exposing identities", () => {
  const hashes = new Set([identityHash("sampleprivateitem")]);
  assert.throws(() =>
    assertPublicText("Sample / prívate — item", "fixture", hashes),
  );
  assert.doesNotThrow(() =>
    assertPublicText("Other expenses: $12.34", "fixture", hashes),
  );
});
