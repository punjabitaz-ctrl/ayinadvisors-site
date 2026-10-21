"""Baseline-independent chrome invariants across every rendered page."""
import pytest
import build
from bs4 import BeautifulSoup
from parity import canon_subtree


@pytest.fixture(scope="module")
def soups():
    return {stem: BeautifulSoup(html, "html.parser") for stem, html in build.render_all().items()}


def _normalised(soup, selector):
    """Canonical subtree minus the parts that legitimately vary per page."""
    soup = BeautifulSoup(str(soup), "html.parser")
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
    shapes = {stem: canon_subtree(s, "footer.footer") for stem, s in soups.items() if s.select_one("footer.footer")}
    assert set(soups) - set(shapes) == {"404"}
    assert all(shapes.values())
    first = next(iter(shapes))
    for stem, shape in shapes.items():
        assert shape == shapes[first], f"{stem} footer differs from {first}"


@pytest.mark.parametrize("selector", ["nav.nav", ".mobile-drawer"])
def test_aria_current_marks_exactly_the_active_page_in_each_navigation(soups, selector):
    """The normaliser above ignores aria-current, so pin it here: one link, value "page", same target in both navs."""
    targets = {}
    for stem, s in soups.items():
        current = s.select(f"{selector} a[aria-current]")
        if stem == "404":
            assert not current, "404 has no current page"
            continue
        assert len(current) == 1 and current[0]["aria-current"] == "page", f"{stem} {selector}: {current}"
        targets[stem] = current[0]["href"]
    # Each page marks a different link, except the three pillar pages, which sit under Services in the nav.
    pillars = {s for s, p in build.load_site()["pages"].items() if p.get("template") == "pillar"}
    assert pillars and all(targets[s] == targets["Services"] for s in pillars)
    rest = {s: t for s, t in targets.items() if s not in pillars}
    assert len(set(rest.values())) == len(rest), "each page must mark a different link"
    other = "nav.nav" if selector == ".mobile-drawer" else ".mobile-drawer"
    for stem, s in soups.items():
        if stem != "404":
            assert s.select_one(f"{other} a[aria-current]")["href"] == targets[stem]
