"""Motion foundation (T1): assemble, ripples, tilt, drift.

The components are served from an in-memory fixture page (a Playwright route),
so nothing is written to the working tree.
"""
import re

import pytest

from a11y_browser.conftest import new_context
from a11y_browser.motion_fixture import FIXTURE_HTML, FIXTURE_LONG_HTML, FIXTURE_LONG_PATH, FIXTURE_PATH

pytestmark = pytest.mark.browser

STATE_JS = """(sel) => [...document.querySelectorAll(sel)].map(e => {
  const cs = getComputedStyle(e);
  return {cls: String(e.className.baseVal ?? e.className), opacity: cs.opacity, transform: cs.transform};
})"""

# Anything not in its final look (strict=false tolerates the resting translateZ depth): opacity < 1, a non-identity transform, an undrawn stroke.
FINAL_JS = """([strict, scope]) => {
  const ident = (t) => {
    if (t === 'none') return true;
    const m = t.match(/matrix(3d)?\\(([^)]+)\\)/); if (!m) return false;
    const v = m[2].split(',').map(Number);
    const id = m[1] ? [1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1] : [1,0,0,1,0,0];
    return v.every((n, i) => (!strict && m[1] && i === 14) || Math.abs(n - id[i]) < 1e-6);
  };
  const name = (e) => String(e.className.baseVal ?? e.className) || e.tagName;
  const bad = [];
  document.querySelectorAll(`${scope}, ${scope} *`).forEach(e => {
    const cs = getComputedStyle(e);
    if (parseFloat(cs.opacity) < 1) bad.push(['opacity', name(e), cs.opacity]);
    if (!ident(cs.transform)) bad.push(['transform', name(e), cs.transform]);
    if (parseFloat(cs.strokeDashoffset) !== 0 && !isNaN(parseFloat(cs.strokeDashoffset))) bad.push(['dash', name(e), cs.strokeDashoffset]);
  });
  return bad;
}"""


def _open(ctx, site_url, block_site_js=False, init_script=None, long=False):
    page = ctx.new_page()
    path, html = (FIXTURE_LONG_PATH, FIXTURE_LONG_HTML) if long else (FIXTURE_PATH, FIXTURE_HTML)
    page.route(f"**{path}", lambda r: r.fulfill(status=200, content_type="text/html", body=html))
    if block_site_js:
        page.route("**/assets/site.js", lambda r: r.abort())
    if init_script:
        page.add_init_script(init_script)
    page.goto(f"{site_url}{path}", wait_until="load")
    return page


def _settled(page, sel, timeout=8000):
    """Poll until the section has finished assembling (data-assemble-done)."""
    page.wait_for_function(f"document.querySelector('{sel}').hasAttribute('data-assemble-done')", timeout=timeout)


def _scroll_to(page, sel):
    page.evaluate("(s) => document.querySelector(s).scrollIntoView({block: 'center', behavior: 'instant'})", sel)


@pytest.fixture
def rm_page(browser, site_url):
    ctx = new_context(browser, 1280, 800, reduced_motion="reduce")
    yield _open(ctx, site_url)
    ctx.close()


@pytest.fixture
def mo_page(browser, site_url):
    ctx = new_context(browser, 1280, 800, reduced_motion="no-preference")
    yield _open(ctx, site_url)
    ctx.close()


def test_reduced_motion_shows_final_state(rm_page):
    for sel in ("#letters", "#services", "#process"):
        _scroll_to(rm_page, sel)
    rm_page.wait_for_timeout(300)
    assert rm_page.evaluate(FINAL_JS, [True, '.assemble']) == []
    assert rm_page.evaluate("document.getAnimations().length") == 0
    assert rm_page.evaluate("[...document.querySelectorAll('[data-assemble]')].every(e => e.dataset.assemble !== 'pre')")
    assert rm_page.evaluate("document.querySelectorAll('.is-emitting').length") == 0
    assert rm_page.evaluate("[...document.querySelectorAll('.ripples *')].every(e => getComputedStyle(e).opacity === '1')")


