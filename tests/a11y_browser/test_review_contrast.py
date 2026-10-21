"""Every colour-contrast "needs review" result from axe is checked against real rendered pixels.

axe cannot resolve text over gradients, photographs, pseudo-element fills or single
glyphs, so it reports them as "needs review". tests/a11y_review.json justifies those
items by cause; this test is what makes the justification true: it measures the
actual glyph/background contrast (see pixel_contrast.py) for every such node at
every width and requires 4.5:1 (3:1 for large text).
"""
import pytest

from a11y_browser.conftest import PAGES, THEMES, WIDTHS, new_context, open_page, run_axe_full
from a11y_browser.pixel_contrast import measure

pytestmark = pytest.mark.browser

CASES = [(s, w, t) for t in THEMES for s in PAGES for w in WIDTHS]
IDS = [f"{s}-{w}-{t}" for s, w, t in CASES]


@pytest.mark.parametrize("stem,width,theme", CASES, ids=IDS)
def test_needs_review_contrast_nodes_pass_when_measured(browser, site_url, stem, width, theme):
    ctx = new_context(browser, width, 900, theme=theme, reduced_motion="reduce")
    try:
        page = open_page(ctx, site_url, stem)
        _, review = run_axe_full(page, width)
        selectors = sorted({sel for r in review if r.rule == "color-contrast" for sel in r.selectors})
        page.set_viewport_size({"width": width, "height": 900})
        results = measure(page, selectors)
    finally:
        ctx.close()
    failing = {
        s: (round(r["ratio"], 2) if r["ratio"] is not None else None, r["required"], r["note"])
        for s, r in results.items()
        if (r["ratio"] is None and r["hasText"]) or (r["ratio"] is not None and r["ratio"] < r["required"])
    }
    assert not failing, f"{stem}@{width} [{theme}]: measured contrast below the minimum (selector: (ratio, required, note)): {failing}"
