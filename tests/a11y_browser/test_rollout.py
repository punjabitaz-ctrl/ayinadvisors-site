"""Phase 2b rollout (T3): accents and motion on About, Services, Projects, BizCheck and Contact.

Every placement gets the checks the Home placement needed: nothing displaced at rest, depth only while the
pointer tilts, ripple centres in empty space, no sideways scroll while assembling, final state under reduced motion.
"""
import pytest

from a11y_browser.conftest import new_context
from a11y_browser.test_motion import FINAL_JS, _centre

pytestmark = pytest.mark.browser

ROLLOUT = ("About", "Services", "Projects", "BizCheck")


def _page(browser, site_url, stem, width=1280, height=800, **kw):
    ctx = new_context(browser, width, height, **kw)
    page = ctx.new_page()
    page.goto(f"{site_url}/{stem}.html", wait_until="load")
    return ctx, page


def _settle_all(page):
    """Bring every assemble root into view, wait until it is done, park the pointer away."""
    n = page.evaluate("document.querySelectorAll('[data-assemble]').length")
    for i in range(n):
        page.evaluate(
            "(i) => document.querySelectorAll('[data-assemble]')[i].scrollIntoView({block: 'center', behavior: 'instant'})", i)
        page.wait_for_function(
            f"document.querySelectorAll('[data-assemble]')[{i}].hasAttribute('data-assemble-done')", timeout=9000)
    page.mouse.move(2, 2)
    page.wait_for_timeout(700)


@pytest.mark.parametrize("stem", ROLLOUT + ("Contact",))
def test_rollout_no_horizontal_scroll_at_320_while_assembling(browser, site_url, stem):
    ctx, page = _page(browser, site_url, stem, width=320, height=700, reduced_motion="no-preference")
    try:
        total = page.evaluate("document.documentElement.scrollHeight")
        y = 0
        while y < total:
            page.evaluate("(y) => window.scrollTo(0, y)", y)
            page.wait_for_timeout(250)
            sw, cw = page.evaluate("[document.documentElement.scrollWidth, document.documentElement.clientWidth]")
            assert sw <= cw, f"{stem} at y={y}: horizontal scroll {sw} > {cw}"
            y += 500
        page.wait_for_timeout(3600)
        sw, cw = page.evaluate("[document.documentElement.scrollWidth, document.documentElement.clientWidth]")
        assert sw <= cw
    finally:
        ctx.close()


@pytest.mark.parametrize("stem", ROLLOUT)
def test_rollout_reduced_motion_shows_final_state(browser, site_url, stem):
    ctx, page = _page(browser, site_url, stem, reduced_motion="reduce")
    try:
        page.wait_for_timeout(500)
        bad = page.evaluate(FINAL_JS, [True, "main"])
        # two pre-existing static decorations carry a fixed design opacity (the About eye ring, the CTA glow); they never animate
        bad = [b for b in bad if not (b[0] == "opacity" and b[1] in ("ring", "cta-glow"))]
        assert bad == [], bad
        assert page.evaluate("document.querySelectorAll('.is-emitting, .is-tilting').length") == 0
        assert page.evaluate("document.querySelectorAll('[data-assemble=\"pre\"]').length") == 0
    finally:
        ctx.close()


@pytest.mark.parametrize("width", (1280, 768))
def test_rollout_depth_does_not_displace_anything_at_rest(browser, site_url, width):
    """Settled, pointer away: no resting transform on any card or its contents, and the number/title edges align."""
    checks = {
        "Services": ("article.svc-detail .deliverables li", None, None),
        "Projects": (".project-card", ".project-index", "h2"),
        "BizCheck": (".bc-step", ".n", ".h3"),
    }
    for stem, (card, a, b) in checks.items():
        ctx, page = _page(browser, site_url, stem, width=width, reduced_motion="no-preference")
        try:
            _settle_all(page)
            res = page.evaluate(
                """([card, a, b]) => [...document.querySelectorAll(card)].map(c => {
                  const t = (e) => getComputedStyle(e).transform;
                  const nodes = [c, ...c.querySelectorAll('*')];
                  return {tr: nodes.map(t).filter(v => v !== 'none'), tilting: c.classList.contains('is-tilting'),
                          dl: (a && b) ? c.querySelector(a).getBoundingClientRect().left - c.querySelector(b).getBoundingClientRect().left : 0};
                })""", [card, a, b])
            assert res, stem
            for r in res:
                assert r["tr"] == [] and not r["tilting"], f"{stem}@{width}: resting transform {r['tr']}"
                assert abs(r["dl"]) <= 2, f"{stem}@{width}: number left edge vs title left edge {r['dl']}"
        finally:
            ctx.close()


