#!/usr/bin/env python3
"""Render the site from content/site.json + templates/ to .html at the repo root."""
import json
import re
from pathlib import Path
from xml.sax.saxutils import escape
from jinja2 import Environment, FileSystemLoader, select_autoescape

from tools import images as image_tools
from tools import theme as theme_tools

ROOT = Path(__file__).resolve().parent
# Pages are defined by content/site.json, in the order listed there.
PAGES = list(json.loads((ROOT / "content" / "site.json").read_text(encoding="utf-8"))["pages"])

# Autoescape is OFF: page bodies are pre-authored HTML, not user input.
# Plain-text head/nav/footer values are escaped explicitly with |e in the templates.
env = Environment(
    loader=FileSystemLoader(ROOT / "templates"),
    autoescape=select_autoescape(enabled_extensions=(), default=False),
    keep_trailing_newline=True,
)


def _fail(message: str):
    raise ValueError(message)


env.globals["fail"] = _fail


def root_for(stem: str) -> str:
    """URL prefix that reaches the site root from a page: "" for a root page, "../" per folder level."""
    return "../" * stem.count("/")


def _root_url(href: str, root: str) -> str:
    """Prefix a site-relative href with `root`; absolute URLs, mailto:, in-page #fragments and /paths pass through."""
    if not root or ":" in href or href.startswith(("#", "/")):
        return href
    return root + href


env.filters["ru"] = _root_url


def page_root(stem: str) -> str:
    """The root prefix a page renders with: its site.json "root" when set, else root_for(stem).

    The 404 page sets "/": Cloudflare serves it for a missing URL at any depth (/partnerships/no-such-page), so its
    links and assets must start at the site root rather than at the folder of whatever URL was asked for.
    """
    return load_site()["pages"][stem].get("root", root_for(stem))


def load_site() -> dict:
    return json.loads((ROOT / "content" / "site.json").read_text(encoding="utf-8"))


def load_services() -> dict:
    """content/services.json: the three pillars and their sub-services (feeds the hub and pillar pages)."""
    return json.loads((ROOT / "content" / "services.json").read_text(encoding="utf-8"))


SITE_URL = "https://ayinadvisors.com"


_SLOT = re.compile(r"<image-slot(?=[\s>])([^>]*)></image-slot>")
_ATTR = re.compile(r'([\w-]+)="([^"]*)"')


def expand_image_slots(html: str, root: str = "") -> str:
    """Replace <image-slot slug sizes [loading] [class]> placeholders with <picture> markup.

    An unknown slug raises KeyError naming it, so a typo can never ship. `root` prefixes the image paths for
    a page in a subfolder.
    """
    registry = image_tools.load_registry(ROOT / "content" / "images.json")

    def one(m: re.Match) -> str:
        attrs = dict(_ATTR.findall(m.group(1)))
        if "slug" not in attrs:
            raise ValueError("image-slot without a slug")
        if not attrs.get("sizes"):
            raise ValueError(f"image-slot {attrs['slug']!r} needs a sizes attribute")
        return image_tools.render_picture(
            attrs["slug"], attrs["sizes"], attrs.get("loading", "lazy"), attrs.get("class", ""),
            registry=registry, prefix=root,
        )

    return _SLOT.sub(one, html)


ORG_ID = f"{SITE_URL}/#organization"
FOUNDER_ID = f"{SITE_URL}/#founder"


def _name(title: str) -> str:
    """A page title without the " - AYiN Advisors" brand suffix."""
    return title.rsplit(" - AYiN Advisors", 1)[0]


