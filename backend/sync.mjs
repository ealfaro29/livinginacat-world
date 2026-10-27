// Private ingestion helper. Credentials and original documents are never copied
// into the public site, source history, command arguments or console output.
import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
const root = fileURLToPath(new URL("../", import.meta.url));
const config = JSON.parse(
  await fs.readFile(path.join(root, "private/admin-credentials.json"), "utf8"),
);
const [command, file, kind = "invoice"] = process.argv.slice(2);
async function request(route, options = {}) {
  const r = await fetch(config.url + route, {
    ...options,
    headers: {
      Authorization: "Bearer " + config.ingestToken,
      ...options.headers,
    },
  });
  if (!r.ok)
    throw new Error(
      `Private sync failed (${r.status}): ${(await r.json()).error}`,
    );
  return r.json();
}
if (command === "import") {
  const result = await request("/api/ingest", {
    method: "POST",
    body: await fs.readFile(path.resolve(file), "utf8"),
    headers: { "Content-Type": "application/json" },
  });
  console.log(`Synchronized ${result.updated.length} records.`);
} else if (command === "confirm-speedy") {
  await request("/api/ingest/speedy", {
    method: "POST",
    body: await fs.readFile(path.resolve(file), "utf8"),
    headers: { "Content-Type": "application/json" },
  });
  console.log("Verified Speedy events synchronized.");
} else if (command === "snapshot") {
  const snapshot = await request("/api/ingest/snapshot");
  const destination = path.join(root, "private/admin-snapshot.json");
  await fs.writeFile(destination, JSON.stringify(snapshot, null, 2), {
    mode: 0o600,
  });
  console.log(
    `Saved private snapshot: ${snapshot.orders.length} orders, ${snapshot.packages.length} package records.`,
  );
} else if (command === "upload") {
  // upload arguments: package ID, absolute/local PDF path, document kind
  const packageId = file,
    pdf = process.argv[4],
    documentKind = process.argv[5] || "invoice";
  const snapshot = await request("/api/ingest/snapshot"),
    pkg = snapshot.packages.find((x) => x.id === packageId);
  if (!pkg) throw new Error("Package not found.");
  const bytes = await fs.readFile(path.resolve(pdf));
  await request(
    "/api/ingest/packages/" +
      encodeURIComponent(packageId) +
      "/document?" +
      new URLSearchParams({ name: path.basename(pdf), kind: documentKind }),
    {
      method: "POST",
      body: bytes,
      headers: {
        "Content-Type": "application/pdf",
        "X-Record-Version": String(pkg.version),
      },
    },
  );
  console.log("PDF stored privately.");
} else
  throw new Error(
    "Use import <private.json>, snapshot, or upload <package-id> <pdf> <kind>.",
  );
