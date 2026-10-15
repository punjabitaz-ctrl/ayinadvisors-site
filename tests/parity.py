import re
from bs4 import BeautifulSoup, Comment, Doctype, NavigableString


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", s or "").strip()


def _head_children(soup) -> list:
    out = []
    for el in soup.head.find_all(True, recursive=False):
        if el.name == "title":
            continue
        if el.name == "meta" and (
            el.get("charset") is not None or el.get("name") in ("viewport", "description")
        ):
            continue
        if el.name == "link" and "canonical" in (el.get("rel") or []):
            continue
        attrs = tuple(sorted(
            (k, " ".join(v) if isinstance(v, list) else v) for k, v in el.attrs.items()
        ))
        out.append((el.name, attrs, _norm(el.decode_contents())))
    return out


def _body_rest(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for sel in ("nav.nav", ".mobile-drawer", "footer.footer"):
        for el in soup.select(sel):
            el.decompose()
    for el in soup.find_all("script"):
        el.decompose()
    for c in soup.find_all(string=lambda t: isinstance(t, Comment)):
        c.extract()
    return _norm(soup.body.decode_contents()) if soup.body else ""


def _attrs(el) -> tuple:
    return tuple(sorted(
        (k, " ".join(v) if isinstance(v, list) else v) for k, v in el.attrs.items()
    ))


def canon_subtree(soup, selector: str) -> list:
    """Every element under the first match of `selector`, depth-first in document order.

    Entry: (depth, tag, sorted attributes, whitespace-collapsed direct text).
    """
    root = soup.select_one(selector)
    if root is None:
        return []
    out = []

    def walk(el, depth):
        text = _norm(" ".join(
            str(c) for c in el.children
            if isinstance(c, NavigableString) and not isinstance(c, Comment)
        ))
        out.append((depth, el.name, _attrs(el), text))
        for child in el.find_all(True, recursive=False):
            walk(child, depth + 1)

    walk(root, 0)
    return out


def _doc_shape(html: str) -> list:
    soup = BeautifulSoup(html, "html.parser")
    meta = lambda sel: _attrs(soup.select_one(sel)) if soup.select_one(sel) else None
    return [
        ("doctype", any(isinstance(n, Doctype) and n.lower() == "html" for n in soup.contents)),
        ("html", _attrs(soup.html) if soup.html else None),
        ("body", _attrs(soup.body) if soup.body else None),
        ("meta-charset", meta("meta[charset]")),
        ("meta-viewport", meta('meta[name="viewport"]')),
        ("nav.nav", canon_subtree(soup, "nav.nav")),
        (".mobile-drawer", canon_subtree(soup, ".mobile-drawer")),
        ("footer.footer", canon_subtree(soup, "footer.footer")),
        ("scripts", [
            (s.get("src"), _attrs(s), _norm(s.get_text())) for s in soup.find_all("script")
        ]),
    ]


def page_facts(html: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")

    nav = [
        (a.get("href"), _norm(a.get_text()), " ".join(a.get("class", [])))
        for a in soup.select(".nav-links .nav-link")
    ]
    cta = soup.select_one(".nav-cta .btn")
    nav_cta = (
        cta.get("href"),
        _norm(cta.get_text()),
        " ".join(cta.get("class", [])),
    ) if cta else None

    drawer = [
        (a.get("href"), _norm(a.get_text()))
        for a in soup.select(".mobile-drawer a")
    ]

    footer = soup.select_one("footer.footer")
    desc = soup.select_one('meta[name="description"]')
    canon = soup.select_one('link[rel="canonical"]')

    return {
        "title": _norm(soup.title.string if soup.title else ""),
        "description": desc.get("content") if desc else None,
        "canonical": canon.get("href") if canon else None,
        "nav": nav,
        "nav_cta": nav_cta,
        "drawer": drawer,
        "has_footer": footer is not None,
        "footer_links": [
            (a.get("href"), _norm(a.get_text()))
            for a in footer.select("a")
        ] if footer else [],
        "footer_text": _norm(footer.get_text()) if footer else "",
        "assets": sorted({
            e.get("href") or e.get("src")
            for e in soup.select("link[href], script[src], img[src]")
            if (e.get("href") or e.get("src", "")).startswith(("assets/", "favicon", "og-"))
        }),
        "head": _head_children(soup),
        "inline_scripts": [s.get_text() for s in soup.find_all("script") if not s.get("src")],
        "inline_styles": [s.get_text() for s in soup.find_all("style")],
        "body_rest": _body_rest(html),
        "doc_shape": _doc_shape(html),
    }
