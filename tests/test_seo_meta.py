"""Titles and descriptions that search results show in full (site audit, 2026-10-28).

The audit found About, Services, Projects and the three practice pages titled by a single generic word. Each title now
names what the page offers, stays short enough not to be cut off, and is unique across the site.
"""
import build


def _indexed():
    return {s: p for s, p in build.load_site()["pages"].items() if p.get("canonical")}


def test_titles_are_unique_and_fit_a_search_result():
    pages = _indexed()
    titles = [p["title"] for p in pages.values()]
    assert len(set(titles)) == len(titles)
    for stem, p in pages.items():
        assert len(p["title"]) <= 60, f"{stem}: {len(p['title'])} characters"
        assert p["title"].startswith("AYiN Advisors - ") or p["title"].endswith(" - AYiN Advisors"), stem


def test_no_title_is_a_single_generic_word():
    """Service pages are titled by the service's own name (test_service_pages pins that), so they are left out."""
    for stem, p in _indexed().items():
        if p.get("template") == "service":
            continue
        name = p["title"].replace("AYiN Advisors", "").strip(" -")
        assert len(name.split()) >= 2, f"{stem}: {p['title']!r}"


def test_descriptions_are_unique_and_fit_a_search_result():
    pages = _indexed()
    descs = [p["description"] for p in pages.values()]
    assert len(set(descs)) == len(descs)
    for stem, p in pages.items():
        assert 70 <= len(p["description"]) <= 160, f"{stem}: {len(p['description'])} characters"
