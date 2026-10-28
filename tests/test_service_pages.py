"""Sprints 3 to 5: the ten service pages (<pillar>/<slug>.html), built from content/services.json.

Sprint 3 made the four B2B Partnerships pages from existing copy; Sprints 4 and 5 add the three AI Solutions and the
three Digital Presence pages from new copy drafted for the owner to edit.
"""
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
PARTNER_STEMS = [f"partnerships/{slug}" for slug in KEYS]
STEMS = [s["href"][:-5] for p in json.loads((ROOT / "content" / "services.json").read_text(encoding="utf-8"))["pillars"]
         for s in p["services"]]


@pytest.fixture(scope="module")
def pages():
    return build.render_all()


@pytest.fixture(scope="module")
def soups(pages):
    return {stem: BeautifulSoup(pages[stem], "html.parser") for stem in STEMS}


def _text(el) -> str:
    return re.sub(r"\s+", " ", el.get_text(" ", strip=True))


def _pillar(stem: str = "partnerships/x"):
    """The pillar a service page belongs to (by its folder)."""
    return next(p for p in build.load_services()["pillars"] if p["stem"] == stem.split("/")[0])


def test_there_are_ten_service_pages_in_three_folders():
    assert len(STEMS) == 10 and STEMS[:4] == PARTNER_STEMS
    assert {s.split("/")[0] for s in STEMS} == {"partnerships", "ai-solutions", "digital-presence"}


def test_root_prefix_is_empty_at_the_root_and_one_level_up_in_a_folder():
    assert build.root_for("index") == "" and build.root_for("partnerships") == ""
    assert build.root_for("partnerships/channel-strategy") == "../"
    assert build._root_url("Contact.html", "../") == "../Contact.html"
    assert build._root_url("mailto:hello@ayinadvisors.com", "../") == "mailto:hello@ayinadvisors.com"
    assert build._root_url("https://ayinadvisors.com/", "../") == "https://ayinadvisors.com/"
    assert build._root_url("#main", "../") == "#main"
    assert build._root_url("Contact.html", "") == "Contact.html"


@pytest.mark.parametrize("stem", PARTNER_STEMS)
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
    pillar = _pillar(stem)
    svc = next(s for s in pillar["services"] if f"{pillar['stem']}/{s['slug']}" == stem)
    assert page["title"] == f"{svc['name']} - AYiN Advisors" and soup.title.string == page["title"]
    assert page["canonical"] == f"https://ayinadvisors.com/{stem}"
    assert soup.select_one('link[rel="canonical"]')["href"] == page["canonical"]
    assert 120 <= len(page["description"]) <= 160, len(page["description"])
    assert "—" not in pages[stem] and "–" not in pages[stem]
    assert page["sitemap"]["priority"] == "0.7"
    assert len(soup.find_all("h1")) == 1 and _text(soup.h1) == svc["name"]
    crumb = soup.select_one("header.pagehead .eyebrow a")
    assert crumb["href"] == f"../{pillar['stem']}" and _text(crumb) == pillar["name"]
    assert _text(soup.select_one("header.pagehead .lead")) == svc["summary"]
    assert lint_page(stem, pages[stem]) == []


@pytest.mark.parametrize("stem", STEMS)
def test_links_to_the_other_three_services_the_pillar_and_the_cta(soups, stem):
    soup = soups[stem]
    own = stem.split("/")[1]
    pillar = _pillar(stem)
    others = [s for s in pillar["services"] if s["slug"] != own]
    more = soup.select_one("section#more")
    assert _text(more.h2) == f"Also in {pillar['name']}"
    assert [(a["href"], _text(a)) for a in more.select("ul a")] == [(build.clean_href("../" + s["href"]), s["name"]) for s in others]
    back = more.select_one("p.back-link a")
    assert back["href"] == f"../{pillar['stem']}" and _text(back) == f"Back to {pillar['name']}"
    cta = soup.select_one("section.cta")
    assert _text(cta.h2) == pillar["cta"]["heading"] and cta.select_one("a.btn")["href"] == f"../Contact?practice={pillar['stem']}"
    assert [s.get("id") for s in soup.select("main > section")] == ["detail", "more", None]


@pytest.mark.parametrize("stem", STEMS)
def test_every_asset_and_link_resolves_from_the_subfolder(pages, stem):
    html = pages[stem]
    for needle in ('href="../assets/theme.css"', 'href="../assets/styles.css"', 'src="../assets/site.js"',
                   'src="../assets/motion.js"', 'href="../favicon.svg"', 'href="/"', 'href="../Services"',
                   'href="../About"', 'href="../Contact"', 'href="mailto:hello@ayinadvisors.com"'):
        assert needle in html, needle
    soup = BeautifulSoup(html, "html.parser")
    for el, attr in [(e, "href") for e in soup.find_all(["a", "link"], href=True)] + [(e, "src") for e in soup.find_all("script", src=True)]:
        v = el[attr]
        assert v == "/" or v.startswith(("../", "#", "mailto:", "https://", "http://")), v  # "/" is the home page


@pytest.mark.parametrize("stem", STEMS[4:])
def test_a_new_service_page_shows_its_drafted_detail(soups, stem):
    """Sprints 4 and 5: the detail block renders the tag, paragraph and six deliverables from services.json, numbered
    by the service's place in its practice."""
    pillar = _pillar(stem)
    svc = next(s for s in pillar["services"] if f"{pillar['stem']}/{s['slug']}" == stem)
    art = soups[stem].select_one("article.svc-detail")
    assert _text(art.select_one(".tag")) == svc["detail"]["tag"]
    assert _text(art.select_one(".sd-body p")) == svc["detail"]["text"]
    assert [_text(li) for li in art.select(".deliverables li")] == svc["detail"]["deliverables"]
    assert art.select_one(".sd-num")["data-n"] == "%02d" % (pillar["services"].index(svc) + 1)


def test_the_pillar_pages_link_their_services_and_the_root_pages_are_unprefixed(pages):
    for p in build.load_services()["pillars"]:
        for s in p["services"]:
            assert f'href="{build.clean_href(s["href"])}"' in pages[p["stem"]], s["slug"]
        assert 'href="../' not in pages[p["stem"]]
    assert 'href="../' not in pages["index"]


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


@pytest.mark.parametrize("stem", STEMS)
def test_the_other_services_grid_has_one_column_per_card(soups, stem):
    """A practice with three services leaves two cards under "Also in": the grid gets two columns, not an empty third
    whose top border runs on past the cards (seen on the Sprint 4 and 5 preview), and folds to one column on a phone."""
    ul = soups[stem].select_one("section#more ul.ps-list")
    n = len(ul.find_all("li", recursive=False))
    assert f"ps-{n}" in ul["class"], ul["class"]
    if n == 2:
        head = str(soups[stem].head)
        assert ".ps-list.ps-2 { grid-template-columns: repeat(2, 1fr); }" in head
        assert ".ps-list, .ps-list.ps-2 { grid-template-columns: 1fr; }" in head
