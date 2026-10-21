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
        # the theme head script (Phase 2c) lives in the shared base template, not in a page file
        shared = (ROOT / "templates" / "base.j2").read_text(encoding="utf-8")
        haystack = parts["head_extra"] + "\n" + parts["body_scripts"] + "\n" + body + "\n" + shared
        for block in base["inline_styles"] + base["inline_scripts"]:
            if block.strip():
                assert block.strip() in haystack, f"{stem} lost an inline block"


def test_home_why_stats_have_one_numeral_each():
    import re
    body = (BODIES / "index.body.frag").read_text(encoding="utf-8")
    block = body.split('class="why-stats', 1)[1].split("</section>", 1)[0]
    stats = re.findall(r'<div class="why-stat">(.*?)</div></div>', block, re.S)
    assert len(stats) == 4
    for s in stats:
        assert s.count('class="n"') == 1, s
    assert len(re.findall(r'class="n"', block)) == 4
    for bad in ("27T", "50 States", "Trillion"):
        assert bad not in block, bad
