import pytest
import build
from conftest import PAGES, baseline_html
from parity import page_facts


@pytest.fixture(scope="module")
def rendered():
    return build.render_all()


@pytest.mark.parametrize("stem", PAGES)
def test_generated_page_matches_baseline(stem, rendered):
    a = page_facts(baseline_html(stem))
    b = page_facts(rendered[stem])
    for key in a:
        assert a[key] == b[key], f"{stem}: {key}"


def test_bizcheck_turnstile_latch_precedes_api_js(rendered):
    html = rendered["BizCheck"]
    assert html.index("__bcTurnstileReady") < html.index("challenges.cloudflare.com/turnstile")


def test_forms_post_to_the_functions_not_formspree(rendered):
    assert '"/api/bizcheck"' in rendered["BizCheck"]
    assert '"/api/contact"' in rendered["Contact"]
    for stem in ("BizCheck", "Contact"):
        assert "formspree.io/f/" not in rendered[stem]


def test_every_page_keeps_its_fonts_link(rendered):
    for stem in PAGES:
        assert "fonts.googleapis.com/css2" in rendered[stem], stem
