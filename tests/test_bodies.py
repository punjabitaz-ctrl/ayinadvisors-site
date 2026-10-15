import json

from conftest import ROOT, PAGES, baseline_html
from parity import page_facts

BODIES = ROOT / "templates" / "pages"


def test_every_page_has_a_body_file():
    for stem in PAGES:
        assert (BODIES / f"{stem}.body.frag").exists(), stem


def test_bodies_contain_no_chrome():
    for stem in PAGES:
        body = (BODIES / f"{stem}.body.frag").read_text(encoding="utf-8")
        assert '<nav class="nav"' not in body, f"{stem} body still contains nav"
        assert "<footer" not in body, f"{stem} body still contains footer"


def test_inline_blocks_are_preserved_exactly():
    for stem in PAGES:
        base = page_facts(baseline_html(stem))
        parts = json.loads((BODIES / f"{stem}.json").read_text(encoding="utf-8"))
        body = (BODIES / f"{stem}.body.frag").read_text(encoding="utf-8")
        haystack = parts["head_extra"] + "\n" + parts["body_scripts"] + "\n" + body
        for block in base["inline_styles"] + base["inline_scripts"]:
            if block.strip():
                assert block.strip() in haystack, f"{stem} lost an inline block"
