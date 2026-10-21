"""Static accessibility lint over the generated root pages: every rule must report zero problems.

`lint_page` is pure: (stem, html) -> [(rule_id, detail)].
"""
import re
from collections import Counter

import pytest
from bs4 import BeautifulSoup

from conftest import ROOT, PAGES

FOCUSABLE_SELECTOR = (
    "a[href], button, input:not([type=hidden]), select, textarea, summary, "
    "[tabindex], [contenteditable=''], [contenteditable=true]"
)


def _is_focusable(el) -> bool:
    if el.has_attr("disabled"):
        return False
    ti = (el.get("tabindex") or "").strip()
    if ti.lstrip("-").isdigit() and int(ti) < 0:
        return False
    return True


def _text(el) -> str:
    return re.sub(r"\s+", " ", el.get_text(" ", strip=True)) if el is not None else ""


def _has_accessible_name(el, soup) -> bool:
    if (el.get("aria-label") or "").strip() or (el.get("title") or "").strip():
        return True
    for i in (el.get("aria-labelledby") or "").split():
        if _text(soup.find(id=i)):
            return True
    if _text(el):
        return True
    return any((img.get("alt") or "").strip() for img in el.find_all("img"))


def lint_page(stem: str, html: str) -> list[tuple[str, str]]:
    soup = BeautifulSoup(html, "html.parser")
    out: list[tuple[str, str]] = []

    mains = soup.find_all("main") + soup.find_all(attrs={"role": "main"})
    if len(mains) != 1:
        out.append(("main-landmark", f"expected exactly one main landmark, found {len(mains)}"))

    h1s = soup.find_all("h1")
    if len(h1s) != 1:
        out.append(("h1-count", f"expected exactly one h1, found {len(h1s)}"))

    # A heading may be at most one level deeper than the previous heading.
    prev = 0
    for h in soup.find_all(re.compile(r"^h[1-6]$")):
        lvl = int(h.name[1])
        if prev and lvl > prev + 1:
            out.append(("heading-order", f"{h.name} follows h{prev}: {_text(h)[:50]!r}"))
        prev = lvl

    html_el = soup.find("html")
    if not html_el or not (html_el.get("lang") or "").strip():
        out.append(("html-lang", "<html> has no lang attribute"))

    # alt="" is allowed: it marks the image decorative.
    for img in soup.find_all("img"):
        if img.get("alt") is None:
            out.append(("img-alt", f"img without alt: {img.get('src', '')}"))

    for ctl in soup.find_all(["input", "select", "textarea"]):
        if ctl.name == "input" and (ctl.get("type") or "text").lower() in (
            "hidden", "submit", "button", "reset", "image"
        ):
            continue
        cid = ctl.get("id")
        labelled = (
            (ctl.get("aria-label") or "").strip()
            or (ctl.get("aria-labelledby") or "").strip()
            or (ctl.get("title") or "").strip()
            or (cid and soup.find("label", attrs={"for": cid}))
            or ctl.find_parent("label")
        )
        if not labelled:
            out.append(("form-labels", f"<{ctl.name}> '{ctl.get('name') or cid or ''}' has no label"))

    ids = Counter(e["id"] for e in soup.find_all(id=True))
    for i, n in sorted(ids.items()):
        if n > 1:
            out.append(("unique-ids", f"id {i!r} used {n} times"))

    for a in soup.find_all("a", href=True):
        if not _has_accessible_name(a, soup):
            out.append(("link-names", f"link to {a['href']!r} has no accessible name"))

    for b in soup.find_all("button"):
        if not _has_accessible_name(b, soup):
            out.append(("button-names", f"button has no accessible name: {str(b)[:60]!r}"))
    for i in soup.find_all("input", attrs={"type": re.compile("^(submit|button|reset)$", re.I)}):
        if not (i.get("value") or i.get("aria-label") or i.get("title")):
            out.append(("button-names", "input button has no accessible name"))

    # One finding per aria-hidden subtree that exposes a focusable control.
    for el in soup.find_all(attrs={"aria-hidden": "true"}):
        for c in [el] + el.select(FOCUSABLE_SELECTOR):
            if not _is_focusable(c):
                continue
            if c.name == "input" and (c.get("type") or "").lower() == "hidden":
                continue
            if c.name == "a" and not c.has_attr("href") and not c.has_attr("tabindex"):
                continue
            if c.has_attr("tabindex") or c.name in ("a", "button", "input", "select", "textarea", "summary"):
                out.append(("aria-hidden-focusable", f"focusable <{c.name}> inside aria-hidden"))
                break

    for el in soup.find_all(attrs={"tabindex": True}):
        v = el["tabindex"].strip()
        if v.isdigit() and int(v) > 0:
            out.append(("tabindex-positive", f"<{el.name}> has tabindex={v}"))

    # The first focusable element in <body> must be an in-page link to an existing id.
    body = soup.find("body")
    first = next((e for e in (body.select(FOCUSABLE_SELECTOR) if body else []) if _is_focusable(e)), None)
    href = (first.get("href") or "") if first is not None and first.name == "a" else ""
    if not (href.startswith("#") and len(href) > 1 and soup.find(id=href[1:])):
        out.append(("skip-link", "first focusable element is not a skip link to an in-page target"))

    for a in soup.find_all("a", target="_blank"):
        rel = a.get("rel") or []
        rel = set(rel if isinstance(rel, list) else str(rel).split())
        if not ({"noopener", "noreferrer"} & rel):
            out.append(("target-blank-rel", f"target=_blank without rel=noopener: {a.get('href', '')}"))

    return out


