"""Phase 2d in a real browser: the WebGL hero iris, its fallbacks, Lenis smooth scroll, and the accessibility gate with
the canvas present.

Chromium is launched with software WebGL (SwiftShader) so the 3D path can run on a machine without a GPU. If the
harness still has no WebGL the 3D tests skip with that reason; the fallback and Lenis tests do not need it.
"""
import pytest

from a11y_browser.conftest import INSTALL_HINT, THEMES, new_context, open_page, run_axe
from a11y_browser.pixel_contrast import measure

pytestmark = pytest.mark.browser

GL_ARGS = ["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"]

# count every requestAnimationFrame callback that actually runs
RAF_COUNTER = """(() => { window.__raf = 0; const r = window.requestAnimationFrame.bind(window);
  window.requestAnimationFrame = (cb) => r((t) => { window.__raf++; cb(t); }); })();"""
NO_WEBGL = """(() => { const g = HTMLCanvasElement.prototype.getContext;
  HTMLCanvasElement.prototype.getContext = function (t, ...a) { return /webgl/i.test(String(t)) ? null : g.call(this, t, ...a); }; })();"""
# throws inside the 3D start-up only (the stack names hero3d.js), so the 2D hero and site.js are untouched
THROW_IN_3D = """(() => { const RO = window.ResizeObserver;
  window.ResizeObserver = class extends RO { constructor(cb) { if (new Error().stack.includes('hero3d.js')) throw new Error('injected 3D failure'); super(cb); } }; })();"""

SNAP = "() => window.__ayinHero3d && window.__ayinHero3d.snapshot()"
HERO_STATE = """() => ({ iris: document.querySelector('.hero').dataset.iris || null,
  canvas3d: !!document.getElementById('iris3d'), engine: document.getElementById('iris').dataset.engine || null })"""


@pytest.fixture(scope="module")
def gl_browser():
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        pytest.skip(f"playwright is not installed; {INSTALL_HINT}")
    pw = sync_playwright().start()
    try:
        try:
            b = pw.chromium.launch(args=GL_ARGS)
        except Exception as e:
            pytest.skip(f"Chromium unavailable ({type(e).__name__}); {INSTALL_HINT}")
        yield b
        b.close()
    finally:
        pw.stop()


@pytest.fixture(scope="module")
def webgl_ok(gl_browser):
    page = gl_browser.new_page()
    try:
        return bool(page.evaluate("!!document.createElement('canvas').getContext('webgl2')"))
    finally:
        page.close()


def _open(browser, site_url, width=1280, height=900, theme="light", init=(), stem="index", **kw):
    ctx = new_context(browser, width, height, theme=theme, **kw)
    for s in init:
        ctx.add_init_script(s)
    page = ctx.new_page()
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.goto(f"{site_url}/{stem}.html", wait_until="load")
    page._errors = errors
    return ctx, page


def _wait_3d(page):
    page.wait_for_function("document.querySelector('.hero').dataset.iris === 'webgl'", timeout=8000)
    page.wait_for_function("document.getElementById('iris3d') && document.getElementById('iris3d').hasAttribute('data-ready')")
    page.wait_for_timeout(2300)   # entrance (1.8 s) done


def _need_gl(webgl_ok):
    if not webgl_ok:
        pytest.skip("this Chromium has no WebGL even with SwiftShader; the 3D tests need it")


# ---------------------------------------------------------------- (a) 3D active, 2D at rest

def test_webgl_hero_replaces_the_2d_canvas(gl_browser, webgl_ok, site_url):
    _need_gl(webgl_ok)
    ctx, page = _open(gl_browser, site_url)
    try:
        _wait_3d(page)
        st = page.evaluate(HERO_STATE)
        assert st == {"iris": "webgl", "canvas3d": True, "engine": "webgl"}
        assert page.evaluate("document.getElementById('iris3d').getAttribute('aria-hidden')") == "true"
        # the 2D canvas rests: its pixels no longer change
        a = page.evaluate("document.getElementById('iris').toDataURL()")
        page.wait_for_timeout(500)
        assert a == page.evaluate("document.getElementById('iris').toDataURL()")
        assert page.evaluate("getComputedStyle(document.getElementById('iris')).opacity") == "0"
        assert not page._errors, page._errors
    finally:
        ctx.close()


