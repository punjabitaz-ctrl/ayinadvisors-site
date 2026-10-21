"""Sprint 2 Task 3: the homepage speaks to three buyers; the footer, titles and descriptions match."""
import re

import pytest
from bs4 import BeautifulSoup

import build
from conftest import ROOT
from test_services_content import HYPE, PRICE_OFFER

HOME_BODY = ROOT / "templates" / "pages" / "index.body.frag"
PILLAR_STEMS = ("partnerships", "ai-solutions", "digital-presence")
TAGLINE = "Business Solutions for a Digital World"


@pytest.fixture(scope="module")
def pages():
    return build.render_all()


@pytest.fixture(scope="module")
def soups(pages):
    return {stem: BeautifulSoup(html, "html.parser") for stem, html in pages.items()}


@pytest.fixture(scope="module")
def home(soups):
    return soups["index"]


@pytest.fixture(scope="module")
def pillars():
    return build.load_services()["pillars"]


@pytest.fixture(scope="module")
def site():
    return build.load_site()


def _text(el) -> str:
    return re.sub(r"\s+", " ", el.get_text(" ", strip=True))


# ---------------------------------------------------------------- title and description

def test_home_title_and_description_use_the_tagline(site, soups):
    page = site["pages"]["index"]
    assert page["title"] == f"AYiN Advisors — {TAGLINE}"          # page titles keep the em dash site-wide
    assert page["title"].startswith("AYiN Advisors") and page["title"].endswith(TAGLINE)
    d = page["description"]
    assert d.lower().startswith(TAGLINE.lower()), d
    assert 120 <= len(d) <= 160, f"description is {len(d)} characters"
    low = d.lower()
    assert "partnerships" in low and "ai solutions" in low and "digital presence" in low
    assert "us market entry" not in low and "channel activities" not in low
    soup = soups["index"]
    assert soup.title.get_text(strip=True) == page["title"]
    for sel in ('meta[property="og:title"]', 'meta[name="twitter:title"]'):
        assert soup.select_one(sel)["content"] == page["title"]
    for sel in ('meta[property="og:description"]', 'meta[name="twitter:description"]', 'meta[name="description"]'):
        assert soup.select_one(sel)["content"] == page["description"]


def test_about_description_not_us_only(site, soups):
    page = site["pages"]["About"]
    d = page["description"]
    assert not re.search(r"\bUS\b|United States|American", d), d
    assert "three practices" in d.lower()
    assert 120 <= len(d) <= 160, f"description is {len(d)} characters"
    assert "—" not in d
    soup = soups["About"]
    assert soup.select_one('meta[name="description"]')["content"] == d
    for sel in ('meta[property="og:description"]', 'meta[name="twitter:description"]'):
        el = soup.select_one(sel)
        assert el is None or el["content"] == d, "social description must not keep the old US-only text"


# ---------------------------------------------------------------- hero

def test_home_hero_is_the_new_positioning(home):
    hero = home.select_one("header.hero")
    h1 = hero.h1
    assert _text(h1) == "Business solutions for a digital world."
    assert _text(h1.select_one(".italic-accent")) == "digital world."
    assert _text(hero.select_one(".eyebrow")) == "AYiN Advisors"
    lead = _text(hero.select_one(".hero-lead")).lower()
    for part in ("three practices", "partnerships", "international firms entering the us", "ai solutions", "digital presence"):
        assert part in lead, part
    # two CTAs, unchanged
    acts = [(a["href"], _text(a)) for a in hero.select(".hero-actions a")]
    assert acts == [("Contact.html", "Book a Consultation →"), ("Services.html", "Our Services")]


