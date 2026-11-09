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

export const trackingPhases = ["shipped", "miami", "costa_rica", "delivered"];
export function trackingItemFacts(input) {
  if (!["project", "personal"].includes(input.scope))
    throw new ApiError(400, "Choose project or personal.");
  const title = text(input.title, 240);
  if (!title) throw new ApiError(400, "An item description is required.");
  const stages = {};
  for (const phase of trackingPhases) {
    const value = input.stages?.[phase] ?? false;
    if (typeof value !== "boolean") throw new ApiError(400, "Invalid tracking phase.");
    stages[phase] = value;
  }
  return {
    title,
    vendor: text(input.vendor, 80),
    quantity: text(input.quantity, 80),
    note: text(input.note, 1000),
    shippingRequired: input.shippingRequired !== false,
    stages,
    source: text(input.source, 200),
    sourceCheckedAt: timestamp(input.sourceCheckedAt),
  };
}
export function mergeTrackingFacts(existing, input) {
  const next = trackingItemFacts(input);
  if (existing && Date.parse(existing.sourceCheckedAt || 0) > Date.parse(next.sourceCheckedAt || 0))
    return existing;
  // New evidence can advance a phase. Owner marks are stored separately and
  // never overwritten by ingestion. Keep the original evidence when corrected.
  for (const phase of trackingPhases)
    next.stages[phase] ||= existing?.stages?.[phase] === true;
  return next;
}
export function trackingItemView(row) {
  const facts = JSON.parse(row.data), marks = JSON.parse(row.owner_marks);
  return {
    ...facts,
    id: row.id,
    scope: row.scope,
    version: row.version,
    updatedAt: row.updated_at,
    stages: Object.fromEntries(trackingPhases.map((phase) => [phase,
      Object.hasOwn(marks, phase) ? marks[phase] : facts.stages[phase],
    ])),
    manuallyMarked: Object.keys(marks),
  };
}

// Shared-order originals are evidence for ingestion, not content for the room.
// Preserve stored evidence and owner fields; redact only the interactive view.
const restrictedOrders = new Set([
  "AMZ-02", "AMZ-03", "AMZ-04", "AMZ-05", "AMZ-07", "walmart", "bambu-lab",
]);
export const hasRestrictedDetails = (record) =>
  restrictedOrders.has(record.orderId ?? record.id);
export function projectRoomSnapshot(snapshot) {
  const completedOrders = new Set(snapshot.orders
    .filter((order) => order.status === "carrier_delivered")
    .map((order) => order.id));
  const trackedOrders = new Set(snapshot.packages
    .filter((pkg) => pkg.tracking)
    .map((pkg) => pkg.orderId));
  // Imported *-AWAIT preparation records become order summaries after complete
  // fulfillment. Preserve manual records, stored originals and owner evidence.
  const packages = snapshot.packages.filter((pkg) => !(
    pkg.id.endsWith("-AWAIT") && !pkg.tracking && completedOrders.has(pkg.orderId) && trackedOrders.has(pkg.orderId) &&
    !pkg.notes && !pkg.document && !pkg.prealertedAt && !pkg.prealertReference &&
    !pkg.consolidationReference && !pkg.lockerArrivedAt && !pkg.speedyStatus
  ));
  return {
    ...snapshot,
    orders: snapshot.orders.map((order) => hasRestrictedDetails(order) ? {
      ...order,
      title: "Project order",
      orderReference: order.id,
      notes: "Taxes, tariffs, shipping and others are grouped in the order total.",
      source: "Reviewed order evidence",
    } : order),
    packages: packages.map((pkg) => hasRestrictedDetails(pkg) ? {
      ...pkg,
      title: "Project shipment",
      contents: "",
      notes: "",
      declaredValueCents: null,
      source: "Reviewed shipment evidence",
      speedyStatusSource: pkg.speedyStatus ? "Speedy status verified" : undefined,
      speedyEvidence: undefined,
      invoiceVerified: pkg.document?.kind === "invoice",
      document: null,
      restrictedDetails: true,
    } : pkg),
    history: snapshot.history.map(({ detail, ...event }) => ({ ...event, detail: {} })),
  };
}