def current_static() -> dict[str, int]:
    counts: Counter = Counter()
    for stem in PAGES:
        html = (ROOT / f"{stem}.html").read_text(encoding="utf-8")
        for rule, _ in lint_page(stem, html):
            counts[f"{stem}|{rule}"] += 1
    return dict(sorted(counts.items()))


def test_static_lint_reports_nothing():
    found = {k: n for k, n in current_static().items() if n}
    assert not found, f"static a11y problems (page|rule: count): {found}"


@pytest.mark.parametrize("stem", PAGES)
def test_navigation_landmarks_are_labelled_and_the_toggle_is_wired(stem):
    soup = BeautifulSoup((ROOT / f"{stem}.html").read_text(encoding="utf-8"), "html.parser")
    navs = {n.get("aria-label"): n for n in soup.find_all("nav")}
    assert set(navs) >= {"Primary", "Mobile menu"}, f"{stem}: nav landmarks are {sorted(map(str, navs))}"
    assert all(n.get("aria-label") for n in soup.find_all("nav")), f"{stem}: every <nav> needs a unique label"
    drawer = navs["Mobile menu"]
    toggle = soup.select_one("button.nav-toggle")
    assert drawer.get("id") and toggle.get("aria-controls") == drawer["id"]
    assert toggle.get("aria-expanded") == "false" and toggle.get("type") == "button"
    assert not drawer.get("role"), "the drawer is a real <nav>; role=navigation is redundant"


@pytest.mark.parametrize("stem", [s for s in PAGES if s != "404"])
def test_current_page_link_is_exposed_to_assistive_tech(stem):
    """aria-current="page" only on the link to this very page; a page without its own nav entry (a pillar page)
    marks its section link (Services) aria-current="true" instead. Both navigations agree."""
    soup = BeautifulSoup((ROOT / f"{stem}.html").read_text(encoding="utf-8"), "html.parser")
    active = soup.select("nav.nav a.nav-link.active")
    assert len(active) == 1, f"{stem}: expected one active nav link, found {len(active)}"
    own = active[0]["href"] == f"{stem}.html"
    want = "page" if own else "true"
    assert active[0].get("aria-current") == want
    assert len(soup.select("nav.nav a[aria-current]")) == 1
    assert len(soup.select("nav.nav a[aria-current='page']")) == (1 if own else 0)
    drawer = soup.select(".mobile-drawer a[aria-current]")
    assert len(drawer) == 1 and drawer[0]["aria-current"] == want and drawer[0]["href"] == active[0]["href"]
