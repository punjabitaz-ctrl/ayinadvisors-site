"""Sprint 3: the four B2B Partnerships service pages (partnerships/<slug>.html), built from content/services.json."""
import json
import re

import pytest
from bs4 import BeautifulSoup

import build
from conftest import ROOT
from test_a11y_static import lint_page

FIXTURE = json.loads((ROOT / "tests" / "fixtures" / "partnerships_four_services.json").read_text(encoding="utf-8"))
KEYS = {"market-entry-research": "research", "channel-strategy": "channel", "partner-introductions": "introductions",
        "regional-expansion": "expansion"}
STEMS = [f"partnerships/{slug}" for slug in KEYS]


@pytest.fixture(scope="module")
def pages():
    return build.render_all()


@pytest.fixture(scope="module")
def soups(pages):
    return {stem: BeautifulSoup(pages[stem], "html.parser") for stem in STEMS}


def _text(el) -> str:
    return re.sub(r"\s+", " ", el.get_text(" ", strip=True))


def _pillar():
    return build.load_services()["pillars"][0]


def test_root_prefix_is_empty_at_the_root_and_one_level_up_in_a_folder():
    assert build.root_for("index") == "" and build.root_for("partnerships") == ""
    assert build.root_for("partnerships/channel-strategy") == "../"
    assert build._root_url("Contact.html", "../") == "../Contact.html"
    assert build._root_url("mailto:hello@ayinadvisors.com", "../") == "mailto:hello@ayinadvisors.com"
    assert build._root_url("https://ayinadvisors.com/", "../") == "https://ayinadvisors.com/"
    assert build._root_url("#main", "../") == "#main"
    assert build._root_url("Contact.html", "") == "Contact.html"


@pytest.mark.parametrize("stem", STEMS)
def test_the_page_carries_the_services_existing_text_verbatim(soups, stem):
    """The fixture (the four blocks as they stood on the pillar page) is the oracle: same tag, paragraph and deliverables."""
    raw = BeautifulSoup(FIXTURE[KEYS[stem.split("/")[1]]], "html.parser")
    art = soups[stem].select_one("article.svc-detail")
    assert _text(art.select_one(".tag")) == _text(raw.select_one(".tag"))
    assert _text(art.select_one(".sd-body p")) == _text(raw.select_one(".sd-body p"))
    assert [_text(li) for li in art.select(".deliverables li")] == [_text(li) for li in raw.select(".deliverables li")]
    assert art.select_one(".sd-num")["data-n"] == raw.select_one(".sd-num")["data-n"]
    assert _text(soups[stem].h1) == _text(raw.h2)


@pytest.mark.parametrize("stem", STEMS)
def test_head_meta_and_breadcrumb(pages, soups, stem):
    page = build.load_site()["pages"][stem]
    soup = soups[stem]
    svc = next(s for s in _pillar()["services"] if f"partnerships/{s['slug']}" == stem)
    assert page["title"] == f"{svc['name']} - AYiN Advisors" and soup.title.string == page["title"]
    assert page["canonical"] == f"https://ayinadvisors.com/{stem}.html"
    assert soup.select_one('link[rel="canonical"]')["href"] == page["canonical"]
    assert 120 <= len(page["description"]) <= 160, len(page["description"])
    assert "—" not in pages[stem] and "–" not in pages[stem]
    assert page["sitemap"]["priority"] == "0.7"
    assert len(soup.find_all("h1")) == 1 and _text(soup.h1) == svc["name"]
    crumb = soup.select_one("header.pagehead .eyebrow a")
    assert crumb["href"] == "../partnerships.html" and _text(crumb) == "B2B Partnerships"
    assert _text(soup.select_one("header.pagehead .lead")) == svc["summary"]
    assert lint_page(stem, pages[stem]) == []


@pytest.mark.parametrize("stem", STEMS)
def test_links_to_the_other_three_services_the_pillar_and_the_cta(soups, stem):
    soup = soups[stem]
    own = stem.split("/")[1]
    others = [s for s in _pillar()["services"] if s["slug"] != own]
    more = soup.select_one("section#more")
    assert _text(more.h2) == "Also in B2B Partnerships"
    assert [(a["href"], _text(a)) for a in more.select("ul a")] == [("../" + s["href"], s["name"]) for s in others]
    back = more.select_one("p.back-link a")
    assert back["href"] == "../partnerships.html" and _text(back) == "Back to B2B Partnerships"
    cta = soup.select_one("section.cta")
    assert _text(cta.h2) == _pillar()["cta"]["heading"] and cta.select_one("a.btn")["href"] == "../Contact.html"
    assert [s.get("id") for s in soup.select("main > section")] == ["detail", "more", None]


@pytest.mark.parametrize("stem", STEMS)
def test_every_asset_and_link_resolves_from_the_subfolder(pages, stem):
    html = pages[stem]
    for needle in ('href="../assets/theme.css"', 'href="../assets/styles.css"', 'src="../assets/site.js"',
                   'src="../assets/motion.js"', 'href="../favicon.svg"', 'href="../index.html"', 'href="../Services.html"',
                   'href="../About.html"', 'href="../Contact.html"', 'href="mailto:hello@ayinadvisors.com"'):
        assert needle in html, needle
    soup = BeautifulSoup(html, "html.parser")
    for el, attr in [(e, "href") for e in soup.find_all(["a", "link"], href=True)] + [(e, "src") for e in soup.find_all("script", src=True)]:
        v = el[attr]
        assert v.startswith(("../", "#", "mailto:", "https://", "http://", "market", "channel", "partner", "regional")), v


def test_the_pillar_page_links_the_live_services_and_the_root_pages_are_unprefixed(pages):
    assert 'href="partnerships/market-entry-research.html"' in pages["partnerships"]
    assert 'href="../' not in pages["partnerships"] and 'href="../' not in pages["index"]


def test_image_slots_get_the_root_prefix_on_a_subfolder_page():
    html = '<image-slot slug="us-night" sizes="100vw"></image-slot>'
    assert 'src="assets/img/us-night-' in build.expand_image_slots(html)
    sub = build.expand_image_slots(html, "../")
    assert 'src="../assets/img/us-night-' in sub and 'srcset="../assets/img/us-night-' in sub


def test_build_check_sees_a_stale_subfolder_page(sandbox):
    assert build.check() == []
    p = sandbox / "partnerships" / "channel-strategy.html"
    p.write_text(p.read_text(encoding="utf-8") + "<!-- stale -->", encoding="utf-8")
    assert build.check() == ["partnerships/channel-strategy.html"]
