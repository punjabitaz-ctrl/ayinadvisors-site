"""No dead internal links: every href/src on every generated page resolves to a page, an asset or an in-page id."""
import json
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
    if ref.startswith(SITE):
        ref = ref[len(SITE):] or "/"
    path, frag = urldefrag(ref)
    path = urlsplit(path).path
    if path == "":
        stem = from_stem
    elif path in ("/", "/index.html", "index.html"):
        stem = "index"
    else:
        name = path.lstrip("/")
        if name.endswith(".html"):
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


def test_the_crawl_covers_every_site_json_page(soups):
    assert list(soups) == list(build.load_site()["pages"])
    assert sum(1 for s in soups.values() for _ in _targets(s)) > 100


def test_sub_services_are_listed_but_not_linked():
    data = json.loads((ROOT / "content" / "services.json").read_text(encoding="utf-8"))
    for p in data["pillars"]:
        main = _soup(p["stem"]).find("main")
        hrefs = {a["href"] for a in main.find_all("a", href=True)}
        for s in p["services"]:
            assert not any(s["slug"] in h for h in hrefs), f"{p['stem']} links to sub-service {s['slug']}"
