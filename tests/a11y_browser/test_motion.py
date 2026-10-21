"""Motion foundation (T1): assemble, ripples, tilt, drift.

The components are served from an in-memory fixture page (a Playwright route),
so nothing is written to the working tree.
"""
import pytest

from a11y_browser.conftest import new_context
from a11y_browser.motion_fixture import FIXTURE_HTML, FIXTURE_PATH

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


def _open(ctx, site_url, block_site_js=False):
    page = ctx.new_page()
    page.route(
        f"**{FIXTURE_PATH}",
        lambda r: r.fulfill(status=200, content_type="text/html", body=FIXTURE_HTML),
    )
    if block_site_js:
        page.route("**/assets/site.js", lambda r: r.abort())
    page.goto(f"{site_url}{FIXTURE_PATH}", wait_until="load")
    return page


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
    mo_page.wait_for_timeout(3800)
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
    mo_page.wait_for_timeout(3800)  # assembly finished
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
    mo_page.wait_for_timeout(3800)
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
    mo_page.wait_for_timeout(600)
    assert mo_page.evaluate("document.querySelectorAll('#services .ripples.is-emitting').length") == 1
    assert mo_page.evaluate("document.getAnimations().filter(a => a.animationName === 'ripple-once').length") > 0
    mo_page.wait_for_timeout(5500)
    assert mo_page.evaluate("document.getAnimations().filter(a => a.animationName === 'ripple-once').length") == 0
    assert mo_page.evaluate("document.querySelectorAll('.ripples.is-emitting').length") == 0
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
            page.wait_for_timeout(600)
            assert page.evaluate(fits), sel
        page.wait_for_timeout(3500)
        assert page.evaluate(fits)
    finally:
        ctx.close()
