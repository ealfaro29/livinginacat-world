import http from "node:http";
import fs from "node:fs/promises";
import path from "node:path";
import { rootPath } from "./lib.mjs";
const base = path.join(rootPath, "dist/"),
  port = Number(process.env.PORT ?? 4173);
const types = {
  ".html": "text/html; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".svg": "image/svg+xml",
  ".png": "image/png",
  ".zip": "application/zip",
  ".xml": "application/xml; charset=utf-8",
  ".md": "text/markdown; charset=utf-8",
  ".csv": "text/csv; charset=utf-8",
};
http
  .createServer(async (req, res) => {
    try {
      let urlPath = decodeURIComponent(
        new URL(req.url, "http://localhost").pathname,
      );
      if (urlPath.endsWith("/")) urlPath += "index.html";
      const file = path.resolve(base, "." + urlPath);
      if (!file.startsWith(base)) {
        res.writeHead(403);
        res.end();
        return;
      }
      const data = await fs.readFile(file);
      res.writeHead(200, {
        "Content-Type": types[path.extname(file)] ?? "application/octet-stream",
        "Cache-Control": "no-cache",
      });
      res.end(data);
    } catch {
      res.writeHead(404, { "Content-Type": "text/html; charset=utf-8" });
      res.end(await fs.readFile(path.join(base, "404.html")));
    }
  })
  .listen(port, "127.0.0.1", () =>
    console.log(`Preview: http://127.0.0.1:${port}`),
  );
