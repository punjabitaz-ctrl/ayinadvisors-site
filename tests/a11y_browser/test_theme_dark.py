"""Phase 2c Task 2: things that held a fixed colour now follow the theme, and nothing in dark is left behind.

Covers the logo mark, the iris canvas, the select arrow, photographs, form placeholders, selection, the focus ring
and the Turnstile widget theme. Each assertion is made in both themes (set the way a visitor gets them: emulated
system scheme plus the stored choice; `open_page` asserts `html[data-theme]`).
"""
import re

import pytest

from a11y_browser.conftest import THEMES, new_context, open_page
from a11y_browser.pixel_contrast import ratio

pytestmark = pytest.mark.browser

RGB = re.compile(r"rgba?\(\s*(\d+)[ ,]+(\d+)[ ,]+(\d+)(?:[ ,/]+([\d.]+))?\s*\)")


def rgb(css):
    h = re.fullmatch(r"#([0-9a-fA-F]{6})", css.strip())
    if h:
        return tuple(int(h.group(1)[i:i + 2], 16) for i in (0, 2, 4))
    m = RGB.search(css)
    assert m, f"not a colour: {css!r}"
    return tuple(int(m.group(i)) for i in (1, 2, 3))


def alpha(css):
    m = RGB.search(css)
    return float(m.group(4)) if m and m.group(4) is not None else 1.0


def _ctx_page(browser, site_url, stem, theme, width=1280, **kw):
    ctx = new_context(browser, width, 900, theme=theme, **kw)
    return ctx, open_page(ctx, site_url, stem)


# ------------------------------------------------------------------ logo mark

LOGO_JS = """() => [...document.querySelectorAll('.logo-mark')].map(svg => {
  const q = (s) => [...svg.querySelectorAll(s)].map(e => { const c = getComputedStyle(e);
    return {fill: c.fill, stroke: c.stroke, opacity: c.opacity, attrFill: e.getAttribute('fill'), attrStroke: e.getAttribute('stroke')}; });
  const host = svg.closest('.surface-inverse');
  return {where: host ? host.className : '', circles: q('circle'),
          bg: getComputedStyle(host).getPropertyValue('--surface').trim(),
          fillRole: getComputedStyle(host).getPropertyValue('--accent-fill').trim()};
})"""


def test_logo_and_canvas_follow_theme(browser, site_url):
    """The logo mark is painted from CSS variables (no colour in the markup) and meets 3:1 on its surface in both themes;
    the iris canvas reads its colours from CSS variables and repaints when the theme changes."""
    seen = {}
    for theme in THEMES:
        ctx, page = _ctx_page(browser, site_url, "index", theme, reduced_motion="no-preference")
        try:
            logos = page.evaluate(LOGO_JS)
            assert len(logos) == 2, "expected the nav logo and the footer logo"
            for lg in logos:
                bg = rgb(lg["bg"])
                for c in lg["circles"]:
                    assert c["attrFill"] in (None, "none") and c["attrStroke"] in (None, "none"), \
                        f"[{theme}] logo circle still carries a colour attribute: {c}"
                ring, ring2, dot, pupil = lg["circles"]
                assert ratio(rgb(ring["stroke"]), bg) >= 3.0, f"[{theme}] outer ring {ring['stroke']} on {lg['bg']}"
                assert ratio(rgb(dot["fill"]), bg) >= 3.0, f"[{theme}] iris dot {dot['fill']} on {lg['bg']}"
                assert rgb(pupil["fill"]) == bg, f"[{theme}] pupil should be the surface it sits on"
                assert rgb(ring["stroke"]) == rgb(lg["fillRole"]), f"[{theme}] ring should be the accent-fill role"
            seen[theme] = [(lg["circles"][0]["stroke"], lg["circles"][3]["fill"]) for lg in logos]
        finally:
            ctx.close()
    # Nav and footer stay navy in both themes, so the mark's resolved colours are identical in both (by design)...
    assert seen["light"] == seen["dark"]

    # ...which means the canvas test must prove the mechanism, not a light/dark difference: recolour the roles on the
    # canvas' own surface, announce a theme change, and the next frames must be painted in the new colour.
    for theme in THEMES:
        ctx, page = _ctx_page(browser, site_url, "index", theme, reduced_motion="no-preference")
        try:
            page.wait_for_timeout(500)
            dom = "PIX"
            sample = """() => { const c = document.getElementById('iris'); const g = c.getContext('2d');
              const d = g.getImageData(0, 0, c.width, c.height).data; let r = 0, gr = 0, b = 0, n = 0;
              for (let i = 0; i < d.length; i += 4) if (d[i + 3] > 40) { r += d[i]; gr += d[i + 1]; b += d[i + 2]; n++; }
              return n ? [r / n, gr / n, b / n, n] : null; }"""
            before = page.evaluate(sample)
            assert before and before[0] > before[2], f"[{theme}] canvas should start gold (red above blue): {before}"
            page.evaluate("""() => { const c = document.getElementById('iris'); c.parentElement.style.setProperty('--accent-fill', '#00aa44');
              c.style.setProperty('--accent-fill', '#00aa44'); window.dispatchEvent(new CustomEvent('themechange', {detail: {theme: 'x'}})); }""")
            page.wait_for_timeout(400)
            after = page.evaluate(sample)
            assert after and after[1] > after[0] and after[1] > after[2], f"[{theme}] canvas did not repaint from the variable: {after}"
        finally:
            ctx.close()


