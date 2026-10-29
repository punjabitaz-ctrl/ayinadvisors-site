"""AI search review (2026-10-28): what crawlers that read the raw HTML, AI tools and feed readers get from the site."""
import json
import re
import xml.etree.ElementTree as ET

from bs4 import BeautifulSoup

import build
from conftest import ROOT

SITE = build.load_site()
PAGES = SITE["pages"]
CANONICALS = {p["canonical"] for p in PAGES.values() if "canonical" in p}


def _soup(stem: str) -> BeautifulSoup:
    return BeautifulSoup((ROOT / f"{stem}.html").read_text(encoding="utf-8"), "html.parser")


def _ld(stem: str) -> list[dict]:
    out = []
    for tag in _soup(stem).select('script[type="application/ld+json"]'):
        data = json.loads(tag.string)
        out += data.get("@graph", [data])
    return out


def _one(stem: str, kind: str) -> dict:
    found = [d for d in _ld(stem) if d.get("@type") == kind]
    assert len(found) == 1, (stem, kind, found)
    return found[0]


# ---------------------------------------------------------------- stats readable without JavaScript
def test_every_counter_ships_its_final_value_in_the_html():
    seen = 0
    for stem in PAGES:
        for el in _soup(stem).select("[data-count]"):
            want = el.get("data-prefix", "") + el["data-count"] + el.get("data-suffix", "")
            assert el.get_text() == want, (stem, str(el))
            seen += 1
    assert seen == 4, "Home 3, About 3 and 100%, Partnerships 4"


def test_counters_reset_to_zero_only_when_they_will_animate():
    js = (ROOT / "assets" / "site.js").read_text(encoding="utf-8")
    assert "if (counters.length && !reduce)" in js and "(0).toFixed(dec)" in js


# ---------------------------------------------------------------- llms.txt
def test_llms_txt_is_current_and_links_only_real_pages():
    text = (ROOT / "llms.txt").read_text(encoding="utf-8")
    assert text == build.render_llms()
    assert text.startswith("# AYiN Advisors\n\n> ")
    links = re.findall(r"\]\((https://[^)]+)\)", text)
    assert links and set(links) <= CANONICALS
    for pillar in build.load_services()["pillars"]:
        assert PAGES[pillar["stem"]]["canonical"] in links
        for svc in pillar["services"]:
            assert PAGES[svc["href"][: -len(".html")]]["canonical"] in links
    for post in build.blog_posts():
        assert PAGES[post["stem"]]["canonical"] in links
    assert ".html" not in text and "—" not in text


# ---------------------------------------------------------------- RSS
def test_feed_lists_every_post_at_its_canonical_address():
    raw = (ROOT / "blog" / "feed.xml").read_text(encoding="utf-8")
    assert raw == build.render_feed()
    channel = ET.fromstring(raw).find("channel")
    items = channel.findall("item")
    posts = build.blog_posts()
    assert [i.findtext("link") for i in items] == [PAGES[p["stem"]]["canonical"] for p in posts]
    assert [i.findtext("title") for i in items] == [p["question"] for p in posts]
    assert channel.find("{http://www.w3.org/2005/Atom}link").get("href") == build.FEED_URL


def test_every_indexable_page_points_to_the_feed():
    for stem, page in PAGES.items():
        if "canonical" not in page:
            continue
        alt = _soup(stem).select('link[rel="alternate"][type="application/rss+xml"]')
        assert len(alt) == 1 and alt[0]["href"] == build.FEED_URL, stem


def test_generated_text_files_are_served_with_a_charset():
    headers = (ROOT / "_headers").read_text(encoding="utf-8")
    assert "/llms.txt\n  Content-Type: text/plain; charset=utf-8" in headers
    assert "/blog/feed.xml\n  Content-Type: application/rss+xml; charset=utf-8" in headers


# ---------------------------------------------------------------- structured data
def test_organization_names_its_logo_topics_and_contact():
    org = _one("index", "Organization")
    assert org["logo"] == f"{build.SITE_URL}/apple-touch-icon.png" and (ROOT / "apple-touch-icon.png").exists()
    names = [p["name"] for p in build.load_services()["pillars"]]
    assert org["knowsAbout"][:3] == names
    assert org["contactPoint"]["email"] == "hello@ayinadvisors.com"
    assert org["contactPoint"]["url"] == PAGES["Contact"]["canonical"]
    person = _one("index", "Person")
    assert person["knowsAbout"][0] == "B2B Partnerships"


def test_only_the_partnerships_practice_states_where_it_works():
    assert [a["name"] for a in _one("partnerships", "Service")["areaServed"]] == ["United States", "Canada", "Latin America"]
    assert [a["name"] for a in _one("partnerships/regional-expansion", "Service")["areaServed"]] == ["Canada", "Latin America"]
    assert [a["name"] for a in _one("partnerships/channel-strategy", "Service")["areaServed"]] == ["United States"]
    for stem in ("ai-solutions", "ai-solutions/workflow-automation", "digital-presence", "digital-presence/websites"):
        assert "areaServed" not in _one(stem, "Service"), stem


def test_pillar_services_list_their_offers_at_real_addresses():
    for pillar in build.load_services()["pillars"]:
        offers = _one(pillar["stem"], "Service")["hasOfferCatalog"]["itemListElement"]
        assert [o["itemOffered"]["name"] for o in offers] == [s["name"] for s in pillar["services"]]
        assert {o["itemOffered"]["url"] for o in offers} <= CANONICALS
        assert _one(pillar["stem"], "Service")["audience"]["name"] == pillar["buyer"]


def test_projects_structured_data_matches_the_cards_on_the_page():
    page = _one("Projects", "CollectionPage")
    items = [li["item"] for li in page["mainEntity"]["itemListElement"]]
    cards = _soup("Projects").select("article.project-card, article.site-card")
    assert [i["name"] for i in items] == [c.h3.get_text(strip=True) for c in cards]
    assert page["mainEntity"]["numberOfItems"] == len(cards)
    for item, card in zip(items, cards):
        if "site-card" in card["class"]:
            assert item["@type"] == "WebSite" and item["url"] == card.select_one("a.site-link")["href"]
        else:
            assert item["@type"] == "SoftwareApplication" and "url" not in item
        assert item["description"]


def test_contact_is_a_contact_page_about_the_organization():
    page = _one("Contact", "ContactPage")
    assert page["url"] == PAGES["Contact"]["canonical"] and page["about"]["@id"] == build.ORG_ID