# ---------------------------------------------------------------- (b) fallbacks leave the 2D canvas running

def _animating(page):
    a = page.evaluate("document.getElementById('iris').toDataURL()")
    page.wait_for_timeout(500)
    return a != page.evaluate("document.getElementById('iris').toDataURL()")


FALLBACKS = {
    "reduced_motion": dict(kw={"reduced_motion": "reduce"}, expect_2d_animating=False),
    "narrow_viewport": dict(width=600),
    "no_webgl": dict(init=(NO_WEBGL,)),
    "error_in_3d_path": dict(init=(THROW_IN_3D,)),
}


@pytest.mark.parametrize("name", FALLBACKS)
def test_fallback_keeps_the_2d_hero_and_the_page_error_free(gl_browser, site_url, name):
    cfg = FALLBACKS[name]
    ctx, page = _open(gl_browser, site_url, width=cfg.get("width", 1280), init=cfg.get("init", ()), **cfg.get("kw", {}))
    try:
        page.wait_for_timeout(1500)
        assert page.evaluate(HERO_STATE) == {"iris": None, "canvas3d": False, "engine": None}, name
        assert page.evaluate("document.getElementById('iris') !== null")
        if cfg.get("expect_2d_animating", True):
            assert _animating(page), f"{name}: the 2D canvas should keep running"
        assert not page._errors, f"{name}: {page._errors}"
        assert page.evaluate("document.documentElement.scrollWidth <= document.documentElement.clientWidth")
    finally:
        ctx.close()


def test_a_lost_context_hands_the_hero_back_to_2d(gl_browser, webgl_ok, site_url):
    _need_gl(webgl_ok)
    ctx, page = _open(gl_browser, site_url)
    try:
        _wait_3d(page)
        page.evaluate("""() => { const gl = document.getElementById('iris3d').getContext('webgl2');
          gl.getExtension('WEBGL_lose_context').loseContext(); }""")
        page.wait_for_function("!document.getElementById('iris3d')", timeout=4000)
        assert page.evaluate(HERO_STATE) == {"iris": None, "canvas3d": False, "engine": None}
        assert _animating(page)
        assert not page._errors, page._errors
    finally:
        ctx.close()


# ---------------------------------------------------------------- (c) on-demand rendering

def test_render_loop_stops_when_input_stops(gl_browser, webgl_ok, site_url):
    _need_gl(webgl_ok)
    ctx, page = _open(gl_browser, site_url, init=(RAF_COUNTER,))
    try:
        _wait_3d(page)
        page.mouse.move(300, 300)
        page.mouse.move(900, 500, steps=8)
        page.mouse.wheel(0, 400)
        page.wait_for_timeout(3000)               # input stopped, scroll settled
        n1 = page.evaluate("window.__raf")
        page.wait_for_timeout(1500)
        n2 = page.evaluate("window.__raf")
        assert n2 == n1, f"requestAnimationFrame kept running after input stopped ({n2 - n1} callbacks in 1.5 s)"
        assert page.evaluate(SNAP)["frames"] > 5
    finally:
        ctx.close()


def test_nothing_renders_while_the_hero_is_off_screen(gl_browser, webgl_ok, site_url):
    _need_gl(webgl_ok)
    ctx, page = _open(gl_browser, site_url, init=(RAF_COUNTER,))
    try:
        _wait_3d(page)
        page.evaluate("window.scrollTo(0, 3000)")
        page.wait_for_timeout(2500)
        before = page.evaluate(SNAP)["frames"]
        page.mouse.move(400, 400)
        page.mouse.move(800, 300, steps=6)
        page.wait_for_timeout(600)
        assert page.evaluate(SNAP)["frames"] == before, "the scene rendered while the hero was off-screen"
    finally:
        ctx.close()


# ---------------------------------------------------------------- (d) pointer and scroll drive the scene, within bounds

