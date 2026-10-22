"""Sprint 2 Task 2: the Services hub and the three pillar pages (structure, headings, verbatim copy, proof band)."""
import json
import re

import pytest
from bs4 import BeautifulSoup

import build
from conftest import ROOT
from test_a11y_static import lint_page

PILLAR_STEMS = ("partnerships", "ai-solutions", "digital-presence")
FIXTURES = ROOT / "tests" / "fixtures"


@pytest.fixture(scope="module")
def pages():
    return build.render_all()


@pytest.fixture(scope="module")
def soups(pages):
    return {stem: BeautifulSoup(html, "html.parser") for stem, html in pages.items()}


@pytest.fixture(scope="module")
def pillars():
    return build.load_services()["pillars"]


def _text(el) -> str:
    return re.sub(r"\s+", " ", el.get_text(" ", strip=True))


# ---------------------------------------------------------------- hub

def test_hub_lists_three_pillars_linking_to_their_pages(soups, pillars):
    cards = soups["Services"].select("main a.svc")
    assert [c["href"] for c in cards] == [f"{p['stem']}.html" for p in pillars]
    for card, p in zip(cards, pillars):
        assert _text(card.h3) == p["name"]
        assert p["hub_line"] in _text(card)
        # every service of the practice is named on its card, as a plain list item
        names = [_text(li) for li in card.select("ul li")]
        assert names == [s["name"] for s in p["services"]], p["slug"]
        assert not card.select("a"), "a card is one link; no link inside a link"
        assert "Explore" in _text(card.select_one(".svc-arrow"))


def test_hub_cards_have_three_distinct_iris_icons(soups):
    icons = [str(c.select_one("svg.iris-ico")) for c in soups["Services"].select("main a.svc")]
    assert len(icons) == 3 and len(set(icons)) == 3
    for card in soups["Services"].select("main a.svc"):
        svg = card.select_one("svg.iris-ico")
        assert svg.get("aria-hidden") == "true" and svg.get("focusable") == "false" and not svg.select("title, desc")
        assert "asm-card" in card["class"] and "tilt3d" in card["class"] and card.has_attr("data-tilt")


def test_hub_has_the_fit_together_band_and_one_gold_cta(soups):
    soup = soups["Services"]
    fit = soup.select_one("section#fit")
    assert fit is not None and "surface-alt" in fit["class"]
    assert "fit together" in _text(fit.select_one(".eyebrow")).lower()
    assert len(fit.select("p")) >= 2
    assert len(soup.select("section.cta.surface-accent")) == 1


# ---------------------------------------------------------------- pillar pages

@pytest.mark.parametrize("stem", PILLAR_STEMS)
def test_each_pillar_lists_its_services_unlinked(soups, pillars, stem):
    soup = soups[stem]
    p = next(x for x in pillars if x["stem"] == stem)
    cards = soup.select("#what ul.ps-list > li")
    assert [_text(c.h3) for c in cards] == [s["name"] for s in p["services"]]
    assert [_text(c.p) for c in cards] == [s["summary"] for s in p["services"]]
    for c in cards:
        assert not c.select("a, button, [href], .svc-arrow, .btn-arrow"), "informative cards: no links, no arrows"
        assert "asm-card" in c["class"] and "tilt3d" in c["class"] and c.has_attr("data-tilt")
    assert "coming soon" not in soup.get_text(" ").lower()
    # the only links in the body are the CTA and in-page chrome; none lead to a page that does not exist
    for a in soup.select("main a[href]"):
        assert a["href"] in ("Contact.html",), a["href"]


@pytest.mark.parametrize("stem", PILLAR_STEMS)
def test_pillar_page_head_names_the_buyer_and_leads_with_the_headline(soups, pillars, stem):
    p = next(x for x in pillars if x["stem"] == stem)
    head = soups[stem].select_one("header.pagehead")
    assert _text(head.select_one(".eyebrow")) == p["buyer"]
    assert _text(head.h1) == p["tagline"]
    assert _text(head.select_one(".lead")) == p["lead"]