def test_content_visible_with_site_js_blocked(browser, site_url):
    """html.js is set but site.js never runs: nothing may be left hidden."""
    ctx = new_context(browser, 1280, 800, reduced_motion="no-preference")
    try:
        page = _open(ctx, site_url, block_site_js=True)
        assert page.evaluate("document.documentElement.classList.contains('js')")
        assert page.evaluate(FINAL_JS, [False, '.assemble']) == []
    finally:
        ctx.close()


def test_content_visible_without_js(browser, site_url):
    ctx = new_context(browser, 1280, 800, reduced_motion="no-preference", java_script_enabled=False)
    try:
        page = _open(ctx, site_url)
        assert page.evaluate("document.documentElement.className") == ""
        assert page.evaluate(FINAL_JS, [False, '.assemble']) == []
    finally:
        ctx.close()


def test_hidden_state_is_js_driven_and_resolves(mo_page):
    # Below the fold the section waits in "pre" with hidden children...
    assert mo_page.evaluate("document.querySelector('#services').dataset.assemble") == "pre"
    assert mo_page.evaluate("getComputedStyle(document.querySelector('#services .asm-card')).opacity") == "0"
    # ...and resolves to the final look once it has entered view.
    _scroll_to(mo_page, "#services")
    _settled(mo_page, "#services")
    assert mo_page.evaluate("document.querySelector('#services').dataset.assemble") == "in"
    assert mo_page.evaluate(FINAL_JS, [False, '#services > .wrap']) == []


def test_tilt_and_parallax_inert_under_reduced_motion(rm_page):
    _scroll_to(rm_page, "#services")
    rm_page.wait_for_timeout(300)
    before = rm_page.evaluate(STATE_JS, ".tilt3d, .ripples, .letters .lt")
    box = rm_page.locator("#services .tilt3d").first.bounding_box()
    rm_page.mouse.move(box["x"] + box["width"] * 0.9, box["y"] + box["height"] * 0.1)
    rm_page.mouse.move(box["x"] + box["width"] * 0.8, box["y"] + box["height"] * 0.2)
    rm_page.mouse.wheel(0, 300)
    rm_page.wait_for_timeout(500)
    assert rm_page.evaluate("document.querySelectorAll('.is-tilting').length") == 0
    assert rm_page.evaluate("[...document.querySelectorAll('.ripples, .tilt3d, .lt')].every(e => e.style.transform === '')")
    # compare computed state of the same elements (scroll moved the page, not the transforms)
    after = rm_page.evaluate(STATE_JS, ".tilt3d, .ripples, .letters .lt")
    assert before == after


def test_tilt_and_drift_work_with_motion(mo_page):
    _scroll_to(mo_page, "#services")
    _settled(mo_page, "#services")
    box = mo_page.locator("#services .tilt3d").first.bounding_box()
    mo_page.mouse.move(box["x"] + box["width"] * 0.85, box["y"] + box["height"] * 0.15)
    mo_page.mouse.move(box["x"] + box["width"] * 0.9, box["y"] + box["height"] * 0.1)
    assert mo_page.evaluate("document.querySelector('#services .tilt3d').style.transform").startswith("rotateY(")
    mo_page.mouse.move(2, 2)
    assert mo_page.evaluate("document.querySelector('#services .tilt3d').style.transform") == ""
    t0 = mo_page.evaluate("document.querySelector('#services .ripples').style.transform")
    mo_page.mouse.wheel(0, 300)
    mo_page.wait_for_timeout(400)
    t1 = mo_page.evaluate("document.querySelector('#services .ripples').style.transform")
    assert t1 and t1 != t0


