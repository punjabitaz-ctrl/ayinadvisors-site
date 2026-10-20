"""Keyboard, focus, reflow and reduced-motion behaviour, checked in real Chromium."""
import pytest

from a11y_browser.conftest import PAGES, new_context, open_page

pytestmark = pytest.mark.browser

ACTIVE_INFO_JS = """() => {
  const e = document.activeElement;
  if (!e || e === document.body || e === document.documentElement) return null;
  const r = e.getBoundingClientRect();
  const cs = getComputedStyle(e);
  const nav = document.querySelector('.nav');
  const n = nav ? nav.getBoundingClientRect() : null;
  return {
    tag: e.tagName, href: e.getAttribute('href'), text: (e.textContent || '').trim().slice(0, 40),
    outlineWidth: parseFloat(cs.outlineWidth), outlineStyle: cs.outlineStyle,
    rect: {top: r.top, bottom: r.bottom, left: r.left, right: r.right},
    inNav: !!(nav && nav.contains(e)),
    nav: n && {top: n.top, bottom: n.bottom},
    key: e.tagName + '|' + (e.getAttribute('href') || '') + '|' + Math.round(r.top + scrollY) + '|' + Math.round(r.left),
  };
}"""


@pytest.fixture
def home(browser, site_url):
    ctx = new_context(browser, 1280, 720)
    page = open_page(ctx, site_url, "index")
    yield page
    ctx.close()


def _walk_tab(page, key="Tab", limit=120):
    """Press `key` repeatedly, collecting info for each distinct focused control until focus leaves/wraps."""
    seen, out = set(), []
    for _ in range(limit):
        page.keyboard.press(key)
        info = page.evaluate(ACTIVE_INFO_JS)
        if info is None or info["key"] in seen:
            break
        seen.add(info["key"])
        out.append(info)
    return out


def test_tab_order_reaches_main_content(home):
    """First Tab lands on a skip link; activating it puts keyboard focus in <main>."""
    home.keyboard.press("Tab")
    first = home.evaluate(ACTIVE_INFO_JS)
    assert first and first["tag"] == "A" and (first["href"] or "").startswith("#"), (
        f"first focusable control is not a skip link: {first and (first['tag'], first['text'])}"
    )
    target_is_main = home.evaluate(
        "(h) => { const t = document.getElementById(h.slice(1)); "
        "return !!t && (t.tagName === 'MAIN' || t.getAttribute('role') === 'main'); }",
        first["href"],
    )
    assert target_is_main, "skip link does not point at the main landmark"
    home.keyboard.press("Enter")
    home.keyboard.press("Tab")
    in_main = home.evaluate(
        "() => { const m = document.querySelector('main,[role=main]'); "
        "return !!m && m.contains(document.activeElement); }"
    )
    assert in_main, "after the skip link, the next Tab does not land inside <main>"


def test_focus_outline_is_visible(home):
    """Every keyboard-focusable control on Home shows an outline of at least 2px."""
    controls = _walk_tab(home)
    assert len(controls) > 5, "tab walk found too few controls; the test is not exercising the page"
    bad = [
        (c["tag"], c["text"], c["outlineStyle"], c["outlineWidth"])
        for c in controls
        if c["outlineStyle"] in ("none", "hidden") or c["outlineWidth"] < 2
    ]
    assert not bad, f"controls without a >=2px focus outline: {bad}"


OBSCURED_JS = """() => {
  const root = document.documentElement;
  root.style.scrollBehavior = 'auto';
  const sel = 'a[href], button, input:not([type=hidden]), select, textarea, summary, [tabindex]:not([tabindex="-1"])';
  const nav = document.querySelector('.nav');
  const bad = [];
  let tested = 0;
  for (const el of document.querySelectorAll(sel)) {
    if (el.closest('.nav') || el.closest('.mobile-drawer') || !el.getClientRects().length) continue;
    const absTop = el.getBoundingClientRect().top + scrollY;
    if (absTop < nav.getBoundingClientRect().height + 40) continue;   // cannot be scrolled under the nav
    // Put the control just under the top edge (as when tabbing backwards through content
    // that is already on screen), then focus it and see where the browser leaves it.
    scrollTo(0, absTop - 20);
    el.focus();
    tested++;
    const r = el.getBoundingClientRect(), n = nav.getBoundingClientRect();
    if (r.top < n.bottom && r.bottom > n.top) {
      bad.push([el.tagName, (el.textContent || '').trim().slice(0, 30), Math.round(r.top), Math.round(n.bottom)]);
    }
  }
  return {tested, bad};
}"""


def test_focus_is_not_obscured_by_the_sticky_nav(home):
    """A control that takes focus near the top edge must not stay hidden behind the fixed nav."""
    res = home.evaluate(OBSCURED_JS)
    assert res["tested"] > 5, "found too few controls; the test is not exercising the page"
    assert not res["bad"], f"focused controls hidden behind the sticky nav (tag, text, top, nav bottom): {res['bad']}"


@pytest.mark.parametrize("stem", [
    pytest.param(s, marks=pytest.mark.xfail(strict=True, raises=AssertionError, reason="fixed in Task 7")) if s == "index" else s
    for s in PAGES
])
def test_no_horizontal_scroll_at_320(browser, site_url, stem):
    ctx = new_context(browser, 320, 800)
    try:
        page = open_page(ctx, site_url, stem)
        sw, cw = page.evaluate("[document.documentElement.scrollWidth, document.documentElement.clientWidth]")
        assert sw <= cw, f"{stem}: page scrolls horizontally at 320px (scrollWidth {sw} > clientWidth {cw})"
    finally:
        ctx.close()


def test_reduced_motion_disables_animation(browser, site_url):
    """With prefers-reduced-motion: reduce no CSS animation runs and the iris canvas stays still."""
    problems = []
    for stem in PAGES:
        ctx = new_context(browser, 1280, 900, reduced_motion="reduce")
        try:
            page = open_page(ctx, site_url, stem)
            page.wait_for_timeout(400)
            running = page.evaluate(
                "document.getAnimations().filter(a => a instanceof CSSAnimation && a.playState === 'running')"
                ".map(a => a.animationName)"
            )
            if running:
                problems.append((stem, "css-animation", sorted(set(running))))
            if page.query_selector("#iris"):
                snap = "() => document.getElementById('iris').toDataURL()"
                a = page.evaluate(snap)
                page.wait_for_timeout(700)
                if page.evaluate(snap) != a:
                    problems.append((stem, "iris-canvas-still-animating", None))
        finally:
            ctx.close()
    assert not problems, f"motion not disabled under prefers-reduced-motion: {problems}"
