"""The consultation form serves all three practices, not only B2B Partnerships.

Site review (2026-10-27): the form asked about "your US ambitions" and offered only the four Partnerships services, so
an AI Solutions or Digital Presence prospect had nothing to pick. It now offers one chip per practice plus "Not sure
yet", and each practice page's Book a Consultation button opens it with that practice picked (?practice=<stem>).
"""
import re

import pytest
from bs4 import BeautifulSoup

import build


@pytest.fixture(scope="module")
def pages():
    return build.render_all()


@pytest.fixture(scope="module")
def soup(pages):
    return BeautifulSoup(pages["Contact"], "html.parser")


def _pillars():
    return build.load_services()["pillars"]


def test_there_is_one_chip_per_practice_and_a_not_sure_chip(soup):
    chips = soup.select("#chips .chip")
    practices = [c.get("data-practice") for c in chips if c.get("data-practice")]
    assert practices == [p["stem"] for p in _pillars()]
    assert [c["data-v"] for c in chips if c.get("data-practice")] == [p["name"] for p in _pillars()]
    assert chips[-1]["data-v"] == "Not sure yet" and not chips[-1].get("data-practice")
    assert all(c.get("aria-pressed") == "false" for c in chips), "chips start unpressed; the script keeps aria-pressed in step"


def test_the_copy_no_longer_assumes_a_us_market_entry(soup):
    text = re.sub(r"\s+", " ", soup.select_one("main").get_text(" "))
    for partnerships_only in ("US ambitions", "your US goals", "read the market"):
        assert partnerships_only not in text


def test_the_script_picks_the_practice_passed_in_the_url(pages):
    html = pages["Contact"]
    assert 'new URLSearchParams(location.search).get("practice")' in html
    assert 'c.setAttribute("aria-pressed"' in html


@pytest.mark.parametrize("stem", [p["stem"] for p in _pillars()])
def test_each_pillar_and_its_services_book_with_their_practice(pages, stem):
    pillar = next(p for p in _pillars() if p["stem"] == stem)
    for page, href in [(stem, f"Contact.html?practice={stem}")] + [
        (s["href"][:-5], f"../Contact.html?practice={stem}") for s in pillar["services"] if s["status"] == "live"
    ]:
        cta = BeautifulSoup(pages[page], "html.parser").select_one("section.cta a.btn")
        assert cta["href"] == href, page


def test_pages_outside_a_practice_book_without_one(pages):
    for page in ("index", "About", "Services"):
        for a in BeautifulSoup(pages[page], "html.parser").select('main a[href*="Contact.html"]'):
            assert "practice=" not in a["href"], page


def test_bizcheck_promises_the_same_turnaround_as_the_contact_form(pages):
    """Site review (2026-10-28): BizCheck said "Within 48 hours / Business days" in one place and "48 business hours" in
    another. Both now match the contact form's "two business days"."""
    text = re.sub(r"\s+", " ", BeautifulSoup(pages["BizCheck"], "html.parser").select_one("main").get_text(" "))
    assert "48" not in text
    assert text.count("two business days") == 2
