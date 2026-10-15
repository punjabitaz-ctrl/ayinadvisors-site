import re
from bs4 import BeautifulSoup


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
    }


def diff_facts(a: dict, b: dict) -> list[str]:
    return [
        f"{k}:\n  baseline={a[k]!r}\n  built   ={b[k]!r}"
        for k in a if a[k] != b[k]
    ]