def test_pointer_moves_the_scene_within_bounds(gl_browser, webgl_ok, site_url):
    _need_gl(webgl_ok)
    ctx, page = _open(gl_browser, site_url)
    try:
        _wait_3d(page)
        page.mouse.move(40, 60, steps=5)
        page.wait_for_timeout(1500)
        a = page.evaluate(SNAP)
        page.mouse.move(1240, 840, steps=5)
        page.wait_for_timeout(1500)
        b = page.evaluate(SNAP)
        assert b["rotY"] - a["rotY"] > 0.2 and b["rotX"] - a["rotX"] > 0.1, (a, b)
        for s in (a, b):
            assert abs(s["rotY"]) <= 0.301 and abs(s["rotX"]) <= 0.181 and abs(s["camX"]) <= 0.281, s
    finally:
        ctx.close()


def test_scroll_spreads_the_rings_in_depth(gl_browser, webgl_ok, site_url):
    _need_gl(webgl_ok)
    ctx, page = _open(gl_browser, site_url)
    try:
        _wait_3d(page)
        a = page.evaluate(SNAP)
        page.mouse.move(640, 400)
        page.mouse.wheel(0, 380)
        page.wait_for_timeout(2500)
        b = page.evaluate(SNAP)
        span = lambda s: max(s["ringZ"]) - min(s["ringZ"])
        assert b["spread"] > a["spread"] + 0.1, (a["spread"], b["spread"])
        assert span(b) > span(a) * 1.15, (span(a), span(b))
    finally:
        ctx.close()


# ---------------------------------------------------------------- (e) theme

def test_theme_change_retints_without_reload(gl_browser, webgl_ok, site_url):
    _need_gl(webgl_ok)
    ctx, page = _open(gl_browser, site_url)
    try:
        _wait_3d(page)
        # the real toggle: the scene follows the page's own CSS role and the loop is still alive
        page.locator(".nav .theme-toggle").click()
        page.wait_for_timeout(600)
        s = page.evaluate(SNAP)
        css = page.evaluate("""() => { const p = document.createElement('canvas').getContext('2d');
          p.fillStyle = getComputedStyle(document.getElementById('iris')).getPropertyValue('--accent-fill').trim(); return p.fillStyle; }""")
        assert not s["dead"] and "#" + s["gold"] == css.lower(), (s["gold"], css)
        # a role change plus the themechange event re-tints the live materials
        page.evaluate("""() => { document.querySelector('.hero').style.setProperty('--accent-fill', '#ff0000');
          window.dispatchEvent(new CustomEvent('themechange', { detail: { theme: 'dark' } })); }""")
        page.wait_for_timeout(300)
        s = page.evaluate(SNAP)
        assert s["gold"] == "ff0000" and s["ring"] == "ff0000", s
        assert not page._errors, page._errors
    finally:
        ctx.close()


# ---------------------------------------------------------------- (f) Lenis

def test_lenis_runs_without_reduced_motion_and_is_off_with_it(gl_browser, site_url):
    ctx, page = _open(gl_browser, site_url)
    try:
        page.wait_for_timeout(300)
        assert page.evaluate("document.documentElement.classList.contains('lenis')")
        assert page.evaluate("getComputedStyle(document.documentElement).scrollBehavior") in ("auto", "smooth")
    finally:
        ctx.close()
    ctx, page = _open(gl_browser, site_url, reduced_motion="reduce")
    try:
        page.wait_for_timeout(300)
        assert not page.evaluate("document.documentElement.classList.contains('lenis')")
        assert page.evaluate("document.querySelectorAll('.depth, .depth-frame').length") == 0
        page.mouse.move(640, 400)
        page.mouse.wheel(0, 600)
        page.wait_for_timeout(500)
        assert page.evaluate("scrollY") > 300, "reduced motion keeps the browser's own scrolling"
    finally:
        ctx.close()


