"""Static accessibility lint over the generated root pages, ratcheted.

`lint_page` is pure: (stem, html) -> [(rule_id, detail)]. The ratchet file
tests/a11y_known_issues.json records today's counts per "<stem>|<rule>"; the
suite fails on any increase (or any new key) and on any decrease that has not
been recorded (run `python tools/a11y_ratchet.py --update`).
"""
import json
import re
from collections import Counter

import pytest
from bs4 import BeautifulSoup

from conftest import ROOT, PAGES

KNOWN = ROOT / "tests" / "a11y_known_issues.json"
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


def _known() -> dict[str, int]:
    return json.loads(KNOWN.read_text(encoding="utf-8")).get("static", {})


def test_static_lint_has_no_new_problems():
    known, now = _known(), current_static()
    worse = {k: (known.get(k, 0), n) for k, n in now.items() if n > known.get(k, 0)}
    assert not worse, f"static a11y regressions (recorded, now): {worse}"


def test_static_ratchet_is_tight():
    known, now = _known(), current_static()
    better = {k: (n, now.get(k, 0)) for k, n in known.items() if now.get(k, 0) < n}
    assert not better, (
        f"static a11y problems fixed but ratchet not lowered (recorded, now): {better}. "
        "Run `python tools/a11y_ratchet.py --update` and commit tests/a11y_known_issues.json."
    )


# ---- the linter itself: each rule fires on a minimal bad page ----

GOOD = (
    '<html lang="en"><body><a href="#main">Skip</a><nav><a href="/x">X</a></nav>'
    '<main id="main"><h1>T</h1><h2>S</h2><img src="a.png" alt="a"></main></body></html>'
)


def _rules(html):
    return {r for r, _ in lint_page("t", html)}


def test_linter_accepts_a_clean_page():
    assert lint_page("t", GOOD) == []


@pytest.mark.parametrize("html,rule", [
    ('<html lang="en"><body><h1>x</h1></body></html>', "main-landmark"),
    (GOOD.replace("<h1>T</h1>", "<h1>T</h1><h1>U</h1>"), "h1-count"),
    (GOOD.replace("<h2>S</h2>", "<h3>S</h3>"), "heading-order"),
    (GOOD.replace('<html lang="en">', "<html>"), "html-lang"),
    (GOOD.replace(' alt="a"', ""), "img-alt"),
    (GOOD.replace("</main>", '<input name="q"></main>'), "form-labels"),
    (GOOD.replace("</main>", '<p id="a"></p><p id="a"></p></main>'), "unique-ids"),
    (GOOD.replace("</main>", '<a href="/y"></a></main>'), "link-names"),
    (GOOD.replace("</main>", "<button></button></main>"), "button-names"),
    (GOOD.replace("</main>", '<div aria-hidden="true"><a href="/z">z</a></div></main>'), "aria-hidden-focusable"),
    (GOOD.replace("</main>", '<a href="/z" tabindex="3">z</a></main>'), "tabindex-positive"),
    (GOOD.replace('<a href="#main">Skip</a>', ""), "skip-link"),
    (GOOD.replace("</main>", '<a href="http://e" target="_blank">e</a></main>'), "target-blank-rel"),
])
def test_linter_flags_each_rule(html, rule):
    assert rule in _rules(html)
