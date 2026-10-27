export class ApiError extends Error {
  constructor(status, message) {
    super(message);
    this.status = status;
  }
}
export const text = (value, max = 500) =>
  String(value ?? "")
    .trim()
    .slice(0, max);
export function id(value) {
  const result = text(value, 100);
  if (!/^[a-zA-Z0-9_-]{1,80}$/.test(result))
    throw new ApiError(400, "Invalid record ID.");
  return result;
}
export function tracking(value) {
  const result = text(value, 100).replace(/\s|-/g, "").toUpperCase();
  if (result && !/^[A-Z0-9]{6,60}$/.test(result))
    throw new ApiError(400, "Check the tracking number.");
  return result;
}
export function day(value) {
  if (!value) return null;
  const parsed = new Date(value + "T12:00:00Z");
  if (
    !/^\d{4}-\d{2}-\d{2}$/.test(value) ||
    !Number.isFinite(parsed.getTime()) ||
    parsed.toISOString().slice(0, 10) !== value
  )
    throw new ApiError(400, "Use a valid date.");
  return value;
}
export function timestamp(value) {
  if (!value) return null;
  const date = new Date(value);
  if (!Number.isFinite(date.getTime()))
    throw new ApiError(400, "Invalid timestamp.");
  return date.toISOString();
}
export function cents(value) {
  if (value === null || value === undefined || value === "") return null;
  if (!Number.isSafeInteger(value) || value < 0 || value > 100000000)
    throw new ApiError(400, "Invalid amount.");
  return value;
}
export function ready(pkg) {
  const missing = [];
  if (!pkg.tracking) missing.push("Tracking number");
  if (!pkg.carrier) missing.push("Carrier");
  if (!pkg.document || pkg.document.kind !== "invoice")
    missing.push("Invoice PDF");
  return { ready: missing.length === 0, missing };
}
export function packageFacts(input) {
  const status = text(input.shippingStatus, 40) || "awaiting_tracking";
  if (
    ![
      "awaiting_tracking",
      "preparing",
      "shipped",
      "carrier_delivered",
      "on_hold",
    ].includes(status)
  )
    throw new ApiError(400, "Invalid shipping status.");
  return {
    title: text(input.title, 160),
    contents: text(input.contents, 3000),
    carrier: text(input.carrier, 80),
    tracking: tracking(input.tracking),
    shippingStatus: status,
    expectedArrival: day(input.expectedArrival),
    expectedShipDate: day(input.expectedShipDate),
    declaredValueCents: cents(input.declaredValueCents),
    source: text(input.source, 500),
    sourceCheckedAt: timestamp(input.sourceCheckedAt),
  };
}
// Mail imports may update vendor facts, but never overwrite the owner's arrival,
// prealert, notes or uploaded document. Replaying the same email is idempotent.
export function mergeImport(existing, incoming) {
  const facts = packageFacts(incoming);
  if (existing) {
    const oldTime = Date.parse(existing.sourceCheckedAt || 0);
    const newTime = Date.parse(facts.sourceCheckedAt || 0);
    if (oldTime > newTime) return existing;
    if (existing.tracking && !facts.tracking) {
      facts.tracking = existing.tracking;
      facts.carrier = existing.carrier;
    }
  }
  return {
    ...(existing || {
      notes: "",
      prealertedAt: null,
      prealertReference: "",
      lockerArrivedAt: null,
      document: null,
    }),
    ...facts,
  };
}
export function editPackage(existing, input) {
  const next = { ...existing };
  for (const field of [
    "title",
    "contents",
    "carrier",
    "tracking",
    "shippingStatus",
    "expectedArrival",
    "expectedShipDate",
    "declaredValueCents",
  ])
    if (Object.hasOwn(input, field)) next[field] = input[field];
  Object.assign(next, packageFacts(next));
  if (Object.hasOwn(input, "notes")) next.notes = text(input.notes, 5000);
  if (Object.hasOwn(input, "prealertReference"))
    next.prealertReference = text(input.prealertReference, 160);
  if (Object.hasOwn(input, "prealertedAt"))
    next.prealertedAt = timestamp(input.prealertedAt);
  if (Object.hasOwn(input, "lockerArrivedAt"))
    next.lockerArrivedAt = timestamp(input.lockerArrivedAt);
  // Existing prealerts may have been submitted directly in Speedy before a local
  // PDF was collected. Preserve that truthful state and show missing files.
  return next;
}
