import json
from conftest import ROOT, PAGES


def load():
    return json.loads((ROOT / "content" / "site.json").read_text(encoding="utf-8"))


def test_every_page_is_described():
    pages = load()["pages"]
    for stem in PAGES:
        assert stem in pages, f"{stem} missing from site.json"


def test_cta_variants_are_captured():
    pages = load()["pages"]
    assert pages["BizCheck"]["cta"] == {
        "href": "#submit", "label": "Submit Your Idea", "class": "btn"
    }
    assert pages["Contact"]["cta"]["href"] == "#book"
    assert pages["About"]["cta"]["href"] == "Contact.html"


def test_404_carries_the_footer():
    """Sprint 6 reconsidered the 404's missing footer: a lost visitor gets every route, so it now has one."""
    assert load()["pages"]["404"]["footer"] is True
    assert load()["pages"]["About"]["footer"] is True


def test_nav_order_is_the_owner_chosen_order():
    nav = load()["nav"]
    assert [n["label"] for n in nav] == [
        "BizCheck", "Home", "About", "Services", "Projects", "Contact"
    ]
    assert next(n for n in nav if n["label"] == "BizCheck")["class"] == "gold"
