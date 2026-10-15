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