def test_assemble_runs_once(mo_page):
    mo_page.evaluate(
        """() => { window.__log = [];
          document.querySelectorAll('[data-assemble]').forEach(r => new MutationObserver(() =>
            window.__log.push([r.id, r.getAttribute('data-assemble')])
          ).observe(r, {attributes: true, attributeFilter: ['data-assemble']})); }"""
    )
    _scroll_to(mo_page, "#services")
    _settled(mo_page, "#services")
    assert mo_page.evaluate("document.querySelector('#services').dataset.assemble") == "in"
    assert mo_page.evaluate("document.querySelector('#services').hasAttribute('data-assemble-done')")
    mo_page.evaluate("window.scrollTo(0, 0)")
    mo_page.wait_for_timeout(300)
    _scroll_to(mo_page, "#services")
    mo_page.wait_for_timeout(500)
    log = [e for e in mo_page.evaluate("window.__log") if e[0] == "services"]
    assert log == [["services", "in"]], log
    assert mo_page.evaluate("getComputedStyle(document.querySelector('#services .asm-card')).opacity") == "1"


def test_ripples_emit_then_rest_within_five_seconds(mo_page):
    _scroll_to(mo_page, "#services")
    mo_page.wait_for_function("document.querySelector('#services .ripples.is-emitting')", timeout=3000)
    ripple_anims = "document.getAnimations().filter(a => a.animationName === 'ripple-once').length"
    assert mo_page.evaluate(ripple_anims) > 0
    # the emission itself must be over within 5 s of starting (poll, do not sleep)
    mo_page.wait_for_function(f"{ripple_anims} === 0", timeout=5200)
    # and the class is dropped right after
    mo_page.wait_for_function("!document.querySelector('.ripples.is-emitting')", timeout=3000)
    # at rest the rings are plain static circles
    assert mo_page.evaluate("[...document.querySelectorAll('#services .ripples circle')].every(c => getComputedStyle(c).opacity === '1')")


@pytest.mark.parametrize("reduced", ["reduce", "no-preference"])
def test_no_horizontal_scroll_at_320(browser, site_url, reduced):
    ctx = new_context(browser, 320, 700, reduced_motion=reduced)
    try:
        page = _open(ctx, site_url)
        fits = "document.documentElement.scrollWidth <= document.documentElement.clientWidth"
        assert page.evaluate(fits)
        for sel in ("#letters", "#services", "#process"):
            _scroll_to(page, sel)
            page.wait_for_timeout(300)
            assert page.evaluate(fits), sel
        if reduced == "no-preference":
            _settled(page, "#process")
        assert page.evaluate(fits)
    finally:
        ctx.close()


def test_drift_is_bounded_on_a_long_page(browser, site_url):
    ctx = new_context(browser, 1280, 800, reduced_motion="no-preference")
    try:
        page = _open(ctx, site_url, long=True)
        assert page.evaluate("document.documentElement.scrollHeight") >= 6000
        assert page.evaluate("document.querySelector('#services .ripples').getBoundingClientRect().top + scrollY") > 3500
        sel = "#services .ripples"
        for offset in (0, 300, -400):
            page.evaluate(
                "(o) => { const h = document.querySelector('#services'); window.scrollTo(0, h.offsetTop + h.offsetHeight / 2 - innerHeight / 2 + o); }",
                offset,
            )
            page.wait_for_function(f"document.querySelector('{sel}').style.transform !== ''", timeout=3000)
            page.wait_for_timeout(150)
            m = re.match(
                r"translate3d\(0(?:px)?, (-?[\d.]+)px, 0(?:px)?\) rotate\((-?[\d.]+)deg\)",
                page.evaluate(f"document.querySelector('{sel}').style.transform"),
            )
            assert m, "no drift transform"
            ty, rot = float(m.group(1)), float(m.group(2))
            assert abs(ty) <= 120 and abs(rot) <= 6, (offset, ty, rot)
            hit = page.evaluate(
                """() => { const r = document.querySelector('#services .ripples').getBoundingClientRect();
                  const h = document.querySelector('#services').getBoundingClientRect();
                  return r.top < h.bottom && r.bottom > h.top && r.left < h.right && r.right > h.left; }"""
            )
            assert hit, "ripple left its host"
    finally:
        ctx.close()


NOOP_IO = "window.IntersectionObserver = class { constructor() {} observe() {} unobserve() {} disconnect() {} takeRecords() { return []; } };"


