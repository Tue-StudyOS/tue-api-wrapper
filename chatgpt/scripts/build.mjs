import { build } from "esbuild";
import { rm } from "node:fs/promises";

const workingDirectory = process.cwd();
await Promise.all(["web/dist/widget.js.map", "web/dist/widget.css.map"].map((path) => rm(path, { force: true })));

await build({
  absWorkingDir: workingDirectory,
  entryPoints: { index: "src/index.ts", "link-sidecar": "src/relay/client.ts", "export-tools": "src/export-tools.ts" },
  outdir: "dist",
  bundle: true,
  platform: "node",
  format: "esm",
  packages: "external",
  minify: true,
  sourcemap: false,
  target: "node24"
});

await build({
  absWorkingDir: workingDirectory,
  entryPoints: ["web/src/main.ts"],
  outdir: "web/dist",
  entryNames: "widget",
  bundle: true,
  format: "esm",
  platform: "browser",
  loader: {
    ".css": "css"
  },
  minify: true,
  sourcemap: false,
  target: "es2022"
});
