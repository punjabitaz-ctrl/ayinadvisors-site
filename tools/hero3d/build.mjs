// Bundles src/main.js (plus the parts of three.js it uses) into ../../assets/hero3d.js and records its hash.
// Run: npm ci && npm run build
import { build } from "esbuild";
import { createHash } from "node:crypto";
import { readFileSync, writeFileSync } from "node:fs";
import { gzipSync } from "node:zlib";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const out = join(here, "..", "..", "assets", "hero3d.js");
const pkgVersion = (name) => JSON.parse(readFileSync(join(here, "node_modules", name, "package.json"), "utf8")).version;
const three = pkgVersion("three");
const esb = pkgVersion("esbuild");

await build({
  entryPoints: [join(here, "src", "main.js")],
  outfile: out,
  bundle: true,
  minify: true,
  format: "iife",
  target: ["es2020"],
  legalComments: "none",
  banner: { js: `/* AYiN hero iris. Built from tools/hero3d/src/main.js with three.js r${three.split(".")[1]} (MIT, https://threejs.org). Do not edit; see DEPLOY.md. */` },
  logLevel: "warning",
});

// Hash text as git stores it (LF) so CRLF checkouts (autocrlf) record the same hashes.
const lf = (b) => Buffer.from(b.toString("latin1").replace(/\r\n/g, "\n"), "latin1");
const buf = readFileSync(out);
const meta = {
  generated_by: "tools/hero3d/build.mjs",
  three,
  esbuild: esb,
  source_sha256: createHash("sha256")
    .update(lf(readFileSync(join(here, "src", "main.js"))))
    .update(lf(readFileSync(join(here, "package-lock.json"))))
    .digest("hex"),
  bundle_sha256: createHash("sha256").update(lf(buf)).digest("hex"),
  bytes: buf.length,
  gzip_bytes: gzipSync(buf, { level: 9 }).length,
};
writeFileSync(join(here, "..", "..", "assets", "hero3d.build.json"), JSON.stringify(meta, null, 2) + "\n");
console.log("hero3d.js", meta.bytes, "bytes,", meta.gzip_bytes, "gzip");
