"""Phase 2b rollout (static): iris markers on section heads, assemble/tilt hooks on card grids, ripple placement."""
import pytest
import build
from bs4 import BeautifulSoup


@pytest.fixture(scope="module")
def soups():
    return {stem: BeautifulSoup(html, "html.parser") for stem, html in build.render_all().items()}


# Every section head eyebrow, per page (page-header and closing-CTA eyebrows are not section heads)
HEADS = {
    "index": ".sec-head .eyebrow",
    "About": ".meaning .eyebrow, .sec-head .eyebrow",
    "BizCheck": ".bc-head .eyebrow, .intake-intro .eyebrow",
    "Contact": ".contact-intro .eyebrow",
}
EXPECTED = {"index": 2, "About": 3, "BizCheck": 4, "Contact": 1}


@pytest.mark.parametrize("stem", sorted(HEADS))
def test_every_section_head_has_the_iris_marker(soups, stem):
    heads = soups[stem].select(HEADS[stem])
    assert len(heads) == EXPECTED[stem], f"{stem}: {len(heads)} section heads"
    for eb in heads:
        marks = eb.select("svg.iris-mark")
        assert len(marks) == 1, (stem, eb.get_text(" ", strip=True))
        m = marks[0]
        assert m.get("aria-hidden") == "true" and m.get("focusable") == "false" and not m.get("tabindex")
        assert m.get_text(strip=True) == "" and not m.select("title, desc")
        assert not eb.select(".sec-index"), "the iris replaces the number"
        text = eb.get_text(" ", strip=True)
        assert text and not text[0].isdigit(), f"{stem}: eyebrow text must survive the marker: {text!r}"


def test_no_orphan_section_numbers(soups):
    # numbers survive only where no iris replaced them (none left on About/BizCheck/Contact)
    for stem in ("About", "BizCheck", "Contact", "Services", "Projects"):
        assert not soups[stem].select(".sec-index"), stem


def _hooks(el):
    c = el.get("class", [])
    return "asm-card" in c and "tilt3d" in c and el.has_attr("data-tilt") and "reveal" not in c


def test_card_grids_assemble_and_tilt_hooks_present(soups):
    # Services: every deliverables grid is an assemble stage inside its own assemble root
    arts = soups["Services"].select("article.svc-detail")
    assert len(arts) == 4
    for art in arts:
        assert "assemble" in art.get("class", []) and art.has_attr("data-assemble")
        grid = art.select_one(".deliverables")
        assert "asm-stage" in grid.get("class", [])
        cells = grid.select("li")
        assert len(cells) == 6 and all(_hooks(li) for li in cells)
    # Projects: the grid is root and stage, the five cards animate and tilt
    grid = soups["Projects"].select_one(".projects-grid")
    assert {"assemble", "asm-stage"} <= set(grid.get("class", [])) and grid.has_attr("data-assemble")
    cards = grid.select(".project-card")
    assert len(cards) == 5 and all(_hooks(c) for c in cards)
    # BizCheck steps
    steps = soups["BizCheck"].select_one(".bc-steps")
    assert {"assemble", "asm-stage"} <= set(steps.get("class", [])) and steps.has_attr("data-assemble")
    cards = steps.select(".bc-step")
    assert len(cards) == 3 and all(_hooks(c) for c in cards)
    # no item animates without a root, and every root is a real assemble container
    for stem, soup in soups.items():
        for item in soup.select(".asm-card, .asm-fade, .asm-rise, .asm-grow, .asm-scatter"):
            assert item.find_parent(attrs={"data-assemble": True}) is not None, (stem, item.name, item.get("class"))
        for root in soup.select("[data-assemble]"):
            assert "assemble" in root.get("class", []), (stem, root.get("class"))


def test_ripples_are_decorative_and_stay_off_hero_and_forms(soups):
    placed = {}
    for stem, soup in soups.items():
        rs = soup.select("svg.ripples")
        placed[stem] = len(rs)
        for r in rs:
            assert r.get("aria-hidden") == "true" and r.get("focusable") == "false"
            # Home's rings drift with scroll; the section-head rings (ripples-top) stay put so their box never leaves the section
            assert r.get("data-drift") or "ripples-top" in r.get("class", [])
            host = r.parent
            assert "has-ripples" in host.get("class", []), (stem, host.name, host.get("class"))
            assert host.name == "section"
            assert not host.select("form, canvas, [data-turnstile], .cf-turnstile")
            assert not r.find_parent(["header", "form"])
            assert host.get("id") != "submit"
    # ripples only where a section heading has room around it: About (approach) and BizCheck (panel), plus Home's two
    assert placed["Contact"] == 0 and placed["404"] == 0
    assert placed["Services"] == 0 and placed["Projects"] == 0
    assert placed["About"] == 1 and placed["BizCheck"] == 1 and placed["index"] == 2
    for stem in ("About", "BizCheck"):
        r = soups[stem].select_one("svg.ripples")
        assert "ripples-top" in r.get("class", []), stem
        assert r.find_next("div", class_="bc-head") or r.find_next("div", class_="sec-head")