def structured_data(stem: str, site: dict | None = None, services: dict | None = None) -> list[dict]:
    """schema.org JSON-LD for a page, built only from what the site itself states (site.json, services.json, the footer).

    Home: the organization, its founder and the website. About: the organization and founder. Services, pillar and
    service pages: a breadcrumb trail; pillar and service pages also describe the service. Other pages: nothing.
    """
    site = site or load_site()
    page = site["pages"][stem]
    org = {
        "@type": "Organization", "@id": ORG_ID, "name": "AYiN Advisors", "url": f"{SITE_URL}/",
        "email": "hello@ayinadvisors.com", "description": site["pages"]["index"]["description"],
        "image": f"{SITE_URL}/og-image.jpg",
        "address": {"@type": "PostalAddress", "addressLocality": "New York", "addressCountry": "US"},
        "founder": {"@id": FOUNDER_ID},
    }
    founder = {
        "@type": "Person", "@id": FOUNDER_ID, "name": "Taz Abbas", "jobTitle": "Managing Partner",
        "image": f"{SITE_URL}/assets/taz-abbas.jpg", "worksFor": {"@id": ORG_ID},
        "sameAs": ["https://linkedin.com/in/tazabbas"],
    }
    if stem == "index":
        website = {"@type": "WebSite", "@id": f"{SITE_URL}/#website", "url": f"{SITE_URL}/", "name": "AYiN Advisors",
                   "publisher": {"@id": ORG_ID}}
        return [{"@context": "https://schema.org", "@graph": [org, founder, website]}]
    if stem == "About":
        return [{"@context": "https://schema.org", "@graph": [org, founder]}]
    kind = page.get("template")
    if kind not in ("hub", "pillar", "service"):
        return []
    pages = site["pages"]
    trail = [("Home", f"{SITE_URL}/"), ("Services", pages["Services"]["canonical"])]
    pillar = next((p for p in (services or load_services())["pillars"] if p["stem"] == page.get("pillar", stem)), None)
    if kind in ("pillar", "service"):
        trail.append((pillar["name"], pages[pillar["stem"]]["canonical"]))
    if kind == "service":
        trail.append((_name(page["title"]), page["canonical"]))
    out = [{"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": i, "name": n, "item": u} for i, (n, u) in enumerate(trail, 1)]}]
    if kind in ("pillar", "service"):
        out.append({"@context": "https://schema.org", "@type": "Service", "name": _name(page["title"]),
                    "description": page["description"], "url": page["canonical"],
                    "serviceType": pillar["name"], "provider": {"@type": "Organization", "@id": ORG_ID, "name": "AYiN Advisors"}})
    return out


def jsonld_tags(stem: str) -> str:
    """The page's structured data as <script type="application/ld+json"> tags; "</" is escaped so no value can close the tag."""
    return "\n".join(
        '<script type="application/ld+json">' + json.dumps(d, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/") + "</script>"
        for d in structured_data(stem)
    )


def clean_href(href: str) -> str:
    """The extensionless form of an internal page link: "Contact.html?practice=x" -> "Contact?practice=x", "../index.html" -> "/".

    Cloudflare Pages serves /About.html at /About and 308-redirects the .html form, so linking the clean address saves
    a redirect on every click. Absolute URLs, mailto:, in-page #fragments and non-page files pass through unchanged.
    """
    if ":" in href or href.startswith("#"):
        return href
    rest, hsep, frag = href.partition("#")
    path, qsep, query = rest.partition("?")
    if not path.endswith(".html"):
        return href
    path = path[: -len(".html")]
    if path == "index" or path.endswith("/index"):
        path = "/"  # the home page, from any folder: the site is always served at the domain root
    return path + qsep + query + hsep + frag


_HREF = re.compile(r'(\shref=")([^"]*)(")')


def clean_links(html: str) -> str:
    """Rewrite every internal .html href in a rendered page to its extensionless address (see clean_href)."""
    return _HREF.sub(lambda m: m.group(1) + clean_href(m.group(2)) + m.group(3), html)


def render_page(stem: str, body: str, head_extra: str = "", body_scripts: str = "") -> str:
    site = load_site()
    if stem not in site["pages"]:
        raise KeyError(f"unknown page {stem!r}; known pages: {', '.join(site['pages'])}")
    root = page_root(stem)
    return clean_links(env.get_template("base.j2").render(
        site=site,
        page=site["pages"][stem],
        stem=stem,
        root=root,
        body=body,
        head_extra=head_extra,
        body_scripts=body_scripts,
        logo=env.get_template("_logo.j2").render(root=root),
        footer=env.get_template("_footer.j2").render(site=site, root=root),
        jsonld=jsonld_tags(stem),
    ))


def template_kind(stem: str) -> str | None:
    """"hub", "pillar", "service" or "notfound" for a template-rendered page, None for a page made of a .frag and a .json."""
    kind = load_site()["pages"][stem].get("template")
    if kind not in (None, "hub", "pillar", "service", "notfound"):
        raise ValueError(f"{stem}: unknown template {kind!r}")
    return kind


def process_for(pillar: dict | None, services: dict | None = None) -> dict:
    """The "How we work" copy for a pillar: the shared process, with the pillar's optional overrides applied.

    A pillar may carry "process": {"intro": ..., "final": {"name", "text"}}; "final" replaces the last step.
    """
    base = (services or load_services())["process"]
    out = {**base, "steps": [dict(s) for s in base["steps"]]}
    over = (pillar or {}).get("process") or {}
    if "intro" in over:
        out["intro"] = over["intro"]
    if "final" in over:
        out["steps"][-1] = dict(over["final"])
    return out


def page_parts(stem: str) -> tuple[str, str, str]:
    """(body, head_extra, body_scripts) for a page, before image slots are expanded.

    Hand-authored pages read templates/pages/<stem>.body.frag and <stem>.json. Template pages (site.json
    "template": "hub" | "pillar" | "service" | "notfound") render templates/<kind>.body.j2 with the services data, and
    take their head from templates/_head_template_page.j2 (the 404, "notfound", from templates/_head_notfound.j2); they
    have no .frag or .json and no body scripts.
    """
    kind = template_kind(stem)
    if kind is None:
        parts = json.loads((ROOT / "templates" / "pages" / f"{stem}.json").read_text(encoding="utf-8"))
        body = (ROOT / "templates" / "pages" / f"{stem}.body.frag").read_text(encoding="utf-8")
        return body, parts.get("head_extra", ""), parts.get("body_scripts", "")
    site = load_site()
    page = site["pages"][stem]
    services = load_services()
    pillars = services["pillars"]
    ctx = {"site": site, "page": page, "stem": stem, "root": page_root(stem), "kind": kind, "pillars": pillars,
           "pillar": None, "service": None, "hub": services["hub"], "process": services["process"]}
    if kind in ("pillar", "service"):
        ctx["pillar"] = next((p for p in pillars if p["slug"] == page.get("pillar")), None)
        if ctx["pillar"] is None:
            raise KeyError(f"{stem}: no pillar {page.get('pillar')!r} in content/services.json")
        ctx["process"] = process_for(ctx["pillar"], services)
    if kind == "service":
        ctx["service"] = next((s for s in ctx["pillar"]["services"] if s["slug"] == page.get("service")), None)
        if ctx["service"] is None or "detail" not in ctx["service"]:
            raise KeyError(f"{stem}: no service {page.get('service')!r} with a detail in pillar {page.get('pillar')!r}")
    return (
        env.get_template(f"{kind}.body.j2").render(**ctx),
        env.get_template("_head_notfound.j2" if kind == "notfound" else "_head_template_page.j2").render(**ctx),
        "",
    )


def render_all() -> dict[str, str]:
    out = {}
    for stem in PAGES:
        body, head_extra, body_scripts = page_parts(stem)
        out[stem] = render_page(stem, expand_image_slots(body, page_root(stem)), head_extra, body_scripts)
    return out


def render_sitemap() -> str:
    """sitemap.xml: every page of site.json that carries a "sitemap" entry, in site.json order.

    A page's "lastmod" (YYYY-MM-DD) is set by hand in site.json: bump it when the page's content changes, so search
    engines can tell a changed page from an unchanged one.
    """
    rows = []
    for stem, page in load_site()["pages"].items():
        if "sitemap" not in page:
            continue
        loc = page["canonical"]
        lastmod = f"<lastmod>{escape(page['sitemap']['lastmod'])}</lastmod>" if "lastmod" in page["sitemap"] else ""
        rows.append(
            f"  <url><loc>{escape(loc)}</loc>{lastmod}<changefreq>monthly</changefreq>"
            f"<priority>{escape(str(page['sitemap']['priority']))}</priority></url>"
        )
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
        *rows,
        "</urlset>",
    ]
    return "\n".join(lines) + "\n"