def test_home_hero_stats_keep_only_claims_the_site_already_made(home):
    stats = home.select(".hero-stats .hstat")
    assert len(stats) == 3
    n = [s.select_one(".n") for s in stats]
    label = [_text(s.select_one(".l")) for s in stats]
    # 1: the count of practices (spec decision)
    assert n[0].select_one("[data-count]")["data-count"] == "3" and not n[0].select_one("[data-count]").get("data-suffix", "").strip()
    assert "Practices" in label[0] and "Partnerships" in label[0] and "AI" in label[0] and "Digital" in label[0]
    # 2: the existing 90-day claim, scoped to the Partnerships practice
    assert n[1].select_one("[data-count]")["data-count"] == "90" and n[1].select_one("[data-count]")["data-suffix"] == " Days"
    assert label[1].startswith("Partnerships") and "to first qualified partner" in label[1].lower()
    # 3: no number; the working-style line from About
    assert not n[2].select("[data-count]") and _text(n[2]) == "Founder-led"
    assert label[2] == "Operators, not observers"
    assert "100" not in _text(home.select_one(".hero-stats")), "the old 100% channel-led claim is gone"
    assert "Canada" not in _text(home.select_one(".hero-stats"))


# ---------------------------------------------------------------- the three bands that carry the practices

def test_home_has_three_pillar_cards_linking_to_pillar_pages(home, pillars):
    sec = home.select_one("section#services")
    cards = sec.select("a.svc")
    assert [c["href"] for c in cards] == [f"{p['stem']}.html" for p in pillars] == [
        "partnerships.html", "ai-solutions.html", "digital-presence.html"]
    macro = build.env.get_template("_components.j2").module
    for card, p in zip(cards, pillars):
        assert _text(card.h3) == p["name"]
        assert _text(card.select_one("p")) == p["hub_line"]
        assert "Explore" in _text(card.select_one(".svc-arrow"))
        assert not card.select("a"), "a card is one link; no link inside a link"
        assert "asm-card" in card["class"] and "tilt3d" in card["class"] and card.has_attr("data-tilt")
        # the same iris icon as the hub card
        svg = card.select_one("svg.iris-ico")
        want = BeautifulSoup(str(macro.iris_ico(p["icon"])), "html.parser").svg
        assert str(svg) == str(want), p["slug"]
        assert svg.get("aria-hidden") == "true" and svg.get("focusable") == "false"
    assert len({str(c.select_one("svg.iris-ico")) for c in cards}) == 3
    assert "Services.html" not in {a["href"] for a in sec.select("a")}
    assert "sec-head" in " ".join(sec.select_one(".sec-head")["class"]) and sec.select_one(".sec-head svg.iris-mark") is None
    assert sec.select_one(".sec-head .eyebrow svg.iris-mark") and _text(sec.select_one(".sec-head .eyebrow")) == "What we do"
    hub = build.load_services()["hub"]["choose"]
    assert _text(sec.select_one(".sec-head h2")) == hub["heading"]
    assert _text(sec.select_one(".sec-head p")) == hub["intro"]


def test_home_who_we_work_with_names_the_three_buyers(home, pillars):
    sec = home.select_one("section#who")
    assert sec is not None
    assert _text(sec.select_one(".eyebrow")) == "Who we work with" and sec.select_one(".eyebrow svg.iris-mark")
    assert not sec.select(".sec-index")
    items = sec.select(".principle")
    assert [_text(i.h3) for i in items] == [p["buyer"] for p in pillars]
    assert [_text(i.p) for i in items] == [p["who"]["intro"] for p in pillars]
    assert _text(sec.select_one(".lead")) == build.load_services()["hub"]["fit"]["paragraphs"][0]
    assert len(sec.select("h2")) == 1 and not sec.select("a"), "informative; the cards above carry the links"


def test_home_process_is_the_generic_one(home):
    sec = home.select_one("section#process")
    proc = build.process_for(None)
    assert _text(sec.select_one(".sec-head .eyebrow")) == proc["eyebrow"]
    assert _text(sec.select_one(".sec-head h2")) == proc["heading"]
    assert _text(sec.select_one(".sec-head p")) == proc["intro"]
    steps = sec.select(".proc-step")
    assert [(_text(s.h3), _text(s.p)) for s in steps] == [(s["name"], s["text"]) for s in proc["steps"]]
    assert [_text(s.select_one(".pn")) for s in steps] == [f"Step 0{i}" for i in range(1, 5)]
    assert [len(s.select("svg.step-iris circle")) for s in steps] == [1, 2, 3, 4]
    low = _text(sec).lower()
    for word in ("us market", "united states", "channel", "partners", "retainer", "step back", "without us", "diagnose"):
        assert word not in low, word


