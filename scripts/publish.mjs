import { execFileSync } from "node:child_process";
import fs from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import { root, rootPath, readJSON } from "./lib.mjs";
const cwd = rootPath,
  site = await readJSON("data/site.json");
function run(cmd, args, dir = cwd) {
  return execFileSync(cmd, args, { cwd: dir, stdio: "inherit" });
}
const status = execFileSync("git", ["status", "--porcelain"], {
  cwd,
  encoding: "utf8",
}).trim();
if (status) throw new Error("Commit source changes before publishing.");
const remote = execFileSync("git", ["remote", "get-url", "origin"], {
  cwd,
  encoding: "utf8",
}).trim();
if (!remote.endsWith(`${site.repoOwner}/${site.repoName}.git`))
  throw new Error("Unexpected origin; check destination.");
run("npm", ["test"]);
run("npm", ["run", "build"]);
run("npm", ["run", "check"]);
const tmp = await fs.mkdtemp(path.join(os.tmpdir(), "livinginacat-pages-"));
try {
  run("git", ["clone", "--no-checkout", "--depth", "1", remote, tmp]);
  let hasBranch = true;
  try {
    execFileSync(
      "git",
      ["ls-remote", "--exit-code", "--heads", remote, "gh-pages"],
      { cwd, stdio: "ignore" },
    );
  } catch {
    hasBranch = false;
  }
  if (hasBranch) {
    run("git", ["fetch", "origin", "gh-pages:gh-pages"], tmp);
    run("git", ["checkout", "gh-pages"], tmp);
  } else run("git", ["checkout", "--orphan", "gh-pages"], tmp);
  for (const file of await fs.readdir(tmp))
    if (file !== ".git")
      await fs.rm(path.join(tmp, file), { recursive: true, force: true });
  await fs.cp(new URL("dist/", root), tmp, { recursive: true });
  run("git", ["add", "--all"], tmp);
  const changes = execFileSync("git", ["status", "--porcelain"], {
    cwd: tmp,
    encoding: "utf8",
  }).trim();
  if (changes) {
    const sha = execFileSync("git", ["rev-parse", "--short", "HEAD"], {
      cwd,
      encoding: "utf8",
    }).trim();
    run("git", ["commit", "-m", `Publish site from ${sha}`], tmp);
    run("git", ["push", "origin", "gh-pages"], tmp);
  } else console.log("Pages output is already current.");
} finally {
  await fs.rm(tmp, { recursive: true, force: true });
}
