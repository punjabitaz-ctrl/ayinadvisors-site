"""No dead internal links: every href/src on every generated page resolves to a page, an asset or an in-page id."""
import re
import json
import posixpath
from urllib.parse import urldefrag, urlsplit

import pytest
from bs4 import BeautifulSoup

import build
from conftest import ROOT, PAGES

SITE = "https://ayinadvisors.com"


def _soup(stem: str) -> BeautifulSoup:
    return BeautifulSoup((ROOT / f"{stem}.html").read_text(encoding="utf-8"), "html.parser")


@pytest.fixture(scope="module")
def soups():
    return {stem: _soup(stem) for stem in PAGES}


def _targets(soup):
    for tag, attr in (("a", "href"), ("link", "href"), ("script", "src"), ("img", "src"), ("source", "srcset")):
        for el in soup.find_all(tag):
            v = el.get(attr)
            if v:
                yield tag, v.split()[0] if attr == "srcset" else v


def _resolve(from_stem, ref, soups):
    """None if the reference is fine, else the reason it is dead."""
    if ref.startswith(("mailto:", "tel:", "data:", "javascript:")):
        return None
    if ref.startswith(("http://", "https://")) and not ref.startswith(SITE):
        return None  # external; not crawled
    absolute = ref.startswith(SITE)
    if absolute:
        ref = ref[len(SITE):] or "/"
    path, frag = urldefrag(ref)
    path = urlsplit(path).path
    if path == "":
        stem = from_stem
    elif path in ("/", "/index.html"):
        stem = "index"
    else:
        # a root-absolute path starts at the site root; anything else resolves against the page's own folder
        name = path.lstrip("/") if path.startswith("/") else posixpath.normpath(posixpath.join(posixpath.dirname(from_stem), path))
        if name == "index.html":
            stem = "index"
            return f"no id #{frag} on index.html" if frag and soups[stem].find(id=frag) is None else None
        if name in soups:
            # Cloudflare Pages serves /About.html at /About (it 308-redirects the .html form), so the canonical, og:url,
            # sitemap and page links all use the extensionless address (build.clean_href).
            stem = name
        elif name.endswith(".html"):
            if name[:-5] not in soups:
                return f"no such page {name}"
            stem = name[:-5]
        else:
            if not (ROOT / name).is_file():
                return f"no such file {name}"
            return f"fragment on a non-page {name}" if frag else None
    if frag and soups[stem].find(id=frag) is None:
        return f"no id #{frag} on {stem}.html"
    return None


def test_no_dead_internal_links_or_anchors(soups):
    dead = []
    for stem, soup in soups.items():
        for tag, ref in _targets(soup):
            why = _resolve(stem, ref, soups)
            if why:
                dead.append(f"{stem}.html <{tag}> {ref!r}: {why}")
    assert not dead, "dead internal links:\n  " + "\n  ".join(dead)


def test_the_crawler_catches_a_dead_page_file_and_anchor(soups):
    assert _resolve("index", "Services.html", soups) is None
    assert _resolve("index", "Nope.html", soups)
    assert _resolve("index", "Services.html#no-such-id", soups)
    assert _resolve("index", "#no-such-id", soups)
    assert _resolve("index", "assets/missing.css", soups)
    assert _resolve("index", "mailto:hello@ayinadvisors.com", soups) is None


def test_the_crawler_resolves_extensionless_page_addresses(soups):
    assert _resolve("index", "Services", soups) is None
    assert _resolve("index", "Projects#ai-projects", soups) is None
    assert _resolve("index", "Nope", soups)
    assert _resolve("partnerships/channel-strategy", "../Contact?practice=partnerships", soups) is None
    assert _resolve("partnerships/channel-strategy", "/", soups) is None


def test_page_links_use_the_extensionless_address(soups):
    """Every internal page link skips the 308 redirect Cloudflare answers a .html address with."""
    for stem, soup in soups.items():
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if ":" in href or href.startswith("#"):
                continue
            assert ".html" not in href, f"{stem}.html links {href!r}"


def test_the_crawler_resolves_links_from_subfolder_pages_against_their_folder(soups):
    sub = "partnerships/channel-strategy"
    assert _resolve(sub, "../Services.html", soups) is None
    assert _resolve(sub, "../index.html", soups) is None
    assert _resolve(sub, "../assets/theme.css", soups) is None
    assert _resolve(sub, "market-entry-research.html", soups) is None  # a sibling in the same folder
    assert _resolve(sub, "../partnerships.html#what", soups) is None
    assert _resolve(sub, "Services.html", soups), "a root-relative name from a subfolder page is dead"
    assert _resolve(sub, "assets/theme.css", soups)
    assert _resolve(sub, "../partnerships.html#research", soups), "the removed detail anchors stay dead"


def test_the_crawl_covers_every_site_json_page(soups):
    assert list(soups) == build.live_pages()
    assert sum(1 for s in soups.values() for _ in _targets(s)) > 100