@pytest.mark.parametrize("stem", PILLAR_STEMS)
def test_pillar_page_bands_in_order(soups, pillars, stem):
    soup = soups[stem]
    p = next(x for x in pillars if x["stem"] == stem)
    got = [s.get("id") for s in soup.select("main > section")]
    # the partnerships detail band is one section holding the four #research..#expansion articles
    want = ["what", "detail", "why", "process", "who", None] if stem == "partnerships" else ["what", "process", "who", None]
    assert got == want
    what = soup.select_one("#what")
    assert _text(what.select_one(".eyebrow")) == p["name"]
    assert _text(what.h2) == p["do_heading"]
    who = soup.select_one("#who")
    assert _text(who.select_one(".eyebrow")) == "Who it is for"
    assert _text(who.h2) == p["who"]["heading"]
    items = who.select(".principle")
    assert [(_text(i.h3), _text(i.p)) for i in items] == [(x["title"], x["text"]) for x in p["who"]["items"]]


@pytest.mark.parametrize("stem", PILLAR_STEMS)
def test_pillar_cta_copy_is_per_pillar_and_not_stale_market_entry_copy(soups, pillars, stem):
    p = next(x for x in pillars if x["stem"] == stem)
    cta = soups[stem].select_one("section.cta")
    assert _text(cta.select_one(".eyebrow")) == p["cta"]["eyebrow"]
    assert _text(cta.h2) == p["cta"]["heading"]
    assert _text(cta.select_one(".lead")) == p["cta"]["text"]
    assert "Contact.html" in cta.select_one("a.btn")["href"]
    if stem != "partnerships":
        assert "market read" not in _text(cta).lower() and "market" not in _text(cta).lower()


def test_the_three_pillar_ctas_differ(pillars):
    texts = {p["cta"]["text"] for p in pillars} | {p["cta"]["heading"] for p in pillars}
    assert len(texts) == 6


@pytest.mark.parametrize("stem", PILLAR_STEMS)
def test_how_we_work_is_the_generic_process(soups, pillars, stem):
    proc = soups[stem].select_one("#process")
    data = build.process_for(next(x for x in pillars if x["stem"] == stem))
    assert "assemble" in proc["class"] and proc.has_attr("data-assemble")
    assert _text(proc.select_one(".eyebrow")) == data["eyebrow"] == "How we work"
    steps = proc.select(".proc-step")
    assert [(_text(s.h3), _text(s.p)) for s in steps] == [(x["name"], x["text"]) for x in data["steps"]]
    assert [_text(s.select_one(".pn")) for s in steps] == ["Step 01", "Step 02", "Step 03", "Step 04"]
    assert all("asm-rise" in s["class"] for s in steps) and proc.select_one(".proc-line .asm-grow")
    # four markers growing from one dot to four rings
    assert [len(s.select("svg.step-iris circle")) for s in steps] == [1, 2, 3, 4]
    # the engagement process is generic: it names no one practice
    text = _text(proc).lower()
    for word in ("us market", "united states", "website", "automation"):
        assert word not in text


# ---------------------------------------------------------------- headings (static lint) and landmarks

@pytest.mark.parametrize("stem", ("Services",) + PILLAR_STEMS)
def test_template_pages_pass_the_static_lint_with_one_h1(pages, soups, stem):
    assert lint_page(stem, pages[stem]) == []
    assert len(soups[stem].find_all("h1")) == 1


def _outline(soup):
    return [(h.name, _text(h)) for h in soup.select("main h2, main h3")] + [("h1", _text(soup.h1))]


def test_hub_headings(soups, pillars):
    soup = soups["Services"]
    assert [(h.name, _text(h)) for h in soup.select("main h2")] == [
        ("h2", _text(soup.select_one("#practices h2"))), ("h2", _text(soup.select_one("#fit h2"))), ("h2", _text(soup.select_one("section.cta h2")))]
    assert [_text(h) for h in soup.select("#practices h3")] == [p["name"] for p in pillars]


