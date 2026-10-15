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


def test_body_rest_nonempty_for_every_page():
    for stem in PAGES:
        assert page_facts(baseline_html(stem))["body_rest"], stem


def test_body_rest_excludes_chrome():
    for stem in PAGES:
        rest = page_facts(baseline_html(stem))["body_rest"]
        assert 'class="nav"' not in rest, stem
        assert "<footer" not in rest, stem


def test_body_rest_differs_between_pages():
    a = page_facts(baseline_html("About"))["body_rest"]
    b = page_facts(baseline_html("Services"))["body_rest"]
    assert a != b


def _edit_in_h1(html, word):
    """Append ZZ to `word` inside the first <h1> only (never <head>, title or meta)."""
    import re
    m = re.search(r"<h1[^>]*>.*?</h1>", html, re.S)
    assert m and word in m.group(0)
    edited = m.group(0).replace(word, word + "ZZ", 1)
    return html[: m.start()] + edited + html[m.end():]


def test_body_rest_tracks_body_copy_not_nav():
    html = baseline_html("About")
    base = page_facts(html)["body_rest"]
    # pick a word of real body copy: first <h1> text
    from bs4 import BeautifulSoup
    h1 = BeautifulSoup(html, "html.parser").find("h1").get_text().split()[0]
    assert h1 in html
    edited = _edit_in_h1(html, h1)
    assert page_facts(edited)["body_rest"] != base
    nav_only = html.replace('<nav class="nav"', '<nav class="nav" data-x="1"', 1)
    assert nav_only != html
    assert page_facts(nav_only)["body_rest"] == base


def test_body_rest_ignores_comments_but_not_copy():
    html = baseline_html("About")
    base = page_facts(html)["body_rest"]
    with_comment = html.replace("<body>", "<body><!-- decorative -->", 1)
    assert with_comment != html
    assert page_facts(with_comment)["body_rest"] == base
    from bs4 import BeautifulSoup
    h1 = BeautifulSoup(html, "html.parser").find("h1").get_text().split()[0]
    assert page_facts(_edit_in_h1(with_comment, h1))["body_rest"] != base
