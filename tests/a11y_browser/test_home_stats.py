"""Home hero statistics: three clean entries, each a claim the site already made (Sprint 2 Task 3)."""
import pytest

from a11y_browser.conftest import new_context, open_page

pytestmark = pytest.mark.browser


def test_hero_stats_read_cleanly(browser, site_url):
    ctx = new_context(browser, 1280, 900, reduced_motion="reduce")
    try:
        page = open_page(ctx, site_url, "index")
        page.wait_for_function(
            "[...document.querySelectorAll('.hstat .n')].every(e => e.textContent.trim() !== '')", timeout=8000)
        texts = page.eval_on_selector_all(".hstat .n", "els => els.map(e => e.textContent.trim())")
        assert texts == ["3", "90 Days", "Founder-led"]
        labels = page.eval_on_selector_all(".hstat .l", "els => els.map(e => e.textContent.trim())")
        assert labels[1] == "To first qualified partner" and labels[2] == "Operators, not observers"
        # the Why-the-US band and its four numerals moved to the Partnerships page
        assert page.locator(".why-stats, .why-stat, .globe-stage").count() == 0
    finally:
        ctx.close()


def test_partnerships_proof_stats_still_read_cleanly(browser, site_url):
    """The four numerals the Home band used to carry now live in the Partnerships proof band (owner decision 2026-10)."""
    ctx = new_context(browser, 1280, 900, reduced_motion="reduce")
    try:
        page = open_page(ctx, site_url, "partnerships")
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
