import pytest
import build
from conftest import PAGES, baseline_html
from parity import page_facts

# The ONE deliberate visible change in this sprint: five pages adopt BizCheck's footer.
# Everything else must be unchanged.
FOOTER_UNIFIED = ["index", "About", "Services", "Projects", "Contact"]
FOOTER_ADDED = {("BizCheck.html", "BizCheck"), ("BizCheck.html", "Submit a BizCheck")}
FOOTER_REMOVED = {("Contact.html", "Request a market brief")}


@pytest.fixture(scope="module")
def rendered():
    return build.render_all()


@pytest.mark.parametrize("stem", PAGES)
def test_generated_page_matches_baseline(stem, rendered):
    a = page_facts(baseline_html(stem))
    b = page_facts(rendered[stem])
    ignore = {"footer_links", "footer_text"} if stem in FOOTER_UNIFIED else set()
    for key in a:
        if key in ignore:
            continue
        assert a[key] == b[key], f"{stem}: {key}\n  baseline={a[key]!r}\n  built   ={b[key]!r}"


@pytest.mark.parametrize("stem", FOOTER_UNIFIED)
def test_footer_delta_is_exactly_the_agreed_links(stem, rendered):
    a = page_facts(baseline_html(stem))["footer_links"]
    b = page_facts(rendered[stem])["footer_links"]
    assert set(b) - set(a) == FOOTER_ADDED
    assert set(a) - set(b) == FOOTER_REMOVED
    assert b == page_facts(baseline_html("BizCheck"))["footer_links"]


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
