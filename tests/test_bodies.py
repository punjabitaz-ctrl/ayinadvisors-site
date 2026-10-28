import build
from conftest import ROOT, PAGES, baseline_html
from parity import page_facts

BODIES = ROOT / "templates" / "pages"


def _hand_authored():
    return [s for s in PAGES if build.template_kind(s) is None]


def test_every_page_has_a_body_file_or_a_template():
    for stem in PAGES:
        kind = build.template_kind(stem)
        if kind is None:
            assert (BODIES / f"{stem}.body.frag").exists() and (BODIES / f"{stem}.json").exists(), stem
        else:
            # template pages have no .frag/.json to drift out of sync with their template
            assert (ROOT / "templates" / f"{kind}.body.j2").exists(), stem
            assert not (BODIES / f"{stem}.body.frag").exists() and not (BODIES / f"{stem}.json").exists(), stem


def test_bodies_contain_no_chrome():
    for stem in PAGES:
        body, _, _ = build.page_parts(stem)
        assert '<nav class="nav"' not in body, f"{stem} body still contains nav"
        assert "<footer" not in body, f"{stem} body still contains footer"


def test_inline_blocks_are_preserved_exactly():
    """Every inline <style>/<script> block of the baseline survives in the page's source parts (body + head + scripts)."""
    for stem in PAGES:
        base = page_facts(baseline_html(stem))
        body, head_extra, body_scripts = build.page_parts(stem)
        # the theme head script (Phase 2c) lives in the shared base template, not in a page file
        shared = (ROOT / "templates" / "base.j2").read_text(encoding="utf-8")
        # the JSON-LD blocks (site audit, 2026-10-28) are generated from site.json by build.structured_data
        haystack = "\n".join([head_extra, body_scripts, body, shared, build.jsonld_tags(stem)])
        for block in base["inline_styles"] + base["inline_scripts"]:
            if block.strip():
                assert block.strip() in haystack, f"{stem} lost an inline block"


def test_template_pages_are_declared_in_site_json():
    kinds = {s: build.template_kind(s) for s in PAGES}
    assert {s for s, k in kinds.items() if k == "hub"} == {"Services"}
    assert {s for s, k in kinds.items() if k == "pillar"} == {"partnerships", "ai-solutions", "digital-presence"}
    assert {s for s, k in kinds.items() if k == "service"} == {s for s in PAGES if "/" in s and not s.startswith("blog/")}
    assert {s for s, k in kinds.items() if k == "blog"} == {"blog"}
    assert {s for s, k in kinds.items() if k == "post"} == {s for s in PAGES if s.startswith("blog/")}
    assert len(PAGES) == 20 + 1 + len(build.load_blog()["posts"])
    assert {s for s, k in kinds.items() if k == "notfound"} == {"404"}  # Sprint 6: the 404 links each practice from services.json
    assert set(_hand_authored()) == {"index", "About", "Projects", "BizCheck", "Contact"}


def test_why_stats_have_one_numeral_each():
    """The numeral band moved from Home to the Partnerships proof partial (Sprint 2 Task 3). The site review
    (2026-10-27) cut it from four to two: the unsourced $24T, 70% and 3x figures were removed."""
    import re
    assert "why-stats" not in (BODIES / "index.body.frag").read_text(encoding="utf-8")
    body = (ROOT / "templates" / "partials" / "partnerships-proof.frag").read_text(encoding="utf-8")
    block = body.split('class="why-stats', 1)[1].split("</section>", 1)[0]
    stats = re.findall(r'<div class="why-stat">(.*?)</div></div>', block, re.S)
    assert len(stats) == 2
    for s in stats:
        assert s.count('class="n"') == 1, s
    assert len(re.findall(r'class="n"', block)) == 2
    for bad in ("27T", "50 States", "Trillion", 'data-count="24"', 'data-count="70"', 'data-suffix="x"'):
        assert bad not in block, bad
