#!/usr/bin/env python3
"""Render the site from content/site.json + templates/ to .html at the repo root."""
import json
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape

ROOT = Path(__file__).resolve().parent
PAGES = ["index", "About", "Services", "Projects", "BizCheck", "Contact", "404"]

# Autoescape is OFF: page bodies are pre-authored HTML, not user input.
# Plain-text head/nav/footer values are escaped explicitly with |e in the templates.
env = Environment(
    loader=FileSystemLoader(ROOT / "templates"),
    autoescape=select_autoescape(enabled_extensions=(), default=False),
    keep_trailing_newline=True,
)


def load_site() -> dict:
    return json.loads((ROOT / "content" / "site.json").read_text(encoding="utf-8"))


def render_page(stem: str, body: str, head_extra: str = "", body_scripts: str = "") -> str:
    site = load_site()
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
            (ROOT / "templates" / "pages" / f"{stem}.body.frag").read_text(encoding="utf-8"),
            parts.get("head_extra", ""),
            parts.get("body_scripts", ""),
        )
    return out


def main() -> None:
    for stem, html in render_all().items():
        (ROOT / f"{stem}.html").write_text(html, encoding="utf-8")
        print(f"  wrote {stem}.html")


def check() -> list[str]:
    """Return generated files whose content differs from a fresh render."""
    return [
        f"{stem}.html"
        for stem, fresh in render_all().items()
        if (ROOT / f"{stem}.html").read_text(encoding="utf-8") != fresh
    ]


if __name__ == "__main__":
    import sys

    if "--check" in sys.argv:
        stale = check()
        print("  stale:", ", ".join(stale) if stale else "none")
        sys.exit(1 if stale else 0)
    main()