def test_rollout_depth_appears_while_tilting(browser, site_url):
    for stem, card, inner in (("Projects", ".project-card.navy-card", "h2"), ("BizCheck", ".bc-step", ".h3")):
        ctx, page = _page(browser, site_url, stem, reduced_motion="no-preference")
        try:
            _settle_all(page)
            page.evaluate("(s) => document.querySelector(s).scrollIntoView({block: 'center', behavior: 'instant'})", card)
            page.wait_for_timeout(300)
            z = "([c, i]) => new DOMMatrix(getComputedStyle(document.querySelector(c + ' ' + i)).transform).m43"
            assert page.evaluate(z, [card, inner]) == 0
            box = page.locator(card).first.bounding_box()
            page.mouse.move(box["x"] + box["width"] * 0.7, box["y"] + box["height"] * 0.3)
            page.mouse.move(box["x"] + box["width"] * 0.75, box["y"] + box["height"] * 0.35)
            page.wait_for_timeout(700)
            assert page.evaluate(z, [card, inner]) > 10, stem
            page.mouse.move(2, 2)
            page.wait_for_timeout(700)
            assert page.evaluate(z, [card, inner]) == 0
        finally:
            ctx.close()


def test_services_cells_tilt_and_return(browser, site_url):
    ctx, page = _page(browser, site_url, "Services", reduced_motion="no-preference")
    try:
        _settle_all(page)
        sel = "#research .deliverables li"
        page.evaluate("(s) => document.querySelector(s).scrollIntoView({block: 'center', behavior: 'instant'})", sel)
        page.wait_for_timeout(300)
        box = page.locator(sel).nth(1).bounding_box()
        page.mouse.move(box["x"] + box["width"] * 0.8, box["y"] + box["height"] * 0.3)
        page.mouse.move(box["x"] + box["width"] * 0.85, box["y"] + box["height"] * 0.35)
        page.wait_for_timeout(500)
        tr = "(s) => getComputedStyle(document.querySelectorAll(s)[1]).transform"
        assert page.evaluate(tr, sel) != "none"
        page.mouse.move(2, 2)
        page.wait_for_timeout(700)
        assert page.evaluate(tr, sel) == "none"
    finally:
        ctx.close()


@pytest.mark.parametrize("width", (1280, 768, 375))
def test_rollout_ripple_centre_and_inner_rings_are_clear_of_text(browser, site_url, width):
    seen = 0
    for stem in ROLLOUT:
        ctx, page = _page(browser, site_url, stem, width=width, height=800, reduced_motion="no-preference")
        try:
            if page.locator(".ripples").count() == 0:
                continue
            seen += 1
            _settle_all(page)
            _centre(page, ".has-ripples")
            hit = page.evaluate(
                """() => {
                  const s = document.querySelector('.has-ripples'), svg = s.querySelector('.ripples');
                  const d = svg.querySelector('.drop').getBoundingClientRect();
                  const cx = d.left + d.width / 2, cy = d.top + d.height / 2;
                  const inner = 78 * svg.getBoundingClientRect().width / 400;   // centre dot plus the first two rings
                  const hits = [], w = document.createTreeWalker(s, NodeFilter.SHOW_TEXT);
                  for (let n = w.nextNode(); n; n = w.nextNode()) {
                    if (!n.textContent.trim() || n.parentElement.closest('svg')) continue;
                    const r = document.createRange(); r.selectNodeContents(n);
                    for (const b of r.getClientRects()) {
                      const nx = Math.max(b.left, Math.min(cx, b.right)), ny = Math.max(b.top, Math.min(cy, b.bottom));
                      const dist = Math.hypot(nx - cx, ny - cy);
                      if (dist < inner) hits.push([n.parentElement.tagName, n.textContent.trim().slice(0, 24), Math.round(dist)]);
                    }
                  }
                  return hits;
                }""")
            assert hit == [], f"{stem}@{width}: ripple centre/inner rings run under text {hit}"
        finally:
            ctx.close()
    assert seen >= 3


def test_rollout_no_long_running_animation(browser, site_url):
    """Six seconds after every assemble root and ripple host has been seen, nothing of ours still runs.

    Excluded by name: the pulse on the "In Testing" status dot on Projects (pre-existing infinite loop, owned by Phase 3)."""
    for stem in ROLLOUT:
        ctx, page = _page(browser, site_url, stem, reduced_motion="no-preference")
        try:
            _settle_all(page)
            if page.locator(".has-ripples").count():
                _centre(page, ".has-ripples")
            page.wait_for_timeout(6000)
            running = page.evaluate(
                """() => document.getAnimations().filter(a => a.playState === 'running'
                  && a.effect && a.effect.target && a.effect.target.closest && a.effect.target.closest('.assemble, .has-ripples')
                  && !a.effect.target.closest('.badge-testing'))
                  .map(a => a.animationName || a.transitionProperty || a.constructor.name)""")
            assert running == [], f"{stem}: still running 6 s after the placements were seen: {running}"
            assert page.evaluate("document.querySelectorAll('.is-emitting').length") == 0
        finally:
            ctx.close()
