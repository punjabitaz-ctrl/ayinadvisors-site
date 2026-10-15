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


def test_404_opts_out_of_footer():
    assert load()["pages"]["404"]["footer"] is False
    assert load()["pages"]["About"]["footer"] is True


def test_nav_order_matches_live_site():
    nav = load()["nav"]
    assert [n["label"] for n in nav] == [
        "Home", "BizCheck", "Services", "About", "Projects", "Contact"
    ]
    assert next(n for n in nav if n["label"] == "BizCheck")["class"] == "gold"
