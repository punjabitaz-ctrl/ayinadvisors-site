"""Every page in content/site.json must be in every browser-gate matrix (a page added to the site is gated by default)."""
import build


def _stems(cases) -> set[str]:
    return {c[0] for c in cases}


def _parametrized(fn, argname: str) -> set[str]:
    out: set[str] = set()
    for mark in getattr(fn, "pytestmark", []):
        if mark.name == "parametrize" and mark.args[0] == argname:
            out |= set(mark.args[1])
    return out


def test_every_site_page_is_in_the_gate_matrix():
    from a11y_browser import test_axe, test_behaviour, test_review_contrast
    from a11y_browser.conftest import THEMES, WIDTHS

    site = set(build.live_pages())  # a scheduled post joins the matrix the morning it goes live
    assert set(build.PAGES) == site
    assert _stems(test_axe.CASES) == site, "axe matrix"
    assert _stems(test_review_contrast.CASES) == site, "pixel-contrast matrix"
    assert _parametrized(test_behaviour.test_no_horizontal_scroll_at_320, "stem") == site, "320px scroll"
    assert _parametrized(test_behaviour.test_no_text_is_clipped_at_320, "stem") == site, "320px clipping"
    assert _parametrized(
        test_behaviour.test_form_controls_have_a_3_to_1_boundary_against_their_surroundings, "stem") == site, "form boundary"
    # and each page is covered at all three widths in both themes
    for cases in (test_axe.CASES, test_review_contrast.CASES):
        for stem in site:
            assert {(w, t) for s, w, t in cases if s == stem} == {(w, t) for w in WIDTHS for t in THEMES}, stem