# ------------------------------------------------------------------ select arrow

SELECT_JS = """() => [...document.querySelectorAll('.field select')].map(s => { const c = getComputedStyle(s);
  return {id: s.id, image: c.backgroundImage, bg: c.backgroundColor, fieldBg: c.getPropertyValue('--field-bg').trim(),
          arrow: c.getPropertyValue('--accent-ink').trim()}; })"""


@pytest.mark.parametrize("stem", ("BizCheck",))   # Contact has no select
def test_select_arrow_follows_theme(browser, site_url, stem):
    """The arrow is drawn with the accent-ink role (no colour baked into an image URL), so it changes with the theme."""
    arrows = {}
    for theme in THEMES:
        ctx, page = _ctx_page(browser, site_url, stem, theme)
        try:
            sels = page.evaluate(SELECT_JS)
            assert sels, f"{stem}: no select found"
            for s in sels:
                assert "url(" not in s["image"], f"[{theme}] arrow is an image URL with a baked colour: {s['image'][:80]}"
                colours = {rgb(m) for m in re.findall(r"rgba?\([^)]*\)", s["image"]) if alpha(m) > 0}
                assert colours == {rgb(s["arrow"])}, f"[{theme}] arrow colours {colours} != accent-ink {s['arrow']}"
                field = rgb(s["bg"]) if alpha(s["bg"]) == 1 else rgb(s["fieldBg"])
                assert ratio(rgb(s["arrow"]), field) >= 3.0, f"[{theme}] arrow {s['arrow']} on {field}"
                arrows.setdefault(theme, set()).add(s["arrow"])
        finally:
            ctx.close()
    assert arrows["light"] != arrows["dark"], f"{stem}: the arrow is the same colour in both themes {arrows}"


# ------------------------------------------------------------------ photographs

IMG_JS = """() => [...document.querySelectorAll('img')].map(i => ({src: i.getAttribute('src'), filter: getComputedStyle(i).filter}))"""


# Home has no photograph since Sprint 2 Task 3 (the US photo moved to Partnerships)
@pytest.mark.parametrize("stem", ("About", "BizCheck", "partnerships"))
def test_images_dimmed_only_in_dark(browser, site_url, stem):
    results = {}
    for theme in THEMES:
        ctx, page = _ctx_page(browser, site_url, stem, theme)
        try:
            results[theme] = page.evaluate(IMG_JS)
        finally:
            ctx.close()
    for theme, imgs in results.items():
        for i in imgs:
            if theme == "light":
                assert i["filter"] == "none", f"[light] {stem} {i['src']}: filter {i['filter']}"
            else:
                m = re.fullmatch(r"brightness\(([\d.]+)\)", i["filter"])
                assert m and 0.85 <= float(m.group(1)) <= 0.95, f"[dark] {stem} {i['src']}: filter {i['filter']!r}, want about brightness(0.9)"
    assert results["dark"], f"{stem}: no photograph found; the test would pass vacuously"


# ------------------------------------------------------------------ placeholders, selection, focus ring

FIELD_JS = """() => [...document.querySelectorAll('.field input, .field textarea, .field select')].map(e => {
  const c = getComputedStyle(e), p = getComputedStyle(e, '::placeholder');
  return {id: e.id, tag: e.tagName, placeholder: e.getAttribute('placeholder'), pcolor: p.color, popacity: p.opacity, bg: c.backgroundColor,
          fieldBg: c.getPropertyValue('--field-bg').trim(), ink: c.color, surface: c.getPropertyValue('--surface').trim(), scheme: c.colorScheme}; })"""


