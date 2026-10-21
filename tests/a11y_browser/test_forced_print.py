"""Phase 2c Task 3: forced colours and print, in both themes.

Forced colours (Windows high contrast): the theme toggle must stay visible and legible with system colours, and its
pressed state must be told apart by shape (moon or sun), not by colour. Print: always the light look, no toggle.
"""
import pytest

from a11y_browser.conftest import THEMES, new_context, open_page

pytestmark = pytest.mark.browser

STEMS = ("index", "BizCheck", "Contact")


def _sys_color(page, name):
    return page.evaluate(
        """(n) => { const p = document.createElement('i'); p.style.color = n; document.body.appendChild(p);
          const v = getComputedStyle(p).color; p.remove(); return v; }""", name)


@pytest.mark.parametrize("theme", THEMES)
@pytest.mark.parametrize("stem", STEMS)
def test_toggle_is_visible_and_legible_in_forced_colours(browser, site_url, stem, theme):
    ctx = new_context(browser, 1280, 900, theme=theme, forced_colors="active")
    try:
        page = open_page(ctx, site_url, stem)
        assert page.evaluate("matchMedia('(forced-colors: active)').matches")
        t = page.evaluate(
            """() => { const b = document.querySelector('.nav .theme-toggle'); const c = getComputedStyle(b), r = b.getBoundingClientRect();
              const vis = (s) => { const e = b.querySelector(s); return e ? getComputedStyle(e).display : null; };
              return {display: c.display, w: r.width, h: r.height, color: c.color, borderStyle: c.borderTopStyle,
                      borderWidth: parseFloat(c.borderTopWidth), borderColor: c.borderTopColor,
                      bg: c.backgroundColor, moon: vis('.ico-moon'), sun: vis('.ico-sun'),
                      stroke: getComputedStyle(b.querySelector('.theme-ico')).stroke, pressed: b.getAttribute('aria-pressed')}; }""")
        assert t["display"] != "none" and t["w"] >= 44 and t["h"] >= 44, t
        # Visible shape: a real border in a system colour, icon stroked in the system text colour.
        assert t["borderStyle"] != "none" and t["borderWidth"] >= 1, t
        assert t["borderColor"] == _sys_color(page, "ButtonText") or t["borderColor"] == t["color"], t
        assert t["color"] == _sys_color(page, "ButtonText"), t
        assert t["stroke"] == t["color"], t
        # Pressed state by shape: moon while off, sun while on; exactly one is shown.
        assert t["moon"] == "none" and t["sun"] != "none" if theme == "dark" else t["sun"] == "none" and t["moon"] != "none", t
        # And it still flips, and the border/shape cue follows.
        page.click(".nav .theme-toggle")
        assert page.evaluate("document.documentElement.dataset.theme") == ("light" if theme == "dark" else "dark")
        assert page.evaluate("document.querySelector('.nav .theme-toggle').getAttribute('aria-pressed')") == ("false" if theme == "dark" else "true")
        w = page.evaluate("parseFloat(getComputedStyle(document.querySelector('.nav .theme-toggle')).borderTopWidth)")
        assert (w > t["borderWidth"]) == (theme == "light"), (w, t["borderWidth"])
    finally:
        ctx.close()


@pytest.mark.parametrize("theme", THEMES)
def test_toggle_focus_and_drawer_row_in_forced_colours(browser, site_url, theme):
    ctx = new_context(browser, 375, 800, theme=theme, forced_colors="active")
    try:
        page = open_page(ctx, site_url, "index")
        page.focus(".nav .theme-toggle")
        o = page.evaluate("(() => { const c = getComputedStyle(document.activeElement); return [c.outlineStyle, parseFloat(c.outlineWidth)]; })()")
        assert o[0] != "none" and o[1] >= 2, o
        page.click(".nav-toggle")
        page.wait_for_timeout(800)
        d = page.evaluate(
            """() => { const b = document.querySelector('.mobile-drawer .theme-toggle'); const c = getComputedStyle(b), r = b.getBoundingClientRect();
              return {w: r.width, h: r.height, border: c.borderTopStyle, text: b.textContent.trim(), color: c.color, bg: getComputedStyle(b.closest('.mobile-drawer')).backgroundColor}; }""")
        assert d["h"] >= 44 and d["text"] == "Dark mode" and d["border"] != "none", d
        assert d["color"] != d["bg"], d
    finally:
        ctx.close()


@pytest.mark.parametrize("theme", THEMES)
@pytest.mark.parametrize("stem", STEMS)
def test_print_always_prints_the_light_look_without_the_toggle(browser, site_url, stem, theme):
    ctx = new_context(browser, 1280, 900, theme=theme)
    try:
        page = open_page(ctx, site_url, stem)
        screen = page.evaluate("getComputedStyle(document.body).backgroundColor")
        page.emulate_media(media="print")
        r = page.evaluate(
            """() => { const rs = (e, v) => getComputedStyle(e).getPropertyValue(v).trim();
              const cs = (sel) => [...document.querySelectorAll(sel)].map(e => getComputedStyle(e).display);
              return {scheme: getComputedStyle(document.documentElement).colorScheme, rootSurface: rs(document.documentElement, '--surface'),
                      rootInk: rs(document.documentElement, '--ink'), body: getComputedStyle(document.body).backgroundColor,
                      page: [...document.querySelectorAll('.surface-page,.surface-alt,.surface-card')].map(e => [rs(e, '--surface'), rs(e, '--ink')]),
                      toggles: cs('.theme-toggle'), filters: [...document.querySelectorAll('img')].map(e => getComputedStyle(e).filter)}; }""")
        assert r["scheme"] == "light", r
        assert r["rootSurface"].lower() == "#faf7f0" and r["rootInk"].lower() == "#061325", r
        assert all(d == "none" for d in r["toggles"]) and r["toggles"], r
        assert all(f == "none" for f in r["filters"]), r
        for surf, ink in r["page"]:
            assert ink.lower() == "#061325", (surf, ink)
        if theme == "dark":
            assert screen != r["body"], "dark screen look must not leak into print"
    finally:
        ctx.close()


def test_print_light_look_without_a_theme_attribute(browser, site_url):
    """No JavaScript (no data-theme) on a dark system: print is light as well."""
    ctx = browser.new_context(viewport={"width": 1280, "height": 900}, color_scheme="dark", java_script_enabled=False)
    ctx.route("**/*", lambda route: route.continue_() if route.request.url.startswith("http://127.0.0.1") else route.abort())
    try:
        page = ctx.new_page()
        page.goto(f"{site_url}/index.html", wait_until="load")
        assert page.evaluate("getComputedStyle(document.documentElement).colorScheme") == "dark"
        page.emulate_media(media="print")
        assert page.evaluate("getComputedStyle(document.documentElement).colorScheme") == "light"
        assert page.evaluate("getComputedStyle(document.documentElement).getPropertyValue('--surface').trim().toLowerCase()") == "#faf7f0"
    finally:
        ctx.close()
