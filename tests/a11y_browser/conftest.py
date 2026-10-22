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
THEMES = ("light", "dark")
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
    # axe's own selector for a node -> the entry selectors of tests/a11y_review.json that match that element
    # (`element.matches`), so an entry can name its element by a stable selector instead of axe's generated one.
    matched: dict = {}


class _QuietHandler(http.server.SimpleHTTPRequestHandler):
    # Keep-alive: every response from SimpleHTTPRequestHandler (files, redirects, errors) carries a Content-Length, so
    # the browser reuses its connections instead of opening a socket per asset. Opening one per request exhausted
    # Windows ephemeral ports in long runs (net::ERR_NO_BUFFER_SPACE).
    protocol_version = "HTTP/1.1"

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
def playwright_instance():
    """The ONE Playwright driver per session (a second sync_playwright().start() in the same process fails inside the
    first one's event loop). Tests that need their own browser launch from this."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        pytest.skip(f"playwright is not installed; {INSTALL_HINT}")
    pw = sync_playwright().start()
    try:
        yield pw
    finally:
        pw.stop()


@pytest.fixture(scope="session")
def browser(playwright_instance):
    try:
        b = playwright_instance.chromium.launch()
    except Exception as e:  # missing browser binary, sandbox problems, ...
        pytest.skip(f"Chromium unavailable ({type(e).__name__}); {INSTALL_HINT}")
    yield b
    b.close()


def new_context(browser, width=1280, height=900, theme=None, **kw):
    """A context that only talks to the local server (no web fonts, no Turnstile).

    `theme` ("light" | "dark") renders the page in that theme the way a visitor gets it: the system colour scheme
    is emulated AND the choice is stored under `ayin-theme`; `open_page` then asserts `html[data-theme]`.
    """
    if theme:
        assert theme in THEMES, theme
        kw["color_scheme"] = theme
    ctx = browser.new_context(viewport={"width": width, "height": height}, **kw)
    ctx._ayin_theme = theme
    if theme:
        ctx.add_init_script(f"try {{ localStorage.setItem('ayin-theme', '{theme}'); }} catch (e) {{}}")
    ctx.route(
        "**/*",
        lambda route: route.continue_() if route.request.url.startswith(("http://127.0.0.1", "data:"))
        else route.abort(),
    )
    return ctx


def assert_theme(page, theme):
    got = page.evaluate("document.documentElement.dataset.theme")
    assert got == theme, f"expected html[data-theme]={theme!r}, page has {got!r}"


def open_page(ctx, site_url, stem):
    page = ctx.new_page()
    try:
        page.goto(f"{site_url}/{stem}.html", wait_until="load")
    except Exception as e:  # a transient Windows socket-buffer error on the local server: one retry, nothing else
        if "ERR_NO_BUFFER_SPACE" not in str(e):
            raise
        page.wait_for_timeout(1500)
        page.goto(f"{site_url}/{stem}.html", wait_until="load")
    if getattr(ctx, "_ayin_theme", None):
        assert_theme(page, ctx._ayin_theme)
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


MATCH_JS = """([targets, entries]) => Object.fromEntries(targets.map(t => {
  let el = null; try { el = document.querySelector(t); } catch (e) {}
  return [t, entries.filter(s => { try { return !!el && el.matches(s); } catch (e) { return false; } })];
}))"""


def _entry_selectors() -> list:
    import json
    return sorted({e["selector"] for e in json.loads((ROOT / "tests" / "a11y_review.json").read_text(encoding="utf-8"))["items"]
                   if e["selector"] != "*"})


def run_axe_full(page, width, with_entries=False) -> tuple[list[Violation], list[NeedsReview]]:
    page.set_viewport_size({"width": width, "height": 900})
    res = _axe(page)
    viol = [
        Violation(v["id"], len(v["nodes"]), v.get("impact") or "", tuple(sorted(_selector(n) for n in v["nodes"])))
        for v in res["violations"]
    ]
    entries = _entry_selectors() if with_entries else []
    review = []
    for i in res["incomplete"]:
        sels = tuple(sorted(_selector(n) for n in i["nodes"]))
        matched = page.evaluate(MATCH_JS, [list(sels), entries]) if entries else {}
        review.append(NeedsReview(i["id"], sels, matched))
    return viol, review


def collect_axe(browser, site_url, stem, width, theme="light"):
    """Fresh context/page per (page, width, theme); returns (violations, needs_review)."""
    # Reduced motion renders every assemble item in its settled state. With default motion, items still in
    # their hidden "pre" state are opacity 0 and axe skips them as hidden, leaving real text unchecked.
    ctx = new_context(browser, width, theme=theme, reduced_motion="reduce")
    try:
        page = open_page(ctx, site_url, stem)
        return run_axe_full(page, width, with_entries=True)
    finally:
        ctx.close()


@pytest.fixture(scope="session")
def axe_cache(browser, site_url):
    cache: dict = {}

    def get(stem, width, theme="light"):
        if (stem, width, theme) not in cache:
            cache[(stem, width, theme)] = collect_axe(browser, site_url, stem, width, theme)
        return cache[(stem, width, theme)]

    return get
