"""Baseline-independent chrome invariants across every rendered page."""
import pytest
import build
from bs4 import BeautifulSoup
from parity import canon_subtree


@pytest.fixture(scope="module")
def soups():
    return {stem: BeautifulSoup(html, "html.parser") for stem, html in build.render_all().items()}


def _unroot(soup, selector):
    """Drop the root prefix a page puts on site links ("../" in a subfolder, "/" on the 404), so its chrome compares
    equal to a root page's."""
    for a in soup.select(f"{selector} a[href^='../']"):
        a["href"] = a["href"][3:]
    for a in soup.select(f"{selector} a[href^='/']"):
        a["href"] = a["href"][1:]


def _normalised(soup, selector):
    """Canonical subtree minus the parts that legitimately vary per page."""
    soup = BeautifulSoup(str(soup), "html.parser")
    _unroot(soup, selector)
    for a in soup.select(f"{selector} a"):
        a.attrs.pop("aria-current", None)
        classes = [c for c in a.get("class", []) if c != "active"]
        if classes:
            a["class"] = classes
        elif "class" in a.attrs:
            del a["class"]
    for cta in soup.select(f"{selector} .nav-cta a, {selector} a.md-cta"):
        for attr in ("href", "class"):
            cta.attrs.pop(attr, None)
        label = cta.select_one(".btn-label")
        (label or cta).string = "CTA"
    return canon_subtree(soup, selector)


@pytest.mark.parametrize("selector", ["nav.nav", ".mobile-drawer"])
def test_nav_and_drawer_identical_across_pages(soups, selector):
    shapes = {stem: _normalised(s, selector) for stem, s in soups.items()}
    assert all(shapes.values()), "every page must have the chrome"
    first_stem = next(iter(shapes))
    for stem, shape in shapes.items():
        assert shape == shapes[first_stem], f"{stem} {selector} differs from {first_stem}"


def test_footer_identical_across_pages_that_have_one(soups):
    shapes = {}
    for stem, s in soups.items():
        if s.select_one("footer.footer"):
            s = BeautifulSoup(str(s), "html.parser")
            _unroot(s, "footer.footer")
            shapes[stem] = canon_subtree(s, "footer.footer")
    assert set(soups) == set(shapes)  # Sprint 6: the 404 carries the footer too, so a lost visitor has every route
    assert all(shapes.values())
    first = next(iter(shapes))
    for stem, shape in shapes.items():
        assert shape == shapes[first], f"{stem} footer differs from {first}"


@pytest.mark.parametrize("selector", ["nav.nav", ".mobile-drawer"])
def test_aria_current_marks_exactly_the_active_page_in_each_navigation(soups, selector):
    """The normaliser above ignores aria-current, so pin it here.

    A page that has its own entry in the navigation has exactly one aria-current="page" link (itself) and no other
    aria-current link. A pillar page has no entry of its own: it sits under Services, so the navigation carries no
    "page" link at all and exactly one aria-current="true" link, Services (the section the visitor is in).
    """
    pillars = {s for s, p in build.load_site()["pages"].items() if p.get("template") in ("pillar", "service")}
    assert len(pillars) == 13  # three pillar pages and the ten service pages
    nav_hrefs = [n["href"] for n in build.load_site()["nav"]]
    targets = {}
    for stem, s in soups.items():
        page_links = s.select(f"{selector} a[aria-current='page']")
        true_links = s.select(f"{selector} a[aria-current='true']")
        assert len(s.select(f"{selector} a[aria-current]")) == len(page_links) + len(true_links), f"{stem}: unknown aria-current value"
        if stem == "404":
            assert not page_links and not true_links, "404 has no current page"
            continue
        if stem in pillars:
            assert not page_links, f"{stem} {selector}: a pillar page is not itself a navigation entry"
            assert len(true_links) == 1 and true_links[0]["href"] == build.clean_href(build.page_root(stem) + "Services.html"), f"{stem} {selector}: {true_links}"
        else:
            assert f"{stem}.html" in nav_hrefs
            assert len(page_links) == 1 and not true_links, f"{stem} {selector}: {page_links} {true_links}"
            assert page_links[0]["href"] == build.clean_href(f"{stem}.html")
        targets[stem] = (page_links or true_links)[0]["href"]
    # Each page that has its own entry marks a different link.
    rest = {s: t for s, t in targets.items() if s not in pillars}
    assert len(set(rest.values())) == len(rest), "each page must mark a different link"
    other = "nav.nav" if selector == ".mobile-drawer" else ".mobile-drawer"
    for stem, s in soups.items():
        if stem != "404":
            assert s.select_one(f"{other} a[aria-current]")["href"] == targets[stem]


def test_the_section_link_keeps_its_active_styling_on_pillar_pages(soups):
    """aria-current="true" changes what is announced, not what is drawn: the Services link stays .active on every pillar page."""
    for stem in ("partnerships", "ai-solutions", "digital-presence", "partnerships/market-entry-research"):
        active = soups[stem].select("nav.nav a.nav-link.active")
        assert len(active) == 1 and active[0]["href"] == build.clean_href(build.page_root(stem) + "Services.html") and active[0]["aria-current"] == "true", stem
    for stem in ("Services", "index", "About"):
        active = soups[stem].select("nav.nav a.nav-link.active")
        assert len(active) == 1 and active[0]["aria-current"] == "page", stem
