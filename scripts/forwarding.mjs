// Consume the complete current Speedy review. Membership in the project does
// not affect the amount, and no package-level fields leave this calculation.
export function aggregateForwardingCharges(packages, { hasUnquotedPackages = false, settledTrackings = [], hasUnresolvedConsolidationCharges = false } = {}) {
  const amounts = new Map();
  const settled = new Set(settledTrackings);
  for (const pkg of packages) {
    // Settlement is explicit evidence, independent of an unchanged Speedy label.
    if (settled.has(pkg.tracking)) continue;
    if (pkg.amountCRC == null) {
      hasUnquotedPackages = true;
      continue;
    }
    if (!pkg.tracking || !Number.isInteger(pkg.amountCRC) || pkg.amountCRC < 0)
      throw new Error("Invalid current Speedy charge.");
    if (amounts.has(pkg.tracking) && amounts.get(pkg.tracking) !== pkg.amountCRC)
      throw new Error("Conflicting current Speedy charges; review the evidence.");
    amounts.set(pkg.tracking, pkg.amountCRC);
  }
  return {
    currency: "CRC",
    // A consolidated parcel can coexist with its charged contents. Until their
    // billing relationship is verified, a numeric sum would imply false precision.
    amountCRC: hasUnresolvedConsolidationCharges ? null : [...amounts.values()].reduce((sum, amount) => sum + amount, 0),
    scope: "all_current_packages",
    quoteStatus: hasUnresolvedConsolidationCharges ? "reconciliation_pending" : hasUnquotedPackages ? "awaiting_remaining_quotes" : "currently_quoted",
    payment: "unconfirmed",
    finalConsolidatedChargeConfirmed: false,
  };
}