def test_sections_still_assemble_when_the_observer_never_fires(browser, site_url):
    ctx = new_context(browser, 1280, 800, reduced_motion="no-preference")
    try:
        page = _open(ctx, site_url, init_script=NOOP_IO)
        assert page.evaluate("document.querySelector('#letters').dataset.assemble") == "pre"
        _scroll_to(page, "#letters")
        page.wait_for_function("document.querySelector('#letters').dataset.assemble === 'in'", timeout=3000)
        _settled(page, "#letters")
        assert page.evaluate(FINAL_JS, [False, "#letters"]) == []
        _scroll_to(page, "#services")
        _settled(page, "#services")
        assert page.evaluate(FINAL_JS, [False, "#services > .wrap"]) == []
    finally:
        ctx.close()


def test_anchor_jump_past_sections_leaves_nothing_hidden(mo_page):
    mo_page.evaluate("location.hash = '#process'")
    mo_page.wait_for_function("document.querySelector('#process').dataset.assemble === 'in'", timeout=3000)
    _settled(mo_page, "#process")
    assert mo_page.evaluate(FINAL_JS, [False, "#process > .wrap"]) == []
    # sections jumped over are revealed as soon as they are scrolled to
    for sel, scope in (("#services", "#services > .wrap"), ("#letters", "#letters")):
        _scroll_to(mo_page, sel)
        _settled(mo_page, sel)
        assert mo_page.evaluate(FINAL_JS, [False, scope]) == []


def test_settled_icons_are_solid_strokes(mo_page):
    _scroll_to(mo_page, "#services")
    _settled(mo_page, "#services")
    dashes = mo_page.evaluate(
        "[...document.querySelectorAll('.iris-ico :is(circle, path)')].map(e => getComputedStyle(e).strokeDasharray)"
    )
    assert dashes and all(d == "none" for d in dashes), dashes


# ---------------------------------------------------------------- Home placement (T2)

def _home(browser, site_url, **kw):
    ctx = new_context(browser, kw.pop("width", 1280), kw.pop("height", 800), **kw)
    page = ctx.new_page()
    page.goto(f"{site_url}/index.html", wait_until="load")
    return ctx, page


def test_letters_band_has_text_label(browser, site_url):
    """Font failure must not hide the meaning: the group carries it as text, the glyphs are decorative."""
    ctx, page = _home(browser, site_url)
    try:
        group = page.locator(".letters [role='img']")
        assert group.count() == 1
        label = group.get_attribute("aria-label")
        assert re.search(r"\bayin\b", label, re.I) and re.search(r"\bthe eye\b", label, re.I), label
        glyphs = page.locator(".letters .glyph")
        assert glyphs.count() == 4
        assert [glyphs.nth(i).inner_text() for i in range(4)] == ["ع", "ע", "𐤏", "O"]
        assert all(glyphs.nth(i).get_attribute("aria-hidden") == "true" for i in range(4))
        # separators are non-text shapes and decorative
        seps = page.locator(".letters .lt-sep")
        assert seps.count() == 3
        assert all(seps.nth(i).get_attribute("aria-hidden") == "true" and seps.nth(i).inner_text() == "" for i in range(3))
    finally:
        ctx.close()


def test_marquee_is_replaced(browser, site_url):
    ctx, page = _home(browser, site_url)
    try:
        assert page.locator(".marquee, .marquee-track, .marquee-item").count() == 0
        first_band = page.evaluate(
            "document.querySelector('main#main').firstElementChild.className"
        )
        assert "letters" in first_band and "surface-alt" in first_band, first_band
        # Home still carries the services/process placements
        assert page.locator("#services.has-ripples .ripples-top, #process.has-ripples .ripples-top-l").count() == 2
        assert page.locator("#services .iris-ico").count() == 4
        assert page.locator(".svc-num").count() == 0 and page.locator(".sec-index").count() == 2
        assert page.locator("#services .iris-mark, #process .iris-mark").count() == 2
        assert page.locator("#process .step-iris").count() == 4
    finally:
        ctx.close()


