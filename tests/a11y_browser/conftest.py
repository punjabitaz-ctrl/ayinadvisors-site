"""Shared browser fixtures for the accessibility gate.

The repo root is served read-only through a ThreadingHTTPServer on a free port;
nothing here writes into the working tree. If Chromium cannot launch, every
test using the `browser` fixture skips with the install command in the reason.
"""
import functools
import http.server
import threading
from typing import NamedTuple

import pytest

from conftest import ROOT, PAGES  # noqa: F401  (re-exported for the browser tests)

WIDTHS = (320, 768, 1280)
AXE_TAGS = ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa", "best-practice"]
AXE_OPTIONS = {
    "runOnly": {"type": "tag", "values": AXE_TAGS},
    "resultTypes": ["violations", "incomplete"],
}
# Force scroll-reveal content visible so axe sees real colours, not opacity:0.
REVEAL_CSS = (
    ".reveal,.line-reveal>span{opacity:1!important;transform:none!important;"
    "transition:none!important;animation:none!important}"
)
INSTALL_HINT = "run `python -m playwright install chromium` to enable the browser tests"


class Violation(NamedTuple):
    rule: str
    nodes: int
    impact: str
    selectors: tuple


class NeedsReview(NamedTuple):
    rule: str
    selectors: tuple


class _QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):  # silence request logging
        pass


def start_server():
    """Serve the repo root read-only on a free port; returns (server, base_url)."""
    handler = functools.partial(_QuietHandler, directory=str(ROOT))
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server, f"http://127.0.0.1:{server.server_address[1]}"


@pytest.fixture(scope="session")
def site_url():
    server, url = start_server()
    yield url
    server.shutdown()
    server.server_close()


@pytest.fixture(scope="session")
def browser():
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        pytest.skip(f"playwright is not installed; {INSTALL_HINT}")
    pw = sync_playwright().start()
    try:
        try:
            b = pw.chromium.launch()
        except Exception as e:  # missing browser binary, sandbox problems, ...
            pytest.skip(f"Chromium unavailable ({type(e).__name__}); {INSTALL_HINT}")
        yield b
        b.close()
    finally:
        pw.stop()


def new_context(browser, width=1280, height=900, **kw):
    """A context that only talks to the local server (no web fonts, no Turnstile)."""
    ctx = browser.new_context(viewport={"width": width, "height": height}, **kw)
    ctx.route(
        "**/*",
        lambda route: route.continue_() if route.request.url.startswith(("http://127.0.0.1", "data:"))
        else route.abort(),
    )
    return ctx


def open_page(ctx, site_url, stem):
    page = ctx.new_page()
    page.goto(f"{site_url}/{stem}.html", wait_until="load")
    return page


def _selector(node) -> str:
    return " ".join(node.get("target") or []) if isinstance(node.get("target"), list) else str(node.get("target"))


def _axe(page):
    from axe_playwright_python.sync_playwright import Axe

    page.add_style_tag(content=REVEAL_CSS)
    page.evaluate("document.querySelectorAll('.reveal,.line-reveal').forEach(e=>e.classList.add('in'))")
    return Axe().run(page, options=AXE_OPTIONS).response


def run_axe(page, width) -> list[Violation]:
    """Violations for the page as currently loaded at `width` (WCAG 2.0-2.2 A/AA + best practice)."""
    page.set_viewport_size({"width": width, "height": 900})
    res = _axe(page)
    return [
        Violation(v["id"], len(v["nodes"]), v.get("impact") or "", tuple(sorted(_selector(n) for n in v["nodes"])))
        for v in res["violations"]
    ]


def run_axe_full(page, width) -> tuple[list[Violation], list[NeedsReview]]:
    page.set_viewport_size({"width": width, "height": 900})
    res = _axe(page)
    viol = [
        Violation(v["id"], len(v["nodes"]), v.get("impact") or "", tuple(sorted(_selector(n) for n in v["nodes"])))
        for v in res["violations"]
    ]
    review = [NeedsReview(i["id"], tuple(sorted(_selector(n) for n in i["nodes"]))) for i in res["incomplete"]]
    return viol, review


def collect_axe(browser, site_url, stem, width):
    """Fresh context/page per (page, width); returns (violations, needs_review)."""
    # Reduced motion renders every assemble/tilt item in its settled state. With default motion, items still in
    # their hidden "pre" state are opacity 0 and axe skips them as hidden, leaving real text unchecked.
    ctx = new_context(browser, width, reduced_motion="reduce")
    try:
        page = open_page(ctx, site_url, stem)
        return run_axe_full(page, width)
    finally:
        ctx.close()


@pytest.fixture(scope="session")
def axe_cache(browser, site_url):
    cache: dict = {}

    def get(stem, width):
        if (stem, width) not in cache:
            cache[(stem, width)] = collect_axe(browser, site_url, stem, width)
        return cache[(stem, width)]

    return get
