"""Sprint 6: the 404 redesign, the last page of the services restructure.

Pinned deltas from the old 404: the Primetime headline, a link to each practice, the shared footer, and root-absolute
paths. Cloudflare Pages serves 404.html for a missing URL at any depth, so a relative "assets/styles.css" would break
on /partnerships/no-such-page; every site path on the page starts with "/".
"""
import re

import pytest
from bs4 import BeautifulSoup

import build


@pytest.fixture(scope="module")
def html():
    return build.render_all()["404"]


@pytest.fixture(scope="module")
def soup(html):
    return BeautifulSoup(html, "html.parser")


def _text(el) -> str:
    return re.sub(r"\s+", " ", el.get_text(" ", strip=True))


def test_the_page_leads_with_the_primetime_line(soup):
    assert len(soup.find_all("h1")) == 1
    assert _text(soup.h1) == "You've found a page that's not ready for Primetime."
    assert _text(soup.select_one("main .code")) == "404"


def test_it_routes_home_to_a_consultation_and_to_each_practice(soup):
    actions = [(a["href"], _text(a)) for a in soup.select(".nf-actions a")]
    assert actions == [("/", "Back to Home →"), ("/Contact", "Book a Consultation")]
    routes = soup.select_one("nav.nf-routes")
    assert routes["aria-label"] == "Practices"
    want = [(f"/{p['stem']}", p["name"]) for p in build.load_services()["pillars"]]
    assert [(a["href"], _text(a)) for a in routes.select("a")] == want


def test_it_carries_the_footer(soup):
    assert soup.select_one("footer.footer") is not None


def test_every_site_path_starts_at_the_root(soup):
    """No relative site path: each one works whatever folder the missing URL was in."""
    refs = [e["href"] for e in soup.find_all(["a", "link"], href=True)] + [e["src"] for e in soup.find_all("script", src=True)]
    assert refs
    for v in refs:
        assert v.startswith(("/", "#", "https://", "mailto:")), v
    assert build.page_root("404") == "/" and build.page_root("index") == "" and build.page_root("partnerships/channel-strategy") == "../"


def test_it_stays_out_of_search(soup):
    page = build.load_site()["pages"]["404"]
    assert soup.select_one('meta[name="robots"]')["content"] == "noindex"
    assert soup.select_one('link[rel="canonical"]') is None and "canonical" not in page and "sitemap" not in page


def test_no_em_dashes_or_current_nav_link(html, soup):
    assert "—" not in html and "–" not in html
    assert not soup.select("nav a[aria-current]")