def render_theme() -> str:
    """assets/theme.css from content/theme.json; refuses to emit a failing contrast pairing."""
    theme = theme_tools.load_theme(ROOT / "content" / "theme.json")
    resolved = theme_tools.resolve(theme)
    bad = theme_tools.failures(resolved, theme)
    if bad:
        raise SystemExit("theme contrast failures:\n  " + "\n  ".join(bad))
    return theme_tools.render_css(resolved)


def main() -> None:
    (ROOT / "assets").mkdir(exist_ok=True)
    (ROOT / "assets" / "theme.css").write_text(render_theme(), encoding="utf-8", newline="\n")
    print("  wrote assets/theme.css")
    for stem, html in render_all().items():
        (ROOT / f"{stem}.html").parent.mkdir(parents=True, exist_ok=True)
        (ROOT / f"{stem}.html").write_text(html, encoding="utf-8")
        print(f"  wrote {stem}.html")
    (ROOT / "sitemap.xml").write_text(render_sitemap(), encoding="utf-8", newline="\n")
    print("  wrote sitemap.xml")


def check() -> list[str]:
    """Return generated files that are missing or differ from a fresh render."""
    stale = []
    for stem, fresh in render_all().items():
        path = ROOT / f"{stem}.html"
        if not path.exists() or path.read_text(encoding="utf-8") != fresh:
            stale.append(f"{stem}.html")
    sitemap = ROOT / "sitemap.xml"
    if not sitemap.exists() or sitemap.read_text(encoding="utf-8") != render_sitemap():
        stale.append("sitemap.xml")
    css = ROOT / "assets" / "theme.css"
    if not css.exists() or css.read_text(encoding="utf-8") != render_theme():
        stale.append("assets/theme.css")
    return stale


if __name__ == "__main__":
    import sys

    if "--check" in sys.argv:
        stale = check()
        print("  stale:", ", ".join(stale) if stale else "none")
        sys.exit(1 if stale else 0)
    main()