@pytest.mark.parametrize("stem", ("ai-solutions", "digital-presence"))
def test_ai_and_digital_heading_outline(soups, pillars, stem):
    soup = soups[stem]
    p = next(x for x in pillars if x["stem"] == stem)
    proc = build.process_for(p)
    got = [(h.name, _text(h)) for h in soup.select("main h2, main h3")]
    want = [("h2", p["do_heading"])] + [("h3", s["name"]) for s in p["services"]] \
        + [("h2", proc["heading"])] + [("h3", s["name"]) for s in proc["steps"]] \
        + [("h2", p["who"]["heading"])] + [("h3", i["title"]) for i in p["who"]["items"]] + [("h2", p["cta"]["heading"])]
    assert got == want


def test_partnerships_heading_outline(soups, pillars):
    p = pillars[0]
    proc = build.process_for(p)
    got = [(h.name, _text(h)) for h in soups["partnerships"].select("main h2, main h3")]
    names = [s["name"] for s in p["services"]]
    assert got[0] == ("h2", p["do_heading"]) and [g for g in got[1:5]] == [("h3", n) for n in names]
    # then the four verbatim blocks (h2 each), the moved proof band, the process, who it is for, the CTA
    detail = [g for g in got if g[0] == "h2"]
    titles = [t for _, t in detail]
    assert titles[1:5] == ["US Market Entry Research", "Channel Strategy & Enablement", "B2B Partner Introductions", "Regional Expansion · Canada & LATAM"]
    assert titles[5] == "The largest opportunity is also the hardest to read."
    assert titles[6:] == [proc["heading"], p["who"]["heading"], p["cta"]["heading"]]


# ---------------------------------------------------------------- Partnerships: verbatim services and the proof band

def test_partnerships_keeps_the_four_services_verbatim(pages):
    """Each of the four detail blocks is byte-identical to the one on the Services page at the base commit."""
    base = json.loads((FIXTURES / "partnerships_four_services.json").read_text(encoding="utf-8"))
    assert list(base) == ["research", "channel", "introductions", "expansion"]
    html = pages["partnerships"]
    positions = []
    for key, raw in base.items():
        assert html.count(raw) == 1, f"{key}: block changed or missing"
        positions.append(html.index(raw))
    assert positions == sorted(positions), "the four blocks keep their order"
    soup = BeautifulSoup(html, "html.parser")
    for key, raw in base.items():
        assert _text(soup.select_one(f"article#{key}")) == _text(BeautifulSoup(raw, "html.parser"))


def test_partnerships_has_the_us_proof_band(soups):
    soup = soups["partnerships"]
    band = soup.select_one("section#why")
    assert band is not None and ({"surface-page", "surface-alt"} & set(band["class"]))
    globe = band.select_one(".globe-stage svg")
    assert globe is not None and globe.get("role") == "img" and "United States" in globe.get("aria-label", "")
    assert len(globe.select(".arc")) == 3 and globe.select_one(".dest")
    photo = band.select_one("figure.photo-card picture img")
    assert photo is not None and "us-night" in photo["src"] and photo.get("alt")
    stats = band.select(".why-stat")
    assert [(s.select_one("[data-count]")["data-count"], s.select_one("[data-count]").get("data-prefix", ""),
             s.select_one("[data-count]").get("data-suffix", "")) for s in stats] == [("24", "$", "T"), ("50", "", ""), ("70", "", "%"), ("3", "", "x")]
    assert [_text(s.select_one(".l")) for s in stats] == [
        "US consumer + B2B economy", "State markets, one entry strategy", "Of B2B revenue flows through partners",
        "Faster scale with the right channel"]
    assert "The largest opportunity" in _text(band.h2)
    eyebrow = band.select_one(".eyebrow")
    assert eyebrow.select_one("svg.iris-mark") and not band.select(".sec-index")


# ---------------------------------------------------------------- meta

