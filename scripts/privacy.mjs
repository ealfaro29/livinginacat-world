import { createHash } from "node:crypto";
import { readJSON } from "./lib.mjs";
const policy = await readJSON("data/public-privacy.json");
const restricted = new Set(policy.restrictedIdentityHashes);
export const identityHash = (value) =>
  createHash("sha256").update(value).digest("hex");
export function assertPublicText(
  value,
  label = "public content",
  hashes = restricted,
) {
  const words =
    String(value)
      .normalize("NFKD")
      .replace(/\p{M}/gu, "")
      .toLowerCase()
      .match(/[a-z0-9]+/g) || [];
  for (let start = 0; start < words.length; start++) {
    let phrase = "";
    for (let size = 0; size < 5 && start + size < words.length; size++) {
      phrase += words[start + size];
      if (hashes.has(identityHash(phrase)))
        throw new Error(
          `Private purchase identity detected in ${label}. Keep item details private and publish only the grouped amount.`,
        );
    }
  }
}