def test_home_who_we_are_is_practice_neutral(home):
    sec = home.select_one("section#about")
    eb = sec.select_one(".eyebrow")
    assert _text(eb) == "Who we are" and eb.select_one("svg.iris-mark") and not sec.select(".sec-index")
    low = _text(sec).lower()
    for gone in ("channel first", "on the ground", "north american", "channel is selling", "incentives", "senior attention"):
        assert gone not in low, gone
    names = [_text(h) for h in sec.select(".principle h3")]
    assert names == ["Evidence over theory", "Candid counsel", "Sequenced, not open-ended"]
    assert sec.select_one("a.tlink")["href"] == "About.html"


def test_home_cta_is_practice_neutral(home):
    cta = home.select_one("section.cta")
    low = _text(cta).lower()
    assert "us ambitions" not in low and "us market" not in low and "read the market" not in low
    assert _text(cta.select_one("h2")) == "Tell us what you are trying to do."
    assert "goals" in low and "no obligation, just clarity" in low
    assert cta.select_one("a.btn")["href"] == "Contact.html"


# ---------------------------------------------------------------- Home no longer leads with the US

def test_home_no_longer_leads_with_us_only(home, pages):
    assert "american" not in _text(home.h1).lower()
    assert home.select_one("#why") is None and home.select_one(".globe-stage") is None and home.select_one(".why-stats") is None
    assert "<picture" not in pages["index"], "the US photograph lives on the Partnerships page now"
    assert not home.select("[data-count][data-prefix], .why-stat")
    main = _text(home.select_one("main"))
    for stale in ("Why the US market", "largest opportunity", "US ambitions", "See the American", "crossing the border"):
        assert stale not in main and stale not in _text(home.select_one("header.hero")), stale
    # the US story is still told, once, on the Partnerships page
    assert build.page_parts("partnerships")[0].count("us-night") == 1
    assert (ROOT / "templates" / "partials" / "partnerships-proof.frag").exists()


def test_home_section_order_and_ids(home):
    main = home.select_one("main")
    ids = [s.get("id") for s in main.find_all(True, recursive=False)]
    assert ids == ["letters", "services", "who", "process", "about", None]      # the CTA band has no id
    assert "cta" in main.find_all(True, recursive=False)[-1]["class"]
    # section numbers are gone: iris markers only
    assert not home.select(".sec-index")
    for sel in ("#services .sec-head .eyebrow", "#who .eyebrow", "#process .sec-head .eyebrow", "#about .eyebrow"):
        eb = home.select_one(sel)
        marks = eb.select("svg.iris-mark")
        assert len(marks) == 1, sel
        m = marks[0]
        assert m.get("aria-hidden") == "true" and m.get("focusable") == "false" and not m.select("title, desc")
        assert _text(eb) and not _text(eb)[0].isdigit()
    # assemble hooks stay on the two bands that already had them, nothing else animates without a root
    assert [r["id"] for r in home.select("[data-assemble]")] == ["letters", "services", "process"]
    assert len(home.select("svg.ripples")) == 2


def test_home_head_css_has_no_orphaned_rules():
    """Rules for the removed US band (globe, arcs, stats) and every other class rule in Home's inline CSS must be used by Home."""
    head = build.page_parts("index")[1]
    css = re.sub(r"/\*.*?\*/", "", head.split("<style>", 1)[1].split("</style>", 1)[0], flags=re.S)
    body = HOME_BODY.read_text(encoding="utf-8")
    used = set()
    for m in re.finditer(r'class="([^"]*)"', body):
        used.update(m.group(1).split())
    selectors = " ".join(re.findall(r"([^{}]+)\{", css))
    wanted = set(re.findall(r"\.([A-Za-z_][\w-]*)", selectors))
    # classes set by the scripts at runtime, not in the markup
    runtime = {"in", "js", "is-emitting"}
    orphans = sorted(wanted - used - runtime)
    assert orphans == [], f"classes styled in Home's head but never used by Home: {orphans}"
    for dead in ("why-grid", "globe", "meridian", "latitude", "node-pulse", "drawArc", "why-stat", "why-title", "nodePulse"):
        assert dead not in css, dead


# ---------------------------------------------------------------- copy rules for Home's new copy

