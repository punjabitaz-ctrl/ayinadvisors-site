"""Phase 2d (3D hero, smooth scroll, depth): the static guarantees. No browser, no node needed.

The browser behaviour lives in tests/a11y_browser/test_hero3d.py.
"""
import gzip
import hashlib
import json
import re
from pathlib import Path

from bs4 import BeautifulSoup

import build
from conftest import PAGES, ROOT

ASSETS = ROOT / "assets"
VENDOR = ASSETS / "vendor"
HERO_BUDGET_GZ = 200 * 1024
VENDOR_BUDGET_GZ = 120 * 1024
VENDOR_FILES = ("lenis.min.js", "gsap.min.js", "ScrollTrigger.min.js")
SHARED_SCRIPTS = [f"assets/vendor/{n}" for n in VENDOR_FILES] + ["assets/motion.js"]


def _lf(data: bytes) -> bytes:
    """Hash text as git stores it (LF), so a CRLF checkout (autocrlf) does not break the recorded hashes."""
    return data.replace(b"\r\n", b"\n")


def _gz(path: Path) -> int:
    return len(gzip.compress(path.read_bytes(), 9))


def _head_scripts(stem: str) -> list[dict]:
    soup = BeautifulSoup((ROOT / f"{stem}.html").read_text(encoding="utf-8"), "html.parser")
    return [s.attrs for s in soup.head.find_all("script", src=True)]


# ---------------------------------------------------------------- vendor libraries

def test_vendor_files_exist_and_match_the_manifest():
    manifest = json.loads((VENDOR / "MANIFEST.json").read_text(encoding="utf-8"))["files"]
    assert set(manifest) == set(VENDOR_FILES)
    for name, meta in manifest.items():
        data = (VENDOR / name).read_bytes()
        assert hashlib.sha256(_lf(data)).hexdigest() == meta["sha256"], f"{name} differs from MANIFEST.json (re-run tools/hero3d vendor)"
        assert re.fullmatch(r"\d+\.\d+\.\d+", meta["version"]), name
        assert meta["licence"]


def test_manifest_versions_are_pinned_to_package_json():
    pkg = json.loads((ROOT / "tools" / "hero3d" / "package.json").read_text(encoding="utf-8"))
    pins = {**pkg["dependencies"], **pkg["devDependencies"]}
    manifest = json.loads((VENDOR / "MANIFEST.json").read_text(encoding="utf-8"))["files"]
    for name, meta in manifest.items():
        want = pins[meta["package"]]
        assert re.fullmatch(r"\d+\.\d+\.\d+", want), f"{meta['package']} must be an exact version, not a range: {want}"
        assert meta["version"] == want, name


def test_licences_are_shipped_alongside():
    text = (VENDOR / "LICENSES.md").read_text(encoding="utf-8")
    for needle in ("Lenis", "MIT License", "GSAP", "gsap.com/standard-license", "three.js"):
        assert needle in text, needle


def test_vendor_budget_gzip():
    total = sum(_gz(VENDOR / n) for n in VENDOR_FILES)
    assert total <= VENDOR_BUDGET_GZ, f"vendor libraries are {total} bytes gzipped (budget {VENDOR_BUDGET_GZ})"


# ---------------------------------------------------------------- hero bundle

def test_hero_bundle_budget_gzip():
    size = _gz(ASSETS / "hero3d.js")
    assert size <= HERO_BUDGET_GZ, f"assets/hero3d.js is {size} bytes gzipped (budget {HERO_BUDGET_GZ})"


def test_hero_bundle_is_not_stale():
    """The committed bundle is what the source and lockfile build to (hashes recorded by tools/hero3d/build.mjs).
    Cheap on purpose: it compares recorded hashes, so it needs neither node nor esbuild."""
    meta = json.loads((ASSETS / "hero3d.build.json").read_text(encoding="utf-8"))
    src = ROOT / "tools" / "hero3d"
    want = hashlib.sha256(_lf((src / "src" / "main.js").read_bytes()) + _lf((src / "package-lock.json").read_bytes())).hexdigest()
    assert meta["source_sha256"] == want, "tools/hero3d/src/main.js or package-lock.json changed: run `npm run build` in tools/hero3d and commit"
    assert meta["bundle_sha256"] == hashlib.sha256(_lf((ASSETS / "hero3d.js").read_bytes())).hexdigest(), "assets/hero3d.js was edited by hand"


def test_hero_bundle_has_no_network_and_no_eval():
    text = (ASSETS / "hero3d.js").read_text(encoding="utf-8")
    for needle in ("fetch(", "XMLHttpRequest", "eval(", "new Function"):
        assert needle not in text, needle


def test_node_modules_is_ignored_and_not_tracked():
    assert "tools/hero3d/node_modules/" in (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()
    robots = (ROOT / "robots.txt").read_text(encoding="utf-8")
    assert "Disallow: /tools/" in robots      # the tool folder (and any node_modules inside it) is not for crawlers


# ---------------------------------------------------------------- page wiring

def test_every_page_loads_the_shared_scripts_deferred_in_order():
    for stem in PAGES:
        scripts = _head_scripts(stem)
        root = build.page_root(stem)
        srcs = [s["src"][len(root):] if s["src"].startswith(root) else s["src"] for s in scripts]
        shared = [s for s in srcs if s in SHARED_SCRIPTS]
        assert shared == SHARED_SCRIPTS, f"{stem}: {shared}"
        for s in scripts:
            assert "defer" in s, f"{stem}: {s['src']} must be deferred"


def test_only_home_loads_the_hero_bundle():
    for stem in PAGES:
        srcs = [s["src"].removeprefix(build.page_root(stem)) for s in _head_scripts(stem)]
        assert ("assets/hero3d.js" in srcs) == (stem == "index"), stem
        html = (ROOT / f"{stem}.html").read_text(encoding="utf-8")
        assert ("hero3d" in html) == (stem == "index"), stem


def test_scripts_come_from_this_origin_only():
    for stem in PAGES:
        for s in _head_scripts(stem):
            if "challenges.cloudflare.com" in s["src"]:      # Turnstile on the form pages, allowed by the CSP since before 2d
                continue
            assert not re.match(r"(https?:)?//", s["src"]), f"{stem}: {s['src']}"
    for f in [ASSETS / "motion.js", ASSETS / "hero3d.js", *[VENDOR / n for n in VENDOR_FILES]]:
        text = f.read_text(encoding="utf-8")
        assert not re.search(r"""(?:src|href|import|from)\s*[=(]?\s*["']https?://(?!www\.w3\.org|threejs\.org|gsap\.com|github\.com)""", text), f.name


def test_csp_covers_the_new_scripts_without_loosening():
    headers = (ROOT / "_headers").read_text(encoding="utf-8")
    csp = next(l for l in headers.splitlines() if l.strip().startswith("Content-Security-Policy:"))
    script_src = re.search(r"script-src ([^;]+)", csp).group(1).split()
    assert "'self'" in script_src
    assert "'unsafe-eval'" not in script_src and "'strict-dynamic'" not in script_src
    assert not any(t.startswith("'nonce-") for t in script_src)
    assert "worker-src" not in csp or "'self'" in csp