# Animations that existed before Phase 2b and are owned by Phase 3, named explicitly:
#  - scrolldot: the hero scroll-hint dot (infinite, `.scroll-hint .bar::after`)
#  - nodePulse: the Why-section globe destination pulse (infinite, `.why-grid.in .node-pulse`); it starts
#    when the Why band, which sits directly under the process band, scrolls into view
#  - drawArc: the same globe's flight arcs (finite, 2.4 s plus up to 1 s delay, same trigger); it can still be
#    mid-run 6 s after the bands entered view when the Why band is revealed later than them
# The hero iris is a canvas driven by requestAnimationFrame, so it never appears in getAnimations().
PRE_EXISTING_RUNNING = {"scrolldot", "nodePulse", "drawArc"}


def test_no_long_running_animation_after_load(browser, site_url):
    ctx, page = _home(browser, site_url, reduced_motion="no-preference")
    try:
        for sel in ("#letters", "#services", "#process"):
            page.evaluate("(s) => document.querySelector(s).scrollIntoView({block: 'center', behavior: 'instant'})", sel)
            page.wait_for_function(f"document.querySelector('{sel}').dataset.assemble === 'in'", timeout=3000)
        page.wait_for_timeout(6000)
        running = page.evaluate(
            """() => document.getAnimations().filter(a => a.playState === 'running').map(a => ({
              name: a.animationName || a.transitionProperty || a.constructor.name,
              kind: a.constructor.name,
              target: a.effect && a.effect.target ? (a.effect.target.className.baseVal ?? a.effect.target.className) : ''}))"""
        )
        extra = [a for a in running if a["name"] not in PRE_EXISTING_RUNNING]
        assert extra == [], f"still running 6 s after the bands entered view: {extra}"
        # nothing at all runs inside the three bands this plan owns
        inside = page.evaluate(
            """() => document.getAnimations().filter(a => a.playState === 'running' && a.effect && a.effect.target
              && a.effect.target.closest('#letters, #services, #process')).length"""
        )
        assert inside == 0
        assert page.evaluate("document.querySelectorAll('.is-emitting').length") == 0
    finally:
        ctx.close()


def test_home_no_horizontal_scroll_at_320_after_assemble(browser, site_url):
    ctx, page = _home(browser, site_url, width=320, height=700, reduced_motion="no-preference")
    try:
        for sel in ("#letters", "#services", "#process"):
            page.evaluate("(s) => document.querySelector(s).scrollIntoView({block: 'center', behavior: 'instant'})", sel)
            page.wait_for_timeout(300)
            sw, cw = page.evaluate("[document.documentElement.scrollWidth, document.documentElement.clientWidth]")
            assert sw <= cw, f"{sel}: page scrolls horizontally mid-assemble ({sw} > {cw})"
        page.wait_for_timeout(3600)
        sw, cw = page.evaluate("[document.documentElement.scrollWidth, document.documentElement.clientWidth]")
        assert sw <= cw
    finally:
        ctx.close()


# ---------------------------------------------------------------- Home fix round 1

def _centre(page, sel):
    """Scroll a band to the middle of the viewport, plus one wheel tick so the ripple drift recomputes
    (drift only updates on scroll events, so after an instant jump it can lag until the next one)."""
    page.evaluate("(s) => document.querySelector(s).scrollIntoView({block: 'center', behavior: 'instant'})", sel)
    page.mouse.wheel(0, 1)
    page.wait_for_timeout(400)


def _settle_home(page):
    for sel in ("#letters", "#services", "#process"):
        page.evaluate("(s) => document.querySelector(s).scrollIntoView({block: 'center', behavior: 'instant'})", sel)
        page.wait_for_function(f"document.querySelector('{sel}').hasAttribute('data-assemble-done')", timeout=8000)
    page.mouse.move(2, 2)
    page.wait_for_timeout(700)