@pytest.mark.parametrize("theme", THEMES)
@pytest.mark.parametrize("stem", ("Contact", "BizCheck"))
def test_form_text_placeholders_and_scheme_in_both_themes(browser, site_url, stem, theme):
    ctx, page = _ctx_page(browser, site_url, stem, theme)
    try:
        fields = page.evaluate(FIELD_JS)
    finally:
        ctx.close()
    assert len(fields) >= 4, fields
    bad = []
    for f in fields:
        bg = rgb(f["bg"]) if alpha(f["bg"]) == 1 else rgb(f["fieldBg"])
        if ratio(rgb(f["ink"]), bg) < 4.5:
            bad.append((f["id"], "typed text", round(ratio(rgb(f["ink"]), bg), 2)))
        if f["placeholder"] and f["tag"] != "SELECT":
            pc = rgb(f["pcolor"])
            eff = tuple(round(alpha(f["pcolor"]) * c + (1 - alpha(f["pcolor"])) * b) for c, b in zip(pc, bg))
            r = ratio(eff, bg)
            if r < 4.5:
                bad.append((f["id"], "placeholder", round(r, 2)))
    assert not bad, f"{stem} [{theme}]: {bad}"
    assert all(f["scheme"] == theme for f in fields), f"{stem} [{theme}]: native controls not in the theme's colour-scheme: {[f['scheme'] for f in fields]}"


@pytest.mark.parametrize("theme", THEMES)
def test_selection_and_focus_ring_in_both_themes(browser, site_url, theme):
    """::selection pairs and the two-tone focus ring hold their contrast on every surface, in each theme."""
    ctx, page = _ctx_page(browser, site_url, "Contact", theme)
    try:
        res = page.evaluate(
            """() => { const out = [];
              const roles = (el) => { const c = getComputedStyle(el); const g = (n) => c.getPropertyValue(n).trim(); return {surface: g('--surface'), ring: g('--focus-ring'), ink: g('--ink')}; };
              const probe = document.createElement('i'); document.body.appendChild(probe);
              const norm = (v) => { probe.style.color = v; return getComputedStyle(probe).color; };
              for (const s of document.querySelectorAll('.surface-page, .surface-alt, .surface-card, .surface-inverse, .surface-accent')) {
                const r = roles(s); out.push({cls: s.className.split(' ').find(x => x.startsWith('surface-')), surface: norm(r.surface), ring: norm(r.ring)});
              }
              const sel = getComputedStyle(document.body, '::selection');
              probe.remove();
              return {rows: out, selBg: sel.backgroundColor, selFg: sel.color}; }""")
    finally:
        ctx.close()
    assert res["rows"], "no surfaces found"
    for r in res["rows"]:
        assert ratio(rgb(r["ring"]), rgb(r["surface"])) >= 3.0, f"[{theme}] focus ring on {r['cls']}: {r}"
    assert ratio(rgb(res["selFg"]), rgb(res["selBg"])) >= 4.5, f"[{theme}] selection {res['selFg']} on {res['selBg']}"


# ------------------------------------------------------------------ Turnstile

STUB = """window.__tsOpts = [];
window.turnstile = {render: (sel, o) => { window.__tsOpts.push({sel, ...o}); return 'w' + window.__tsOpts.length; }, getResponse: () => '', reset() {}, remove() {}};"""


@pytest.mark.parametrize("theme", THEMES)
@pytest.mark.parametrize("stem,render,box", [("Contact", "__ctRenderTurnstile", "#ct-turnstile"), ("BizCheck", "__bcRenderTurnstile", "#bc-turnstile")])
def test_turnstile_widget_theme_follows_the_surface_it_sits_on(browser, site_url, stem, render, box, theme):
    """The explicit render passes a theme that matches the surface behind the widget in the active theme (the widget
    cannot follow our toggle on its own: `auto` follows the operating system only)."""
    ctx = new_context(browser, 1280, 900, theme=theme)
    ctx.add_init_script(STUB)
    try:
        page = open_page(ctx, site_url, stem)
        page.evaluate(f"window.{render}()")
        got = page.evaluate("window.__tsOpts[0]")
        surf = page.evaluate(
            """(sel) => { const p = document.createElement('i'); document.body.appendChild(p);
              p.style.color = getComputedStyle(document.querySelector(sel)).getPropertyValue('--surface'); const v = getComputedStyle(p).color; p.remove(); return v; }""", box)
    finally:
        ctx.close()
    r, g, b = rgb(surf)
    lum = 0.2126 * (r / 255) ** 2.2 + 0.7152 * (g / 255) ** 2.2 + 0.0722 * (b / 255) ** 2.2
    assert got["theme"] in ("light", "dark"), f"theme option must be an explicit light/dark chosen from the surface, got {got}"
    assert got["theme"] == ("dark" if lum < 0.18 else "light"), f"{stem} [{theme}]: widget theme {got['theme']!r} on surface {surf}"
    assert got["action"] in ("contact", "bizcheck") and got["sitekey"]