def test_services_and_partnerships_meta_match_their_roles():
    pages = build.load_site()["pages"]
    hub, part = pages["Services"], pages["partnerships"]
    d = hub["description"].lower()
    assert "ai" in d and "digital" in d and "partnership" in d and "market entry research" not in d
    assert hub["title"] == "Services - AYiN Advisors"
    p = part["description"].lower()
    assert "b2b partnerships" in p and "international" in p and "market entry" in p
    for stem, page in pages.items():
        if page.get("template"):
            assert page["title"].endswith("- AYiN Advisors") and page["canonical"] == f"https://ayinadvisors.com/{stem}.html"


def test_og_and_twitter_meta_follow_the_page(pages):
    for stem in ("Services",) + PILLAR_STEMS:
        page = build.load_site()["pages"][stem]
        soup = BeautifulSoup(pages[stem], "html.parser")
        for sel in ('meta[property="og:title"]', 'meta[name="twitter:title"]'):
            assert soup.select_one(sel)["content"] == page["title"]
        for sel in ('meta[property="og:description"]', 'meta[name="twitter:description"]', 'meta[name="description"]'):
            assert soup.select_one(sel)["content"] == page["description"]


# ---------------------------------------------------------------- CSS hygiene

def _head_css(stem) -> str:
    return build.page_parts(stem)[1]


@pytest.mark.parametrize("stem", ("Services", "ai-solutions", "digital-presence"))
def test_no_dead_detail_css_outside_partnerships(stem):
    css = _head_css(stem)
    for dead in ("svc-detail", "deliverables", "sd-num", "why-grid", "globe-stage"):
        assert dead not in css, f"{stem}: unused rule for .{dead}"


def test_partnerships_head_keeps_the_detail_and_proof_css():
    css = _head_css("partnerships")
    for needed in ("svc-detail", "deliverables", "sd-num", "why-grid", "globe-stage", "proc-grid", "principle"):
        assert needed in css


# ---------------------------------------------------------------- copy keeps to what the owner said or the site already says

def test_retainer_and_step_back_promises_are_only_on_partnerships(soups):
    """"No open-ended retainers" and the hand-over-and-step-back line come from the market-entry copy; AI and Digital work can be ongoing."""
    for stem in ("ai-solutions", "digital-presence", "Services"):
        text = _text(soups[stem].select_one("main")).lower()
        assert "retainer" not in text and "step back" not in text and "without us" not in text, stem
    part = _text(soups["partnerships"].select_one("#process")).lower()
    assert "no open-ended retainers" in part and "step back" in part
    ai = _text(soups["ai-solutions"].select_one("#process"))
    assert "document what we built" not in ai
    dig = _text(soups["digital-presence"].select_one("#process"))
    assert "We hand over what we built and agree what happens next." in dig


UNPROMISED = (
    "led by senior", "senior attention", "senior-led", "one brief", "search, email", "learning from what works",
    "fast, accessible", "clear, fast", "plain code", "already sells at home", "gets you to market", "leaner operation",
    "presence that works", "meet you where you are", "we'll", "what is worth building",
)


@pytest.mark.parametrize("stem", ("Services",) + PILLAR_STEMS)
def test_no_promise_the_owner_never_gave(soups, pages, stem):
    text = _text(soups[stem].select_one("main")).lower() + " " + pages[stem].lower().split("<title>")[1].split("</title>")[0]
    for phrase in UNPROMISED:
        assert phrase not in text, f"{stem}: {phrase!r}"


def test_ai_page_states_its_stance_once(soups):
    text = _text(soups["ai-solutions"].select_one("main"))
    assert text.count("We tell you which") == 1
    assert "worth building" not in text


def test_hub_eyebrow_is_plural_and_the_fit_band_defers_sequencing(soups):
    assert _text(soups["Services"].select_one("header.pagehead .eyebrow")) == "Our Practices"
    assert "Tell us about both and we will say how to sequence them." in _text(soups["Services"].select_one("#fit"))


def test_meta_descriptions_are_search_snippet_length():
    pages = build.load_site()["pages"]
    for stem in ("Services",) + PILLAR_STEMS:
        n = len(pages[stem]["description"])
        assert 120 <= n <= 160, f"{stem}: description is {n} characters"
