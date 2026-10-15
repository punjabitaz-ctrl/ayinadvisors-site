from conftest import PAGES, baseline_html
from parity import page_facts


def test_facts_extract_nav_and_footer():
    facts = page_facts(baseline_html("About"))
    assert facts["title"] == "About — AYiN Advisors"
    assert ("BizCheck.html", "BizCheck") in [(h, t) for h, t, _ in facts["nav"]]
    assert facts["has_footer"] is True


def test_404_has_no_footer():
    assert page_facts(baseline_html("404"))["has_footer"] is False


def test_head_keeps_href_first_font_link():
    head = page_facts(baseline_html("About"))["head"]
    fonts = [h for h in head if h[0] == "link"
             and any(k == "href" and "fonts.googleapis.com/css2" in v for k, v in h[1])]
    assert fonts, "About's Google Fonts link must be present in the head facts"


def test_head_excludes_what_base_owns():
    head = page_facts(baseline_html("About"))["head"]
    assert not any(h[0] == "title" for h in head)
    assert not any(h[0] == "link" and ("rel", "canonical") in h[1] for h in head)
    assert any(h[0] == "style" for h in head)


def test_bizcheck_cta_differs_from_about():
    biz = page_facts(baseline_html("BizCheck"))
    about = page_facts(baseline_html("About"))
    assert biz["nav_cta"] == ("#submit", "Submit Your Idea", "btn")
    assert about["nav_cta"] == ("Contact.html", "Book a Consultation", "btn btn-white")
