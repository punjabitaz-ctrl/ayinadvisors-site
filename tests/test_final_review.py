"""Final review fixes (2026-10-28): a direct booking line under every consultation CTA, proof of work on Home, an iOS
home-screen icon, and a practice-neutral location field on Contact."""
from bs4 import BeautifulSoup
from PIL import Image

import build
from conftest import ROOT, PAGES

BOOKING = "https://calendar.app.google/8iyzRwWpo7FWfYB98"


def _soup(stem):
    return BeautifulSoup((ROOT / f"{stem}.html").read_text(encoding="utf-8"), "html.parser")


def test_every_closing_cta_offers_a_direct_booking_link():
    seen = 0
    for stem in PAGES:
        cta = _soup(stem).select_one("section.cta")
        if cta is None:
            continue
        seen += 1
        a = cta.select_one(".cta-alt a")
        assert a and a["href"] == BOOKING, stem
        assert a["target"] == "_blank" and "noopener" in a["rel"] and "(opens in a new tab)" in a.get_text(), stem
    assert seen == 18 + len(build.blog_posts())  # 17 before the blog, the blog index, then one per live post


def test_home_shows_selected_work_linking_to_projects():
    work = _soup("index").select_one("section#work")
    assert [a["href"] for a in work.select("a")] == ["Projects#ai-projects", "Projects#digital-projects"]
    projects = _soup("Projects")
    assert projects.select_one("#ai-projects") and projects.select_one("#digital-projects")
    # only names the Projects page already shows
    shown = {h.get_text(strip=True) for h in projects.select("h3")}
    for name in ("ChanneliQ", "Memento", "BizCheck", "TrustLayer", "Pardesi Connections", "Thinkers Dilemma", "Historical Philly"):
        assert name in shown and name in work.get_text(), name


def test_every_page_has_a_png_touch_icon():
    icon = ROOT / "apple-touch-icon.png"
    with Image.open(icon) as im:
        assert im.size == (180, 180) and im.format == "PNG"
    for stem in PAGES:
        link = _soup(stem).select_one('link[rel="apple-touch-icon"]')
        assert link and link["href"] == build.page_root(stem) + "apple-touch-icon.png", stem


def test_contact_location_field_suits_every_practice():
    label = _soup("Contact").select_one('label[for="hq"]')
    assert label.get_text(strip=True) == "Where are you based?"
