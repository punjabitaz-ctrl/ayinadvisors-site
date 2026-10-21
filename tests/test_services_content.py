"""content/services.json: shape, and the copy rules that bind the three pillars (no pricing, no invented numbers)."""
import json
import re

from bs4 import BeautifulSoup

import build
from conftest import ROOT

SERVICES = ROOT / "content" / "services.json"


import pytest


@pytest.fixture(scope="module")
def pages_rendered():
    return build.render_all()


def load() -> dict:
    return json.loads(SERVICES.read_text(encoding="utf-8"))


def test_services_json_shape():
    data = load()
    pillars = data["pillars"]
    assert len(pillars) == 3
    for key in ("slug", "stem", "name", "tagline", "buyer", "summary", "icon", "lead", "hub_line", "do_heading", "intro"):
        assert all(isinstance(p.get(key), str) and p[key].strip() for p in pillars), key
    assert [p["icon"] for p in pillars] == ["linked", "focus", "arcs"], "three distinct iris icons"
    for p in pillars:
        who = p["who"]
        assert who["heading"].strip() and who["intro"].strip(), p["slug"]
        assert len(who["items"]) == 3 and all(i["title"].strip() and i["text"].strip() for i in who["items"]), p["slug"]
        assert all(p["cta"][k].strip() for k in ("eyebrow", "heading", "text")), p["slug"]
    assert len({p["slug"] for p in pillars}) == 3 and len({p["stem"] for p in pillars}) == 3
    assert [p["stem"] for p in pillars] == ["partnerships", "ai-solutions", "digital-presence"]
    pages = build.load_site()["pages"]
    for p in pillars:
        assert pages[p["stem"]]["template"] == "pillar" and pages[p["stem"]]["pillar"] == p["slug"], p["stem"]
    slugs = []
    for p in pillars:
        assert p["services"], p["slug"]
        for s in p["services"]:
            assert s["name"].strip() and s["summary"].strip(), s
            assert s["status"] in ("planned", "live"), s
            assert ("href" in s) == (s["status"] == "live"), f"{s['slug']}: href only when live"
            slugs.append(s["slug"])
    assert len(slugs) == len(set(slugs)) == 10


def test_the_ten_sub_services_are_the_ones_in_the_design():
    got = [[s["slug"] for s in p["services"]] for p in load()["pillars"]]
    assert got == [
        ["market-entry-research", "channel-strategy", "partner-introductions", "regional-expansion"],
        ["custom-applications", "workflow-automation", "operational-efficiency"],
        ["websites", "digital-marketing", "community-content"],
    ]


def test_no_service_is_live_before_its_page_exists():
    assert all(s["status"] == "planned" for p in load()["pillars"] for s in p["services"])


def test_the_four_market_entry_services_keep_their_existing_names_and_lines():
    frag = (ROOT / "templates" / "pages" / "index.body.frag").read_text(encoding="utf-8")
    soup = BeautifulSoup(frag, "html.parser")
    existing = {}
    for card in soup.select("a.svc"):
        existing[card.h3.get_text(" ", strip=True)] = card.p.get_text(" ", strip=True)
    partnerships = load()["pillars"][0]["services"]
    assert len(partnerships) == 4
    for s in partnerships:
        assert existing.get(s["name"]) == s["summary"], s["name"]


def _strings(node):
    """Every piece of copy under a node (dict values, list items), skipping machine keys."""
    if isinstance(node, str):
        yield node
    elif isinstance(node, list):
        for x in node:
            yield from _strings(x)
    elif isinstance(node, dict):
        for k, v in node.items():
            if k not in ("slug", "stem", "icon", "status", "href"):
                yield from _strings(v)


def _words(pillar) -> str:
    return " ".join(_strings(pillar))


def _shared_copy() -> str:
    data = load()
    return " ".join(_strings({"hub": data["hub"], "process": data["process"]}))


