// Copies the pinned vendor libraries from node_modules into assets/vendor and rewrites MANIFEST.json.
// Run: npm ci && npm run vendor   (versions come from package.json, which is the single source of truth)
import { createHash } from "node:crypto";
import { copyFileSync, mkdirSync, readFileSync, writeFileSync, statSync } from "node:fs";
import { gzipSync } from "node:zlib";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const out = join(here, "..", "..", "assets", "vendor");
const nm = join(here, "node_modules");
const version = (pkg) => JSON.parse(readFileSync(join(nm, pkg, "package.json"), "utf8")).version;

const files = [
  { name: "lenis.min.js", from: join(nm, "lenis", "dist", "lenis.min.js"), pkg: "lenis", licence: "MIT" },
  { name: "gsap.min.js", from: join(nm, "gsap", "dist", "gsap.min.js"), pkg: "gsap", licence: "GSAP Standard 'no charge' licence" },
  { name: "ScrollTrigger.min.js", from: join(nm, "gsap", "dist", "ScrollTrigger.min.js"), pkg: "gsap", licence: "GSAP Standard 'no charge' licence" },
];
mkdirSync(out, { recursive: true });
const manifest = { generated_by: "tools/hero3d/vendor.mjs", files: {} };
for (const f of files) {
  const dest = join(out, f.name);
  copyFileSync(f.from, dest);
  const buf = readFileSync(dest);
  manifest.files[f.name] = {
    package: f.pkg,
    version: version(f.pkg),
    licence: f.licence,
    sha256: createHash("sha256").update(buf).digest("hex"),
    bytes: statSync(dest).size,
    gzip_bytes: gzipSync(buf, { level: 9 }).length,
  };
}
writeFileSync(join(out, "MANIFEST.json"), JSON.stringify(manifest, null, 2) + "\n");
console.log("vendored", Object.keys(manifest.files).join(", "));
