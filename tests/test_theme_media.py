"""Static contract for the light/dark switch: generated CSS, head script order, toggle chrome."""
import re

import build
from bs4 import BeautifulSoup
from conftest import ROOT
from tools import theme as T

CONTEXTS = ("page", "alt", "card", "inverse", "accent")
ROLES = T.ROLES


def _css():
    return T.render_css(T.resolve(T.load_theme()))


def _media_block(css):
    start = css.index("@media (prefers-color-scheme: dark)")
    depth, i = 0, css.index("{", start)
    for j in range(i, len(css)):
        depth += css[j] == "{"
        depth -= css[j] == "}"
        if depth == 0:
            return css[i + 1:j]
    raise AssertionError("unbalanced media block")


def test_theme_css_has_system_dark_rules_scoped_to_unset_theme():
    media = _media_block(_css())
    root = re.search(r":root:not\(\[data-theme\]\)\s*\{([^}]*)\}", media)
    assert root and "color-scheme: dark" in root.group(1)
    for role in ROLES:
        assert f"--{role}:" in root.group(1), role
    for ctx in CONTEXTS:
        m = re.search(r":root:not\(\[data-theme\]\) \.surface-" + ctx + r"\s*\{([^}]*)\}", media)
        assert m, ctx
        for role in ROLES:
            assert f"--{role}:" in m.group(1), (ctx, role)


def test_theme_css_declares_color_scheme_per_theme():
    css = _css()
    assert re.search(r"^:root \{[^}]*color-scheme: light;", css, re.M)
    assert re.search(r':root\[data-theme="light"\] \{[^}]*color-scheme: light;', css)
    assert re.search(r':root\[data-theme="dark"\] \{[^}]*color-scheme: dark;', css)


def test_every_media_selector_is_scoped_to_an_unset_theme():
    selectors = re.findall(r"([^{}]+)\{", _media_block(_css()))
    assert selectors and all(":root:not([data-theme])" in s for s in selectors), selectors


def test_head_script_runs_before_the_stylesheet_and_uses_the_contract():
    for stem, html in build.render_all().items():
        assert html.count("ayin-theme") == 1, stem
        i_script = html.index("ayin-theme")
        assert i_script < html.index(f'href="{build.page_root(stem)}assets/theme.css"'), stem
        assert html.rindex("<script", 0, i_script) > html.index("<head>"), stem
        script = html[html.rindex("<script", 0, i_script):html.index("</script>", i_script)]
        for needle in ("localStorage", "prefers-color-scheme: dark", "dataset.theme", "catch"):
            assert needle in script, (stem, needle)


def test_every_page_has_one_toggle_in_nav_and_one_in_drawer():
    for stem, html in build.render_all().items():
        soup = BeautifulSoup(html, "html.parser")
        for sel in ("nav.nav", ".mobile-drawer"):
            btns = soup.select(f"{sel} button.theme-toggle")
            assert len(btns) == 1, (stem, sel)
            b = btns[0]
            assert b["type"] == "button" and b["aria-pressed"] == "false", (stem, sel)
            assert b.get("aria-label") == "Dark mode", (stem, sel)
            svg = b.find("svg")
            assert svg and svg.get("aria-hidden") == "true", (stem, sel)
        assert len(soup.select(".theme-toggle")) == 2, stem


def test_toggle_is_hidden_until_the_head_script_has_run():
    css = (ROOT / "assets" / "styles.css").read_text(encoding="utf-8")
    assert re.search(r"\.theme-toggle\s*\{[^}]*display:\s*none", css)
    assert re.search(r"html\[data-theme\]\s+\.theme-toggle", css)


def test_site_js_implements_the_contract():
    js = (ROOT / "assets" / "site.js").read_text(encoding="utf-8")
    for needle in ("ayin-theme", "themechange", "theme-color", "aria-pressed"):
        assert needle in js, needle