def test_services_json_has_the_hub_and_process_copy():
    data = load()
    hub = data["hub"]
    for key in ("eyebrow", "headline", "lead"):
        assert hub[key].strip(), key
    for band in ("choose", "fit", "cta"):
        assert hub[band]["eyebrow"].strip() and hub[band]["heading"].strip(), band
    assert len(hub["fit"]["paragraphs"]) >= 2 and hub["choose"]["intro"].strip() and hub["cta"]["text"].strip()
    proc = data["process"]
    assert proc["eyebrow"] == "How we work" and proc["heading"].strip() and proc["intro"].strip()
    assert len(proc["steps"]) == 4 and all(s["name"].strip() and s["text"].strip() for s in proc["steps"])


def _main_text(html: str, drop=()) -> str:
    soup = BeautifulSoup(html, "html.parser")
    main = soup.find("main") or soup
    for sel in drop:
        for el in main.select(sel):
            el.decompose()
    return main.get_text(" ", strip=True)


# The four market-entry detail blocks are the owner's existing copy; they talk about a client's market pricing
# landscape (a deliverable), not our fees. Everything else on these pages is new copy and is scanned.
VERBATIM = ("article.svc-detail",)
PRICE_OFFER = re.compile(r"\$\s?\d|\bpric(?:e|es|ed|ing)\b|\bper month\b|/mo\b|\bsubscription\b", re.I)


def test_no_pricing_words_in_services_json():
    text = " ".join(_words(p) for p in load()["pillars"]) + " " + _shared_copy()
    assert not PRICE_OFFER.search(text), PRICE_OFFER.search(text)


def test_no_pricing_words_on_hub_pillar_and_home_pages():
    pages = build.render_all()
    for stem in ("Services", "partnerships", "ai-solutions", "digital-presence", "index"):
        text = _main_text(pages[stem], drop=VERBATIM)
        text = text.replace("$24T", "")  # the Home stat is a market size, not a price
        m = PRICE_OFFER.search(text)
        assert not m, f"{stem}: pricing word {m.group(0)!r}"


def test_no_invented_digits_in_new_pillar_copy():
    """AI Solutions and Digital Presence copy asserts no number, count or date (step ordinals aside)."""
    pillars = load()["pillars"]
    for p in pillars[1:]:
        assert not re.search(r"\d", _words(p)), f"{p['slug']}: digit in services.json copy"
    assert not re.search(r"\d", _shared_copy()), "digit in the hub or process copy"
    pages = build.render_all()
    for stem in ("Services", "ai-solutions", "digital-presence"):
        text = _main_text(pages[stem])
        text = re.sub(r"\b(?:Step\s+)?0[1-9]\b", "", text)  # step ordinals only
        text = text.replace("B2B", "")  # the practice's name on the hub, not a figure
        m = re.search(r"\d", text)
        assert not m, f"{stem}: digit in page copy near {text[max(0, m.start() - 30):m.end() + 30]!r}"


# Copy rules for everything drafted in Sprint 2 (the four verbatim market-entry blocks and the moved proof band are the
# owner's existing copy and are not scanned here).
HYPE = re.compile(r"coming soon|world-class|cutting-edge|best-in-class|state-of-the-art|game-chang|revolution|seamless|unlock|supercharge|leverage|synerg|guarantee", re.I)


def test_new_copy_has_no_em_dashes_hype_or_coming_soon():
    data = load()
    new = [_shared_copy()] + [" ".join(_strings({k: v for k, v in p.items() if k != "services"})) for p in data["pillars"]]
    new += [" ".join(_strings(p["services"])) for p in data["pillars"][1:]]   # the four market-entry summaries are the owner's
    for text in new:
        assert "—" not in text and "–" not in text, text[:60]
        assert not HYPE.search(text), HYPE.search(text)


def test_new_copy_names_no_clients_results_or_testimonials():
    text = _shared_copy() + " " + " ".join(_words(p) for p in load()["pillars"])
    assert not re.search(r"\b(?:clients? like|case stud|testimonial|trusted by|results? (?:of|from)|we have (?:built|delivered|helped)|years of)\b", text, re.I)


def test_hub_and_pillar_copy_is_the_json_copy(pages_rendered):
    hub = load()["hub"]
    soup = BeautifulSoup(pages_rendered["Services"], "html.parser")
    assert soup.h1.get_text(strip=True) == hub["headline"]
    assert soup.select_one("header.pagehead .lead").get_text(strip=True) == hub["lead"]
