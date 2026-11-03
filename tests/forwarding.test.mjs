import test from "node:test";
import assert from "node:assert/strict";
import { aggregateForwardingCharges } from "../scripts/forwarding.mjs";

test("Speedy aggregate includes every current package without a project filter", () => {
  const result = aggregateForwardingCharges([
    { tracking: "FIXTURE-A", amountCRC: 1000, project: true },
    { tracking: "FIXTURE-B", amountCRC: 2500, project: false },
    { tracking: "FIXTURE-C", amountCRC: null },
  ]);
  assert.equal(result.amountCRC, 3500);
  assert.equal(result.scope, "all_current_packages");
  assert.equal(result.quoteStatus, "awaiting_remaining_quotes");
  assert.equal(JSON.stringify(result).includes("FIXTURE"), false);
});

test("repeated package references are counted once and conflicting amounts block publication", () => {
  assert.equal(aggregateForwardingCharges([
    { tracking: "FIXTURE-A", amountCRC: 1000 },
    { tracking: "FIXTURE-A", amountCRC: 1000 },
  ]).amountCRC, 1000);
  assert.throws(() => aggregateForwardingCharges([
    { tracking: "FIXTURE-A", amountCRC: 1000 },
    { tracking: "FIXTURE-A", amountCRC: 2000 },
  ]), /Conflicting/);
});
