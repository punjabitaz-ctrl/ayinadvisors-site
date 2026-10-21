"""sitemap.xml is generated from content/site.json and checked by `build.py --check`."""
import xml.etree.ElementTree as ET

import build
from conftest import ROOT

NS = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}

# Written out by hand on purpose: this is the public contract, independent of the generator.
EXPECTED = {
    "https://ayinadvisors.com/": "1.0",
    "https://ayinadvisors.com/Services.html": "0.8",
    "https://ayinadvisors.com/partnerships.html": "0.8",
    "https://ayinadvisors.com/ai-solutions.html": "0.8",
    "https://ayinadvisors.com/digital-presence.html": "0.8",
    "https://ayinadvisors.com/About.html": "0.7",
    "https://ayinadvisors.com/Projects.html": "0.7",
    "https://ayinadvisors.com/BizCheck.html": "0.9",
    "https://ayinadvisors.com/Contact.html": "0.9",
}


def _entries(xml: str) -> list[tuple[str, str]]:
    root = ET.fromstring(xml)  # raises on invalid XML
    return [(u.find("s:loc", NS).text, u.find("s:priority", NS).text) for u in root.findall("s:url", NS)]


def test_sitemap_matches_site_json():
    entries = _entries(build.render_sitemap())
    assert dict(entries) == EXPECTED
    assert len(entries) == len(EXPECTED), "no duplicate URLs"


def test_sitemap_lists_exactly_the_site_json_pages_that_opt_in():
    pages = build.load_site()["pages"]
    listed = {p["canonical"] for p in pages.values() if "sitemap" in p}
    assert listed == set(EXPECTED)
    assert "sitemap" not in pages["404"]
    for stem, p in pages.items():
        if p.get("canonical"):
            assert "sitemap" in p, f"{stem} has a canonical but no sitemap priority"


def test_the_committed_sitemap_is_the_generated_one():
    assert (ROOT / "sitemap.xml").read_text(encoding="utf-8") == build.render_sitemap()
    assert dict(_entries((ROOT / "sitemap.xml").read_text(encoding="utf-8"))) == EXPECTED


def test_sitemap_is_fresh():
    assert build.check() == []


def test_check_reports_a_hand_edited_sitemap_as_stale(sandbox):
    p = sandbox / "sitemap.xml"
    p.write_text(p.read_text(encoding="utf-8").replace("<priority>0.8", "<priority>0.1", 1), encoding="utf-8")
    assert build.check() == ["sitemap.xml"]


def test_check_reports_a_missing_sitemap_as_stale(sandbox):
    (sandbox / "sitemap.xml").unlink()
    assert build.check() == ["sitemap.xml"]


def test_main_writes_the_sitemap(sandbox):
    (sandbox / "sitemap.xml").write_text("old", encoding="utf-8")
    build.main()
    assert (sandbox / "sitemap.xml").read_text(encoding="utf-8") == build.render_sitemap()
