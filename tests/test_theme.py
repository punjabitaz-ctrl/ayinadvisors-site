import re

import build
from conftest import ROOT
from tools import theme as T
from tools.contrast import ratio

THEMES = ("light", "dark")
CONTEXTS = ("page", "alt", "card", "inverse", "accent")
ROLES = (
    "surface", "ink", "ink-muted", "accent-ink", "line", "field-bg", "field-border",
    "field-ink", "field-placeholder", "focus-ring", "danger-ink", "success-ink",
)


def _resolved():
    return T.resolve(T.load_theme())


def test_every_context_defines_every_role():
    res = _resolved()
    for th in THEMES:
        assert set(res[th]) >= set(CONTEXTS), th
        for ctx in CONTEXTS:
            for role in ROLES:
                v = res[th][ctx].get(role)
                assert v and re.fullmatch(r"#[0-9a-f]{6}", v), (th, ctx, role, v)


def test_dark_theme_defines_the_same_roles_as_light():
    res = _resolved()
    for key in res["light"]:
        assert set(res["dark"][key]) == set(res["light"][key]), key
    assert set(res["dark"]) == set(res["light"])


def test_all_required_pairings_pass():
    res = _resolved()
    assert T.failures(res) == []
    seen = {p[0] for p in T.required_pairings(res)}
    assert seen == set(THEMES)


def test_pairings_cover_every_context_and_theme():
    res = _resolved()
    pairs = T.required_pairings(res)
    for th in THEMES:
        for ctx in CONTEXTS:
            fgs = {p[2] for p in pairs if p[0] == th and p[1] == ctx}
            assert {"ink", "ink-muted", "accent-ink", "danger-ink", "success-ink",
                    "field-ink", "field-placeholder", "field-border", "focus-ring"} <= fgs, (th, ctx)


def test_failures_detects_a_bad_pairing():
    res = _resolved()
    res["light"]["page"]["ink"] = res["light"]["page"]["surface"]
    assert any("ink" in f for f in T.failures(res))


def test_state_pairings_are_declared_and_pass():
    res = _resolved()
    pairs = T.required_pairings(res)
    labels = {p[5] for p in pairs}
    for needed in ("link hover", "button hover", "placeholder", "error text"):
        assert any(needed in lab for lab in labels), needed
    for th, ctx, fg, bg, minimum, label in pairs:
        if any(n in label for n in ("link hover", "button hover", "placeholder", "error text")):
            a = res[th].get(ctx, {}).get(fg) or res[th]["global"][fg]
            b = res[th].get(ctx, {}).get(bg) or res[th]["global"][bg]
            assert ratio(a, b) >= minimum, (th, ctx, label)


def test_gold_ink_is_text_safe_on_every_light_surface():
    theme = T.load_theme()
    res = T.resolve(theme)
    gold_ink = res["light"]["page"]["accent-ink"]
    for name in ("white", "cream", "almond", "beige"):
        assert ratio(gold_ink, theme["palette"][name]) >= 4.5, name


def test_text_roles_are_solid():
    res = _resolved()
    for th in THEMES:
        for ctx, roles in res[th].items():
            for role, val in roles.items():
                if role.endswith("ink") or role.startswith("ink") or role == "field-placeholder":
                    assert "rgba(" not in val and "alpha" not in val, (th, ctx, role)
                    assert re.fullmatch(r"#[0-9a-f]{6}", val), (th, ctx, role)


def test_css_text_roles_have_no_alpha():
    css = T.render_css(_resolved())
    for line in css.splitlines():
        if re.match(r"\s*--(ink|accent-ink|danger-ink|success-ink|field-ink|field-placeholder)", line):
            assert "rgb" not in line and "color-mix" not in line, line


def test_css_has_complete_role_set_per_context_and_theme():
    css = T.render_css(_resolved())
    for ctx in CONTEXTS:
        for sel in (f".surface-{ctx}", f'[data-theme="dark"] .surface-{ctx}'):
            m = re.search(re.escape(sel) + r"\s*(?:,[^{]*)?\{([^}]*)\}", css)
            assert m, sel
            for role in ROLES:
                assert f"--{role}:" in m.group(1), (sel, role)
    assert ":root" in css


def test_theme_css_is_fresh():
    built = (ROOT / "assets" / "theme.css").read_text(encoding="utf-8")
    assert built == build.render_theme()


def test_check_flags_a_stale_theme_css(sandbox):
    (sandbox / "assets" / "theme.css").write_text("/* stale */", encoding="utf-8")
    assert build.check() == ["assets/theme.css"]