def test_anchor_jump_lands_below_the_sticky_nav(gl_browser, site_url):
    ctx, page = _open(gl_browser, site_url)
    try:
        page.evaluate("""() => { const a = document.createElement('a'); a.id = 'jump'; a.href = '#process'; a.textContent = 'jump';
          document.querySelector('footer').appendChild(a); }""")
        page.evaluate("document.getElementById('jump').scrollIntoView({block: 'center'})")
        page.wait_for_timeout(300)
        page.locator("#jump").click()
        page.wait_for_function("location.hash === '#process'")
        page.wait_for_timeout(2600)
        r = page.evaluate("""() => ({ top: document.getElementById('process').getBoundingClientRect().top,
          pad: parseFloat(getComputedStyle(document.documentElement).scrollPaddingTop),
          nav: document.querySelector('.nav').getBoundingClientRect().bottom })""")
        assert abs(r["top"] - r["pad"]) <= 2 and r["top"] >= r["nav"], r
        page.go_back()                      # back/forward still work: the hash entry is a real history entry
        page.wait_for_function("location.hash === ''")
        assert not page._errors, page._errors
    finally:
        ctx.close()


def test_skip_link_moves_scroll_and_focus_to_main(gl_browser, site_url):
    ctx, page = _open(gl_browser, site_url)
    try:
        page.keyboard.press("Tab")
        assert page.evaluate("document.activeElement.className") == "skip-link"
        page.keyboard.press("Enter")
        page.wait_for_function("location.hash === '#main'")
        page.wait_for_timeout(2600)
        r = page.evaluate("""() => ({ focus: document.activeElement.id, top: document.getElementById('main').getBoundingClientRect().top,
          pad: parseFloat(getComputedStyle(document.documentElement).scrollPaddingTop), y: scrollY })""")
        assert r["focus"] == "main" and r["y"] > 200 and abs(r["top"] - r["pad"]) <= 2, r
        page.keyboard.press("Tab")           # focus continues from main, not from the top of the page
        assert page.evaluate("document.activeElement.closest('main') !== null")
    finally:
        ctx.close()


def test_tab_into_an_off_screen_link_scrolls_it_clear_of_the_nav(gl_browser, site_url):
    ctx, page = _open(gl_browser, site_url)
    try:
        bad, scrolled = [], False
        for _ in range(45):
            page.keyboard.press("Tab")
            page.wait_for_timeout(120)
            r = page.evaluate("""() => { const e = document.activeElement, b = e.getBoundingClientRect();
              return { top: b.top, bottom: b.bottom, nav: document.querySelector('.nav').getBoundingClientRect().bottom,
                       vh: innerHeight, y: scrollY, tag: e.tagName, inNav: !!e.closest('.nav, .mobile-drawer, .skip-link') }; }""")
            scrolled = scrolled or r["y"] > 100
            if r["inNav"] or r["tag"] == "BODY":
                continue
            if r["top"] < r["nav"] - 1 or r["bottom"] > r["vh"] + 1:
                bad.append(r)
        assert scrolled, "tabbing never left the hero; the test did not exercise scrolling"
        assert not bad, bad
    finally:
        ctx.close()


def test_keyboard_scrolling_still_works(gl_browser, site_url):
    ctx, page = _open(gl_browser, site_url)
    try:
        page.locator("main").focus()
        page.keyboard.press("PageDown")
        page.wait_for_timeout(700)
        assert page.evaluate("scrollY") > 300
        page.keyboard.press("End")
        page.wait_for_timeout(900)
        end = page.evaluate("[scrollY, document.documentElement.scrollHeight - innerHeight]")
        assert abs(end[0] - end[1]) <= 2, end
        page.keyboard.press("Home")
        page.wait_for_timeout(900)
        assert page.evaluate("scrollY") <= 2
    finally:
        ctx.close()


def test_mobile_drawer_still_opens_and_locks_the_page(gl_browser, site_url):
    ctx, page = _open(gl_browser, site_url, width=375, height=800)
    try:
        page.locator(".nav-toggle").click()
        page.wait_for_timeout(300)
        assert page.evaluate("document.querySelector('.mobile-drawer').classList.contains('open')")
        page.mouse.move(100, 400)
        page.mouse.wheel(0, 500)
        page.wait_for_timeout(500)
        assert page.evaluate("scrollY") <= 2, "page scrolled behind the open drawer"
        page.keyboard.press("Escape")
        page.wait_for_timeout(200)
        page.mouse.wheel(0, 400)
        page.wait_for_timeout(1500)
        assert page.evaluate("scrollY") > 100, "scrolling must come back when the drawer closes"
    finally:
        ctx.close()


