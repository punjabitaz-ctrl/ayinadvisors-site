"""sitemap.xml is generated from content/site.json and checked by `build.py --check`."""
import xml.etree.ElementTree as ET

import build
from conftest import ROOT

NS = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}

# Written out by hand on purpose: this is the public contract, independent of the generator.
EXPECTED = {
    "https://ayinadvisors.com/": "1.0",
    "https://ayinadvisors.com/Services": "0.8",
    "https://ayinadvisors.com/partnerships": "0.8",
    "https://ayinadvisors.com/partnerships/market-entry-research": "0.7",
    "https://ayinadvisors.com/partnerships/channel-strategy": "0.7",
    "https://ayinadvisors.com/partnerships/partner-introductions": "0.7",
    "https://ayinadvisors.com/partnerships/regional-expansion": "0.7",
    "https://ayinadvisors.com/ai-solutions": "0.8",
    "https://ayinadvisors.com/ai-solutions/custom-applications": "0.7",
    "https://ayinadvisors.com/ai-solutions/workflow-automation": "0.7",
    "https://ayinadvisors.com/ai-solutions/operational-efficiency": "0.7",
    "https://ayinadvisors.com/digital-presence": "0.8",
    "https://ayinadvisors.com/digital-presence/websites": "0.7",
    "https://ayinadvisors.com/digital-presence/digital-marketing": "0.7",
    "https://ayinadvisors.com/digital-presence/community-content": "0.7",
    "https://ayinadvisors.com/About": "0.7",
    "https://ayinadvisors.com/Projects": "0.7",
    "https://ayinadvisors.com/BizCheck": "0.9",
    "https://ayinadvisors.com/Contact": "0.9",
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


def test_public_urls_are_the_ones_cloudflare_serves_without_a_redirect():
    """Site audit (2026-10-28): Cloudflare Pages 308-redirects /About.html to /About, so a canonical, og:url or sitemap URL
    ending in .html points search engines at a redirect. Every one now names the address the page is served at."""
    from bs4 import BeautifulSoup
    for stem, html in build.render_all().items():
        soup = BeautifulSoup(html, "html.parser")
        for el, attr in ((soup.select_one('link[rel="canonical"]'), "href"), (soup.select_one('meta[property="og:url"]'), "content")):
            if el is not None:
                assert not el[attr].endswith(".html"), f"{stem}: {el[attr]}"
    assert ".html" not in build.render_sitemap()
