"""Light-led page rhythm: navy only in the hero, nav, drawer and footer; bands alternate;
closing CTA is the gold accent band; cards are white."""
import pytest
import build
from bs4 import BeautifulSoup

SURFACES = ("surface-page", "surface-alt", "surface-card", "surface-inverse", "surface-accent")
HEROES = ("header.hero", "header.pagehead", "header.bc-hero", "header.contact-hero", "main.nf")

# Top-level band surfaces in document order (hero first, footer last), from the task BAND_MAP.
BAND_MAP = {
    # home: letters (alt), practices (page), who (alt), how we work (page), who we are (alt), selected work (page)
    "index": ["inverse", "alt", "page", "alt", "page", "alt", "page", "accent", "inverse"],
    "About": ["inverse", "page", "alt", "page", "alt", "accent", "inverse"],
    # hub: the three practice cards (page), how they fit together (alt), the gold CTA
    "Services": ["inverse", "page", "alt", "accent", "inverse"],
    # Partnerships: what we do (page), the moved US proof band (alt), how we work (page), who it is for (alt), the gold CTA
    "partnerships": ["inverse", "page", "alt", "page", "alt", "accent", "inverse"],
    # the four B2B Partnerships service pages: the detail (page), the other services (alt), the gold CTA
    "partnerships/market-entry-research": ["inverse", "page", "alt", "accent", "inverse"],
    "partnerships/channel-strategy": ["inverse", "page", "alt", "accent", "inverse"],
    "partnerships/partner-introductions": ["inverse", "page", "alt", "accent", "inverse"],
    "partnerships/regional-expansion": ["inverse", "page", "alt", "accent", "inverse"],
    # the three AI Solutions and three Digital Presence service pages: the same three bands
    "ai-solutions/custom-applications": ["inverse", "page", "alt", "accent", "inverse"],
    "ai-solutions/workflow-automation": ["inverse", "page", "alt", "accent", "inverse"],
    "ai-solutions/operational-efficiency": ["inverse", "page", "alt", "accent", "inverse"],
    "digital-presence/websites": ["inverse", "page", "alt", "accent", "inverse"],
    "digital-presence/digital-marketing": ["inverse", "page", "alt", "accent", "inverse"],
    "digital-presence/community-content": ["inverse", "page", "alt", "accent", "inverse"],
    # AI Solutions and Digital Presence: what we do (page), how we work (alt), who it is for (page), the gold CTA
    "ai-solutions": ["inverse", "page", "alt", "page", "accent", "inverse"],
    "digital-presence": ["inverse", "page", "alt", "page", "accent", "inverse"],
    "Projects": ["inverse", "page", "alt", "accent", "inverse"],
    "BizCheck": ["inverse", "page", "alt", "page", "alt", "inverse"],
    "Contact": ["inverse", "inverse"],
    # Sprint 6: the 404 hero, then the footer it now carries
    "404": ["inverse", "inverse"],
}


@pytest.fixture(scope="module")
def soups():
    return {stem: BeautifulSoup(html, "html.parser") for stem, html in build.render_all().items()}


def _surface(el):
    found = [c[len("surface-"):] for c in el.get("class", []) if c in SURFACES]
    return found[0] if found else None


def _bands(soup):
    """Top-level page bands in order, nav and drawer excluded."""
    out = []
    for el in soup.body.find_all(True, recursive=False):
        if el.name in ("script", "nav") or "mobile-drawer" in el.get("class", []):
            continue
        if _surface(el):
            out.append(el)
        elif el.name == "main":
            # <main id="main"> is a wrapper, not a band: the bands inside it count in order.
            out.extend(c for c in el.find_all(True, recursive=False) if _surface(c))
    return out


def test_inverse_surface_only_on_hero_nav_drawer_footer(soups):
    for stem, soup in soups.items():
        allowed = set()
        for sel in ("nav.nav", ".mobile-drawer", "footer.footer", *HEROES):
            allowed.update(id(e) for e in soup.select(sel))
        for el in soup.select(".surface-inverse"):
            assert id(el) in allowed, f"{stem}: <{el.name} class={el.get('class')}> is navy but is not hero/nav/drawer/footer"


@pytest.mark.parametrize("stem", list(BAND_MAP))
def test_band_map(soups, stem):
    assert [_surface(b) for b in _bands(soups[stem])] == BAND_MAP[stem]


def test_no_two_adjacent_bands_share_a_surface(soups):
    for stem, soup in soups.items():
        surfaces = [_surface(b) for b in _bands(soup)]
        for a, b in zip(surfaces, surfaces[1:]):
            # Contact and the 404 are a single hero followed by the footer: both deliberately navy.
            if stem in ("Contact", "404"):
                continue
            assert a != b, f"{stem}: adjacent bands both surface-{a}: {surfaces}"


def test_final_band_is_the_gold_cta(soups):
    seen = 0
    for stem, soup in soups.items():
        ctas = soup.select("section.cta")
        for cta in ctas:
            assert _surface(cta) == "accent", f"{stem}: .cta band is not surface-accent"
        if ctas:
            seen += 1
            content_bands = [b for b in _bands(soup) if b.name != "footer"]
            assert content_bands[-1] is ctas[-1], f"{stem}: the CTA is not the last band before the footer"
        for el in soup.select(".surface-accent"):
            assert "cta" in el.get("class", []), f"{stem}: surface-accent used outside the CTA band"
    assert seen == 17, "Home, About, Services, the three pillars, the ten service pages and Projects close with a CTA"


def test_cards_use_the_card_surface(soups):
    checked = 0
    for stem, soup in soups.items():
        for el in soup.select(".project-card, .site-card, .report-card, .sample-report, #submit .form-card"):
            checked += 1
            assert "surface-card" in el.get("class", []), f"{stem}: <{el.name} class={el.get('class')}> is not surface-card"
            assert "surface-inverse" not in el.get("class", [])
    assert checked == 14


def test_bizcheck_intake_has_no_decorative_canvas(soups):
    soup = soups["BizCheck"]
    assert soup.select_one("#iris2") is None
    assert soup.select_one("#iris") is not None, "the hero iris canvas stays"


def test_site_js_tolerates_a_missing_canvas(root):
    js = (root / "assets" / "site.js").read_text(encoding="utf-8")
    assert "iris2" not in js
    assert 'getElementById("iris")' in js and "if (canvas && !reduce)" in js


def test_home_rhythm_still_alternates(soups):
    """The letters band replaces the marquee as the first surface-alt band right after the hero."""
    soup = soups["index"]
    assert soup.select_one(".marquee") is None
    bands = _bands(soup)
    assert "letters" in bands[1].get("class", []) and _surface(bands[1]) == "alt"
    assert [_surface(b) for b in bands][:4] == ["inverse", "alt", "page", "alt"]


def test_band_map_covers_every_page():
    assert set(BAND_MAP) == set(build.PAGES)