# ---------------------------------------------------------------- parallax: transform only, rests at zero

def test_parallax_rests_at_the_static_layout(gl_browser, site_url):
    ctx, page = _open(gl_browser, site_url)
    try:
        page.wait_for_timeout(500)
        offsets = page.evaluate("""() => [...document.querySelectorAll('.hero .depth')].map(e => getComputedStyle(e).transform)""")
        assert offsets and all(t in ("none", "matrix(1, 0, 0, 1, 0, 0)") for t in offsets), offsets
        page.mouse.move(640, 400)
        page.mouse.wheel(0, 300)
        page.wait_for_timeout(1500)
        moved = page.evaluate("getComputedStyle(document.querySelector('.hero-inner')).transform")
        assert moved not in ("none", "matrix(1, 0, 0, 1, 0, 0)"), "the headline layer should lag the page while scrolling"
        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(1200)
        assert page.evaluate("getComputedStyle(document.querySelector('.hero-inner')).transform") in ("none", "matrix(1, 0, 0, 1, 0, 0)")
    finally:
        ctx.close()


def test_print_clears_every_depth_transform(gl_browser, site_url):
    ctx, page = _open(gl_browser, site_url)
    try:
        page.mouse.move(640, 400)
        page.mouse.wheel(0, 500)
        page.wait_for_timeout(1500)
        page.emulate_media(media="print")
        t = page.evaluate("""() => [...document.querySelectorAll('.depth, .depth-frame img')].map(e => getComputedStyle(e).transform)""")
        assert t and all(x == "none" for x in t), t
    finally:
        ctx.close()


# ---------------------------------------------------------------- (g) no sideways scroll

@pytest.mark.parametrize("width", (320, 1280))
@pytest.mark.parametrize("theme", THEMES)
def test_home_has_no_horizontal_scroll_with_the_3d_hero(gl_browser, site_url, width, theme):
    ctx, page = _open(gl_browser, site_url, width=width, height=800, theme=theme)
    try:
        page.wait_for_timeout(2200)
        sw, cw = page.evaluate("[document.documentElement.scrollWidth, document.documentElement.clientWidth]")
        assert sw <= cw, f"{width} [{theme}]: scrollWidth {sw} > clientWidth {cw}"
    finally:
        ctx.close()


# ---------------------------------------------------------------- (h) accessibility with the canvas present

HERO_TEXT = ".hero h1, .hero-lead, .hero .eyebrow, .hero-actions a, .hstat .n, .hstat .l"


@pytest.mark.parametrize("theme", THEMES)
@pytest.mark.parametrize("width", (768, 1024, 1280))
def test_home_axe_and_pixel_contrast_with_the_canvas(gl_browser, webgl_ok, site_url, width, theme):
    _need_gl(webgl_ok)
    ctx, page = _open(gl_browser, site_url, width=width, theme=theme)
    try:
        _wait_3d(page)
        found = {v.rule: (v.nodes, v.selectors[:4]) for v in run_axe(page, width)}
        assert not found, f"{width} [{theme}] axe violations with the WebGL canvas: {found}"
        assert page.evaluate("document.querySelector('.hero').dataset.iris") == "webgl"
        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(1200)
        res = measure(page, [s.strip() for s in HERO_TEXT.split(",")])
        failing = {s: (round(r["ratio"], 2) if r["ratio"] is not None else None, r["required"])
                   for s, r in res.items()
                   if (r["ratio"] is None and r["hasText"]) or (r["ratio"] is not None and r["ratio"] < r["required"])}
        assert not failing, f"{width} [{theme}] hero text contrast over the WebGL canvas: {failing}"
    finally:
        ctx.close()