def test_live_sub_services_are_linked_from_their_pillar_and_planned_ones_are_not():
    data = json.loads((ROOT / "content" / "services.json").read_text(encoding="utf-8"))
    for p in data["pillars"]:
        main = _soup(p["stem"]).find("main")
        hrefs = {a["href"] for a in main.find_all("a", href=True)}
        for s in p["services"]:
            if s["status"] == "live":
                assert build.clean_href(s["href"]) in hrefs, f"{p['stem']} does not link live sub-service {s['slug']}"
                assert s["href"][:-5] in build.load_site()["pages"], s["slug"]
            else:
                assert not any(s["slug"] in h for h in hrefs), f"{p['stem']} links to planned sub-service {s['slug']}"


def _is_external(href: str) -> bool:
    if not href.startswith(("http://", "https://", "//")):
        return False
    host = urlsplit(href if not href.startswith("//") else "https:" + href).hostname or ""
    return host != "ayinadvisors.com" and not host.endswith(".ayinadvisors.com")


def test_every_external_link_passes_no_seo_value_and_opens_safely(soups):
    """Links leaving the site (project websites, the founder's LinkedIn, the booking calendar) never endorse the target: nofollow + noopener + noreferrer on every one, no exemptions."""
    seen = 0
    for stem, soup in soups.items():
        for a in soup.select("a[href^='http'], a[href^='//']"):
            if not _is_external(a["href"]):
                continue
            seen += 1
            rel = set(a.get("rel") or [])
            assert {"nofollow", "noopener", "noreferrer"} <= rel, f"{stem}: {a['href']} rel={sorted(rel)}"
            assert a.get("target") == "_blank", f"{stem}: {a['href']} does not open in a new tab"
    assert seen, "the project websites and the founder's LinkedIn are outbound links"


LINKEDIN = "https://linkedin.com/in/tazabbas"
BOOKING = "https://calendar.app.google/8iyzRwWpo7FWfYB98"


def test_the_only_outbound_links_are_the_project_sites_linkedin_and_the_booking_calendar(soups):
    """Site review (2026-10-28): the founder had no public profile anywhere on the site. LinkedIn now sits in every
    footer and in the About founder block; beside it, the project websites (eight since Orison IGT, 2026-10-28) remain the only outbound links. The booking calendar (2026-10-28)
    sits in every footer and on the Contact page."""
    for stem, soup in soups.items():
        outbound = [a["href"] for a in soup.select("a[href^='http'], a[href^='//']") if _is_external(a["href"])]
        others = [h for h in outbound if h not in (LINKEDIN, BOOKING)]
        footer = soup.select_one("footer")
        if footer is not None:
            assert [a["href"] for a in footer.select(f"a[href='{LINKEDIN}']")] == [LINKEDIN], stem
            assert [a["href"] for a in footer.select(f"a[href='{BOOKING}']")] == [BOOKING], stem
        if stem == "Projects":
            assert len(others) == 8, stem
        else:
            assert others == [], f"{stem}: {others}"
    call = soups["Contact"].select(f".contact-meta a[href='{BOOKING}']")
    assert len(call) == 1 and "opens in a new tab" in call[0].select_one(".vh").get_text()
    founder = soups["About"].select_one(".founder-note a")
    assert founder["href"] == LINKEDIN and "opens in a new tab" in founder.select_one(".vh").get_text()


def test_each_project_site_has_one_link_with_a_named_accessible_text(soups):
    soup = soups["Projects"]
    cards = soup.select(".site-card")
    assert len(cards) == 8
    for card in cards:
        links = card.select("a")
        assert len(links) == 1, "the preview and the text share one link (no adjacent duplicate links)"
        a = links[0]
        name = card.select_one("h3").get_text(strip=True)
        assert a.get_text(strip=True).startswith("Visit site")
        assert name in a.select_one(".vh").get_text()
        assert a.select_one(".btn-arrow")["aria-hidden"] == "true"
        name_thumb = card.select_one(".site-thumb-name")
        if name_thumb is not None:
            # no screenshot yet (Orison IGT, 2026-10-28): the frame shows the domain, hidden from assistive tech
            assert name_thumb.get("aria-hidden") == "true" and card.select_one("picture") is None
            continue
        img = card.select_one("picture img")
        assert img and img.get("alt", "").strip() and img.get("width") and img.get("height") and img.get("loading") == "lazy"


def test_hidden_link_text_is_hidden_on_every_page(soups):
    """Every page that carries visually hidden text (.vh) loads the shared stylesheet that hides it. Found on the preview
    (2026-10-28): the rule lived only in the Projects page styles, so "(opens in a new tab)" showed in every footer."""
    css = (ROOT / "assets" / "styles.css").read_text(encoding="utf-8")
    assert re.search(r"^\.vh \{[^}]*clip-path: inset\(50%\)", css, re.M)
    for stem, soup in soups.items():
        if soup.select(".vh"):
            assert any(l["href"].endswith("assets/styles.css") for l in soup.select('link[rel="stylesheet"][href]')), stem
