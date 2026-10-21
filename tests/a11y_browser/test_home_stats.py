"""Home 'why' statistics: four clean numerals, no stray copy (owner decision 2026-10)."""
import pytest

from a11y_browser.conftest import new_context, open_page

pytestmark = pytest.mark.browser


def test_why_stats_read_cleanly(browser, site_url):
    ctx = new_context(browser, 1280, 900, reduced_motion="reduce")
    try:
        page = open_page(ctx, site_url, "index")
        page.evaluate("document.querySelector('.why-stats').scrollIntoView({block:'center', behavior:'instant'})")
        page.wait_for_function(
            "[...document.querySelectorAll('.why-stat .n')].every(e => e.textContent.trim() !== '')", timeout=8000)
        texts = page.eval_on_selector_all(".why-stat .n", "els => els.map(e => e.textContent.trim())")
        assert texts == ["$24T", "50", "70%", "3x"]
        whole = page.inner_text(".why-stats")
        for bad in ("27T", "50 States", "Trillion"):
            assert bad not in whole, bad
    finally:
        ctx.close()