@pytest.mark.parametrize("width", (1280, 768))
def test_home_depth_does_not_displace_anything_at_rest(browser, site_url, width):
    """Settled and no pointer: icon and title share a left edge, glyph and caption a centre (within 2px)."""
    ctx, page = _home(browser, site_url, width=width, reduced_motion="no-preference")
    try:
        _settle_home(page)
        res = page.evaluate(
            """() => ({
              cards: [...document.querySelectorAll('#services .svc')].map(c => [
                c.querySelector('.iris-ico').getBoundingClientRect().left,
                c.querySelector('h3').getBoundingClientRect().left]),
              glyphs: [...document.querySelectorAll('.letters .lt')].map(l => {
                const mid = (e) => { const r = e.getBoundingClientRect(); return r.left + r.width / 2; };
                // glyph centre from its text range, so the glyph itself (not its box) is measured
                const g = l.querySelector('.glyph'), rg = document.createRange(); rg.selectNodeContents(g);
                const b = rg.getBoundingClientRect();
                return [b.left + b.width / 2, mid(l.querySelector('.cap'))];
              })})"""
        )
        assert len(res["cards"]) == 4 and len(res["glyphs"]) == 4
        for icon, title in res["cards"]:
            assert abs(icon - title) <= 2, f"icon left {icon} vs title left {title}"
        for glyph, cap in res["glyphs"]:
            assert abs(glyph - cap) <= 2, f"glyph centre {glyph} vs caption centre {cap}"
    finally:
        ctx.close()


def test_home_depth_appears_while_tilting(browser, site_url):
    ctx, page = _home(browser, site_url, reduced_motion="no-preference")
    try:
        _settle_home(page)
        _centre(page, "#services")
        z = "(sel) => new DOMMatrix(getComputedStyle(document.querySelector(sel)).transform).m43"
        assert page.evaluate(z, "#services .svc .iris-ico") == 0
        box = page.locator("#services .svc").first.bounding_box()
        page.mouse.move(box["x"] + box["width"] * 0.7, box["y"] + box["height"] * 0.3)
        page.mouse.move(box["x"] + box["width"] * 0.75, box["y"] + box["height"] * 0.35)
        page.wait_for_timeout(700)
        assert page.evaluate(z, "#services .svc .iris-ico") > 20
        page.mouse.move(2, 2)
        _centre(page, "#letters")
        lb = page.locator(".letters").bounding_box()
        page.mouse.move(lb["x"] + lb["width"] * 0.4, lb["y"] + lb["height"] * 0.5)
        page.mouse.move(lb["x"] + lb["width"] * 0.45, lb["y"] + lb["height"] * 0.5)
        page.wait_for_timeout(700)
        assert page.evaluate(z, ".letters .glyph") > 20
        page.mouse.move(2, 2)
        page.wait_for_timeout(700)
        assert page.evaluate(z, ".letters .glyph") == 0
    finally:
        ctx.close()


@pytest.mark.parametrize("width", (1280, 375))
def test_ripple_centre_and_inner_rings_are_clear_of_text(browser, site_url, width):
    ctx, page = _home(browser, site_url, width=width, height=800, reduced_motion="no-preference")
    try:
        _settle_home(page)
        for sec in ("#services", "#process"):
            _centre(page, sec)
            hit = page.evaluate(
                """(sec) => {
                  const s = document.querySelector(sec), d = s.querySelector('.ripples .drop').getBoundingClientRect();
                  const cx = d.left + d.width / 2, cy = d.top + d.height / 2;
                  const svg = s.querySelector('.ripples').getBoundingClientRect();
                  const inner = s.querySelectorAll('.ripples circle')[1].getBoundingClientRect().width / 2;   // centre dot plus the first two rings
                  const hits = [];
                  s.querySelectorAll('.sec-head .eyebrow, .sec-head h2, .sec-head p').forEach(e => {
                    const r = document.createRange(); r.selectNodeContents(e);
                    for (const b of r.getClientRects()) {
                      const nx = Math.max(b.left, Math.min(cx, b.right)), ny = Math.max(b.top, Math.min(cy, b.bottom));
                      if (Math.hypot(nx - cx, ny - cy) < inner) hits.push([e.tagName, Math.round(Math.hypot(nx - cx, ny - cy))]);
                    }
                  });
                  return hits;
                }""", sec)
            assert hit == [], f"{sec}@{width}: ripple centre/inner rings run under text {hit}"
    finally:
        ctx.close()
