import subprocess

import build
from conftest import ROOT, PAGES


def _tracked_html() -> set[str]:
    out = subprocess.run(
        ["git", "ls-files", "*.html"], cwd=ROOT, capture_output=True,
        text=True, encoding="utf-8", check=True,
    ).stdout.split()
    return set(out)


def test_only_the_pages_in_site_json_are_tracked_html():
    """Cloudflare serves the repo root, so a tracked .html anywhere else would become a public page."""
    expected = {f"{s}.html" for s in build.live_pages()}  # a scheduled post has no page until its morning
    assert expected == {f"{s}.html" for s in PAGES}
    assert len(expected) >= 10
    got = _tracked_html()
    assert got == expected, {"unexpected": sorted(got - expected), "missing": sorted(expected - got)}


def test_templates_and_fragments_are_never_html():
    """Template-rendered pages keep their sources as .j2, hand-authored pages as .frag, so neither is served as a page."""
    for p in (ROOT / "templates").rglob("*"):
        if p.is_file():
            assert p.suffix in (".j2", ".frag", ".json"), p
