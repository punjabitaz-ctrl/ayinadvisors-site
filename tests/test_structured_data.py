"""schema.org structured data (JSON-LD), added in the site audit of 2026-10-28.

The site had none, so search engines had no machine-readable name, founder or service list for AYiN Advisors. Every
value comes from what the site already states; nothing here may invent a fact (no ratings, prices, phone or street).
"""
import json

import pytest
from bs4 import BeautifulSoup

import build


@pytest.fixture(scope="module")
def pages():
    return build.render_all()


def _ld(html):
    return [json.loads(s.string) for s in BeautifulSoup(html, "html.parser").find_all("script", type="application/ld+json")]


def _types(blocks):
    out = []
    for b in blocks:
        out += [g["@type"] for g in b["@graph"]] if "@graph" in b else [b["@type"]]
    return out


def test_home_describes_the_organization_founder_and_website(pages):
    blocks = _ld(pages["index"])
    assert _types(blocks) == ["Organization", "Person", "WebSite"]
    org, person, _ = blocks[0]["@graph"]
    assert org["name"] == "AYiN Advisors" and org["url"] == "https://ayinadvisors.com/"
    assert org["email"] == "hello@ayinadvisors.com" and org["address"]["addressLocality"] == "New York"
    assert person["name"] == "Taz Abbas" and person["sameAs"] == ["https://tazabbas.com/", "https://linkedin.com/in/tazabbas"]
    assert person["url"] == "https://tazabbas.com/"


def test_about_describes_the_organization_and_founder(pages):
    assert _types(_ld(pages["About"])) == ["Organization", "Person"]


@pytest.mark.parametrize("pillar", [p["stem"] for p in build.load_services()["pillars"]])
def test_each_pillar_and_service_page_has_a_breadcrumb_and_a_service(pages, pillar):
    site = build.load_site()["pages"]
    for stem, page in site.items():
        if page.get("template") not in ("pillar", "service") or page.get("pillar", stem) != pillar:
            continue
        blocks = _ld(pages[stem])
        expected = ["BreadcrumbList", "Service"] + (["FAQPage"] if page["template"] == "service" else [])
        assert _types(blocks) == expected, stem
        trail = blocks[0]["itemListElement"]
        assert [i["position"] for i in trail] == list(range(1, len(trail) + 1))
        assert trail[-1]["item"] == page["canonical"] and len(trail) == (3 if page["template"] == "pillar" else 4)
        assert blocks[1]["url"] == page["canonical"] and blocks[1]["description"] == page["description"]


def test_no_page_claims_what_the_site_does_not_state(pages):
    for stem, html in pages.items():
        text = json.dumps(_ld(html))
        for invented in ("aggregateRating", "review", "telephone", "streetAddress", "priceRange", "offers"):
            assert f'"{invented}"' not in text, stem  # as a property or type name, not a word in an answer


def test_a_value_can_never_close_the_script_tag(monkeypatch):
    site = build.load_site()
    site["pages"]["index"]["description"] = "</script><b>x"
    monkeypatch.setattr(build, "load_site", lambda: site)
    tags = build.jsonld_tags("index")
    assert "</script><b>" not in tags and json.loads(tags.split(">", 1)[1].rsplit("</script>", 1)[0])
