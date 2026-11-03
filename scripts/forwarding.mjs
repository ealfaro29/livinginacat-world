// Consume the complete current Speedy review. Membership in the project does
// not affect the amount, and no package-level fields leave this calculation.
export function aggregateForwardingCharges(packages, { hasUnquotedPackages = false } = {}) {
  const amounts = new Map();
  for (const pkg of packages) {
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
    amountCRC: [...amounts.values()].reduce((sum, amount) => sum + amount, 0),
    scope: "all_current_packages",
    quoteStatus: hasUnquotedPackages ? "awaiting_remaining_quotes" : "currently_quoted",
    payment: "unconfirmed",
    finalConsolidatedChargeConfirmed: false,
  };
}
