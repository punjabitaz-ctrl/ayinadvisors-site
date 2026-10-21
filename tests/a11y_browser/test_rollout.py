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
                assert stem in ("Services", "Projects"), f"{stem} lost its ripples"
                continue
            seen += 1
            _settle_all(page)
            _centre(page, ".has-ripples")
            hit = page.evaluate(
                """() => {
                  const s = document.querySelector('.has-ripples'), svg = s.querySelector('.ripples');
                  const d = svg.querySelector('.drop').getBoundingClientRect();
                  const cx = d.left + d.width / 2, cy = d.top + d.height / 2;
                  const inner = svg.querySelectorAll('circle')[1].getBoundingClientRect().width / 2;   // centre dot plus the first two rings
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
    assert seen == 2   # About and BizCheck; Services and Projects carry no ripples


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


@pytest.mark.parametrize("width", (1280, 768, 375))
def test_ripples_box_stays_inside_its_own_section(browser, site_url, width):
    """The SVG box must not reach into neighbouring sections (axe reads geometry, not the clip)."""
    for stem in ("About", "BizCheck"):
        ctx, page = _page(browser, site_url, stem, width=width, height=800, reduced_motion="no-preference")
        try:
            r = page.evaluate(
                """() => { const s = document.querySelector('.has-ripples'), v = s.querySelector('.ripples');
                  const a = s.getBoundingClientRect(), b = v.getBoundingClientRect();
                  return {top: b.top - a.top, bottom: a.bottom - b.bottom}; }""")
            assert r["top"] >= -1 and r["bottom"] >= -1, f"{stem}@{width}: ripples box leaves its section {r}"
        finally:
            ctx.close()


GRIDS = {
    "Projects": ".project-card",
    "BizCheck": ".bc-step",
    "Services": "article.svc-detail .deliverables li",
}


@pytest.mark.parametrize("width", (1280, 768))
def test_grid_lines_are_continuous(browser, site_url, width):
    """Every card/cell keeps its right and bottom border as a visible line (rendered pixels, motion on, settled)."""
    import io
    from PIL import Image
    for stem, sel in GRIDS.items():
        ctx, page = _page(browser, site_url, stem, width=width, height=900, reduced_motion="no-preference")
        try:
            _settle_all(page)
            page.evaluate("window.scrollTo(0, 0)")
            page.wait_for_timeout(300)
            info = page.evaluate(
                """(sel) => [...document.querySelectorAll(sel)].map(c => { const r = c.getBoundingClientRect(), s = getComputedStyle(c);
                  return {l: r.left, r: r.right, t: r.top + scrollY, b: r.bottom + scrollY, br: s.borderRightWidth, bb: s.borderBottomWidth}; })""", sel)
            assert info, stem
            for c in info:
                assert c["br"] == "1px" and c["bb"] == "1px", (stem, c)
            # the outer right edge is shared exactly by every card that reaches it (no card sits 1px inside)
            maxr = max(c["r"] for c in info)
            for c in info:
                assert abs(c["r"] - maxr) < 0.5 or c["r"] < maxr - 50, (stem, width, c["r"], maxr)
            full = Image.open(io.BytesIO(page.screenshot(full_page=True))).convert("RGB")
            def lum(px): return sum(px)
            missing = []
            for i, c in enumerate(info):
                xm, ym = int((c["l"] + c["r"]) / 2), int((c["t"] + c["b"]) / 2)
                inside = lum(full.getpixel((xm, ym)))
                # bottom line: some row within 2px of the bottom edge differs from the card face
                rows = [int(c["b"]) + d for d in (-3, -2, -1, 0)]
                if not any(abs(lum(full.getpixel((xm, y))) - inside) > 12 for y in rows if 0 <= y < full.height):
                    missing.append((i, "bottom"))
                cols = [int(c["r"]) + d for d in (-3, -2, -1, 0)]
                if not any(abs(lum(full.getpixel((x, ym))) - inside) > 12 for x in cols if 0 <= x < full.width):
                    missing.append((i, "right"))
            assert missing == [], f"{stem}@{width}: grid lines missing at {missing}"
        finally:
            ctx.close()
