import { build } from "esbuild";
import { fileURLToPath } from "node:url";

await build({
  entryPoints: [fileURLToPath(new URL("./viewer.mjs", import.meta.url))],
  outfile: fileURLToPath(new URL("../../public/assets/v2/visor/visor.js", import.meta.url)),
  bundle: true,
  minify: true,
  legalComments: "inline",
  format: "esm",
  target: "es2022",
  supported: { "template-literal": false },
});