def _home_copy(soup) -> str:
    """Home's visible copy except the hero statistics strip (existing claims, excluded by name) and the letters band."""
    clone = BeautifulSoup(str(soup), "html.parser")
    for sel in (".hero-stats", ".letters", "script", "style", "nav", ".mobile-drawer", "footer"):
        for el in clone.select(sel):
            el.decompose()
    return _text(clone.body)


def test_home_new_copy_has_no_pricing_digits_em_dashes_or_hype(home):
    text = _home_copy(home)
    assert not PRICE_OFFER.search(text), PRICE_OFFER.search(text)
    assert not HYPE.search(text), HYPE.search(text)
    assert "—" not in text and "–" not in text, "no em or en dashes in new Home copy"
    text = re.sub(r"\b(?:Step\s+)?0[1-9]\b", "", text).replace("B2B", "")      # step ordinals and a name, not figures
    m = re.search(r"\d", text)
    assert not m, f"digit in Home copy near {text[max(0, m.start() - 30):m.end() + 30]!r}"
    assert not re.search(r"\b(?:clients? like|case stud|testimonial|trusted by|years of|we have (?:built|delivered|helped))\b", text, re.I)


def test_home_copy_keeps_to_what_the_site_already_says(home):
    text = _home_copy(home).lower()
    for phrase in ("led by senior", "senior attention", "senior-led", "one brief", "search, email", "we'll", "retainer",
                   "step back", "without us", "guarantee", "within 90", "in 90 days"):
        assert phrase not in text, phrase


# ---------------------------------------------------------------- footer and nav

def test_footer_practice_column(soups, pillars, site):
    foot = site["footer"]
    cols = {c["heading"]: c["links"] for c in foot["columns"]}
    assert list(cols) == ["Navigate", "Practice", "Get in touch"]
    assert cols["Practice"] == [{"label": p["name"], "href": f"{p['stem']}.html"} for p in pillars]
    assert foot["strapline"] == "Business solutions for a digital world."
    assert foot["tagline"].startswith("B2B partnerships, AI solutions and digital presence.") and foot["tagline"].endswith("New York.")
    old = ("Channel-led US market entry", "Entering the US market, clearly")
    for stem, soup in soups.items():
        footer = soup.select_one("footer.footer")
        if stem == "404":
            assert footer is None
            continue
        col = next(c for c in footer.select(".footer-col") if c.h2 and _text(c.h2) == "Practice")
        assert [(a["href"], _text(a)) for a in col.select("a")] == [(f"{p['stem']}.html", p["name"]) for p in pillars], stem
        assert _text(footer.select_one(".footer-bottom span:last-child")) == "Business solutions for a digital world."
        assert "Business solutions for a digital world." in _text(footer.select_one(".footer-tag")) or "AI solutions" in _text(footer.select_one(".footer-tag"))
        text = _text(footer)
        for o in old:
            assert o not in text, (stem, o)
        # sub-services are listed nowhere in the footer (they are unlinked everywhere), so no dead anchors can appear
        assert not [a for a in footer.select("a") if "#" in a["href"]], stem


def test_no_page_links_to_a_services_anchor_that_moved(soups):
    """The four services moved to Partnerships; nothing may still point at Services.html#something (the test_links crawl
    proves every remaining fragment exists)."""
    for stem, soup in soups.items():
        for a in soup.select("a[href]"):
            assert not a["href"].startswith("Services.html#"), (stem, a["href"])


def test_nav_still_routes(site, soups):
    nav = site["nav"]
    assert [(n["label"], n["href"]) for n in nav] == [
        ("Home", "index.html"), ("BizCheck", "BizCheck.html"), ("Services", "Services.html"),
        ("About", "About.html"), ("Projects", "Projects.html"), ("Contact", "Contact.html")]
    for n in nav:
        assert (ROOT / n["href"]).exists() and n["href"][:-5] in build.PAGES, n
    for stem, soup in soups.items():
        assert [a["href"] for a in soup.select("nav.nav a.nav-link")] == [n["href"] for n in nav], stem
        assert [a["href"] for a in soup.select("nav.mobile-drawer a:not(.md-cta)")] == [n["href"] for n in nav], stem
