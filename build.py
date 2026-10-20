#!/usr/bin/env python3
"""Render the site from content/site.json + templates/ to .html at the repo root."""
import json
import re
from pathlib import Path
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


def load_site() -> dict:
    return json.loads((ROOT / "content" / "site.json").read_text(encoding="utf-8"))


_SLOT = re.compile(r"<image-slot(?=[\s>])([^>]*)></image-slot>")
_ATTR = re.compile(r'([\w-]+)="([^"]*)"')


def expand_image_slots(html: str) -> str:
    """Replace <image-slot slug sizes [loading] [class]> placeholders with <picture> markup.

    An unknown slug raises KeyError naming it, so a typo can never ship.
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
            registry=registry,
        )

    return _SLOT.sub(one, html)


def render_page(stem: str, body: str, head_extra: str = "", body_scripts: str = "") -> str:
    site = load_site()
    if stem not in site["pages"]:
        raise KeyError(f"unknown page {stem!r}; known pages: {', '.join(site['pages'])}")
    return env.get_template("base.j2").render(
        site=site,
        page=site["pages"][stem],
        body=body,
        head_extra=head_extra,
        body_scripts=body_scripts,
        logo=env.get_template("_logo.j2").render(),
        footer=env.get_template("_footer.j2").render(site=site),
    )


def render_all() -> dict[str, str]:
    out = {}
    for stem in PAGES:
        parts = json.loads((ROOT / "templates" / "pages" / f"{stem}.json").read_text(encoding="utf-8"))
        out[stem] = render_page(
            stem,
            expand_image_slots(
                (ROOT / "templates" / "pages" / f"{stem}.body.frag").read_text(encoding="utf-8")
            ),
            parts.get("head_extra", ""),
            parts.get("body_scripts", ""),
        )
    return out


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
        (ROOT / f"{stem}.html").write_text(html, encoding="utf-8")
        print(f"  wrote {stem}.html")


def check() -> list[str]:
    """Return generated files that are missing or differ from a fresh render."""
    stale = []
    for stem, fresh in render_all().items():
        path = ROOT / f"{stem}.html"
        if not path.exists() or path.read_text(encoding="utf-8") != fresh:
            stale.append(f"{stem}.html")
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
