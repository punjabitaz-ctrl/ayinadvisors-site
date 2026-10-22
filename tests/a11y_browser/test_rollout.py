"""Phase 2b rollout (T3): accents and motion on About, Services, Projects, BizCheck and Contact.

Every placement gets the checks the Home placement needed: nothing displaced at rest, ripple centres in empty space, no sideways scroll while assembling, final state under reduced motion.
"""
import pytest

from a11y_browser.conftest import THEMES, new_context, open_page
from a11y_browser.test_motion import FINAL_JS, _centre

pytestmark = pytest.mark.browser

ROLLOUT = ("About", "Services", "partnerships", "ai-solutions", "digital-presence", "Projects", "BizCheck")
# Pages in ROLLOUT that carry a ripples graphic: About (approach), BizCheck (panel), the hub (practice cards heading)
# and each pillar page ("How we work" heading).
RIPPLE_PAGES = ("About", "Services", "partnerships", "ai-solutions", "digital-presence", "BizCheck")


def _page(browser, site_url, stem, width=1280, height=800, theme=None, **kw):
    ctx = new_context(browser, width, height, theme=theme, **kw)
    return ctx, open_page(ctx, site_url, stem)


def _settle_all(page):
    """Bring every assemble root into view, wait until it is done, park the pointer away."""
    n = page.evaluate("document.querySelectorAll('[data-assemble]').length")
    for i in range(n):
        page.evaluate(
            "(i) => document.querySelectorAll('[data-assemble]')[i].scrollIntoView({block: 'center', behavior: 'instant'})", i)
        page.wait_for_function(
            f"document.querySelectorAll('[data-assemble]')[{i}].hasAttribute('data-assemble-done')", timeout=9000)
    page.mouse.move(2, 2)
    page.wait_for_timeout(700)


@pytest.mark.parametrize("theme", THEMES)
@pytest.mark.parametrize("stem", ROLLOUT + ("Contact",))
def test_rollout_no_horizontal_scroll_at_320_while_assembling(browser, site_url, stem, theme):
    ctx, page = _page(browser, site_url, stem, width=320, height=700, theme=theme, reduced_motion="no-preference")
    try:
        total = page.evaluate("document.documentElement.scrollHeight")
        y = 0
        while y < total:
            page.evaluate("(y) => window.scrollTo(0, y)", y)
            page.wait_for_timeout(250)
            sw, cw = page.evaluate("[document.documentElement.scrollWidth, document.documentElement.clientWidth]")
            assert sw <= cw, f"{stem} at y={y}: horizontal scroll {sw} > {cw}"
            y += 500
        page.wait_for_timeout(3600)
        sw, cw = page.evaluate("[document.documentElement.scrollWidth, document.documentElement.clientWidth]")
        assert sw <= cw
    finally:
        ctx.close()


@pytest.mark.parametrize("stem", ROLLOUT)
def test_rollout_reduced_motion_shows_final_state(browser, site_url, stem):
    ctx, page = _page(browser, site_url, stem, reduced_motion="reduce")
    try:
        page.wait_for_timeout(500)
        bad = page.evaluate(FINAL_JS, [True, "main"])
        # two pre-existing static decorations carry a fixed design opacity (the About eye ring, the CTA glow); they never animate
        bad = [b for b in bad if not (b[0] == "opacity" and b[1] in ("ring", "cta-glow"))]
        # and the outer ring of the fourth "How we work" step marker (the process band on the pillar pages), whose
        # opacity="0.5" is a fixed design attribute on a static circle: exempt only those rings, one entry each
        rings = page.evaluate(
            """() => [...document.querySelectorAll('main .step-iris')].filter(s => { const c = s.querySelectorAll('circle'); const last = c[c.length - 1];
              return last && last.getAttribute('opacity') === '.5' && getComputedStyle(last).opacity === '0.5'; }).length""")
        for _ in range(rings):
            if ["opacity", "circle", "0.5"] in bad:
                bad.remove(["opacity", "circle", "0.5"])
        assert bad == [], bad
        assert page.evaluate("document.querySelectorAll('.is-emitting, .is-tilting').length") == 0
        assert page.evaluate("document.querySelectorAll('[data-assemble=\"pre\"]').length") == 0
    finally:
        ctx.close()


@pytest.mark.parametrize("theme", THEMES)
@pytest.mark.parametrize("width", (1280, 768))
def test_rollout_alignment_at_rest(browser, site_url, width, theme):
    """Settled, pointer away: no resting transform on any card or its contents, and the number/title edges align."""
    checks = [
        ("partnerships", "article.svc-detail .deliverables li", None, None),
        ("Projects", ".project-card", ".project-index", "h3"),
        ("BizCheck", ".bc-step", ".n", ".h3"),
        # the hub's practice cards: icon and title share a left edge; the pillar pages' unlinked service cards rest flat
        ("Services", "a.svc", ".iris-ico", "h3"),
        ("partnerships", "#what .ps-list li", "h3", "p"),
        ("ai-solutions", "#what .ps-list li", "h3", "p"),
        ("digital-presence", "#what .ps-list li", "h3", "p"),
    ]
    for stem, card, a, b in checks:
        ctx, page = _page(browser, site_url, stem, width=width, theme=theme, reduced_motion="no-preference")
        try:
            _settle_all(page)
            res = page.evaluate(
                """([card, a, b]) => [...document.querySelectorAll(card)].map(c => {
                  const t = (e) => getComputedStyle(e).transform;
                  const nodes = [c, ...c.querySelectorAll('*')];
                  return {tr: nodes.map(t).filter(v => v !== 'none'), tilting: c.classList.contains('is-tilting'),
                          dl: (a && b) ? c.querySelector(a).getBoundingClientRect().left - c.querySelector(b).getBoundingClientRect().left : 0};
                })""", [card, a, b])
            assert res, stem
            for r in res:
                assert r["tr"] == [] and not r["tilting"], f"{stem}@{width}: resting transform {r['tr']}"
                assert abs(r["dl"]) <= 2, f"{stem}@{width}: number left edge vs title left edge {r['dl']}"
        finally:
            ctx.close()


@pytest.mark.parametrize("width", (1280, 768, 375))
def test_rollout_ripple_centre_and_inner_rings_are_clear_of_text(browser, site_url, width):
    seen = 0
    for stem in ROLLOUT:
        ctx, page = _page(browser, site_url, stem, width=width, height=800, reduced_motion="no-preference")
        try:
            if page.locator(".ripples").count() == 0:
                assert stem not in RIPPLE_PAGES, f"{stem} lost its ripples"
                continue
            seen += 1
            _settle_all(page)
            _centre(page, ".has-ripples")
            hit = page.evaluate(
                """() => {
                  const s = document.querySelector('.has-ripples'), svg = s.querySelector('.ripples');
                  const d = svg.querySelector('.drop').getBoundingClientRect();
                  const cx = d.left + d.width / 2, cy = d.top + d.height / 2;
                  const inner = svg.querySelectorAll('circle')[1].getBoundingClientRect().width / 2;   // centre dot plus the first two rings
                  const hits = [], w = document.createTreeWalker(s, NodeFilter.SHOW_TEXT);
                  for (let n = w.nextNode(); n; n = w.nextNode()) {
                    if (!n.textContent.trim() || n.parentElement.closest('svg')) continue;
                    const r = document.createRange(); r.selectNodeContents(n);
                    for (const b of r.getClientRects()) {
                      const nx = Math.max(b.left, Math.min(cx, b.right)), ny = Math.max(b.top, Math.min(cy, b.bottom));
                      const dist = Math.hypot(nx - cx, ny - cy);
                      if (dist < inner) hits.push([n.parentElement.tagName, n.textContent.trim().slice(0, 24), Math.round(dist)]);
                    }
                  }
                  return hits;
                }""")
            assert hit == [], f"{stem}@{width}: ripple centre/inner rings run under text {hit}"
        finally:
            ctx.close()
    assert seen == len(RIPPLE_PAGES)   # only Projects, of the pages in ROLLOUT, carries none


def test_rollout_no_long_running_animation(browser, site_url):
    """Six seconds after every assemble root and ripple host has been seen, nothing of ours still runs.

    Nothing is excluded: the old Projects status-dot pulse no longer exists."""
    for stem in ROLLOUT:
        ctx, page = _page(browser, site_url, stem, reduced_motion="no-preference")
        try:
            _settle_all(page)
            if page.locator(".has-ripples").count():
                _centre(page, ".has-ripples")
            page.wait_for_timeout(6000)
            running = page.evaluate(
                """() => document.getAnimations().filter(a => a.playState === 'running'
                  && a.effect && a.effect.target && a.effect.target.closest && a.effect.target.closest('.assemble, .has-ripples'))
                  .map(a => a.animationName || a.transitionProperty || a.constructor.name)""")
            assert running == [], f"{stem}: still running 6 s after the placements were seen: {running}"
            assert page.evaluate("document.querySelectorAll('.is-emitting').length") == 0
        finally:
            ctx.close()


@pytest.mark.parametrize("width", (1280, 768, 375))
def test_ripples_box_stays_inside_its_own_section(browser, site_url, width):
    """The SVG box must not reach into neighbouring sections (axe reads geometry, not the clip)."""
    for stem in ("About", "BizCheck", "index", "Services", "partnerships", "ai-solutions", "digital-presence"):
        ctx, page = _page(browser, site_url, stem, width=width, height=800, reduced_motion="no-preference")
        try:
            r = page.evaluate(
                """() => [...document.querySelectorAll('.has-ripples')].map(s => { const v = s.querySelector('.ripples');
                  const a = s.getBoundingClientRect(), b = v.getBoundingClientRect();
                  return {top: b.top - a.top, bottom: a.bottom - b.bottom}; })""")
            assert r and all(x["top"] >= -1 and x["bottom"] >= -1 for x in r), f"{stem}@{width}: ripples box leaves its section {r}"
        finally:
            ctx.close()


GRIDS = {
    "index": "#services a.svc",
    "Projects": ".project-card, .site-card",
    "BizCheck": ".bc-step",
    "partnerships": "article.svc-detail .deliverables li",
    "Services": "a.svc",
    "ai-solutions": "#what .ps-list li",
    "digital-presence": "#what .ps-list li",
}


@pytest.mark.parametrize("theme", THEMES)
@pytest.mark.parametrize("width", (1280, 768))
def test_grid_lines_are_continuous(browser, site_url, width, theme):
    """Every card/cell keeps its right and bottom border as a visible line (rendered pixels, motion on, settled)."""
    import io
    from PIL import Image
    for stem, sel in GRIDS.items():
        ctx, page = _page(browser, site_url, stem, width=width, height=900, theme=theme, reduced_motion="no-preference")
        try:
            _settle_all(page)
            page.evaluate("window.scrollTo(0, 0)")
            page.wait_for_timeout(300)
            info = page.evaluate(
                """(sel) => [...document.querySelectorAll(sel)].map(c => { const r = c.getBoundingClientRect(), s = getComputedStyle(c);
                  return {l: r.left, r: r.right, t: r.top + scrollY, b: r.bottom + scrollY, br: s.borderRightWidth, bb: s.borderBottomWidth}; })""", sel)
            assert info, stem
            for c in info:
                assert c["br"] == "1px" and c["bb"] == "1px", (stem, c)
            # the outer right edge is shared exactly by every card that reaches it (no card sits 1px inside)
            maxr = max(c["r"] for c in info)
            for c in info:
                assert abs(c["r"] - maxr) < 0.5 or c["r"] < maxr - 50, (stem, width, c["r"], maxr)
            full = Image.open(io.BytesIO(page.screenshot(full_page=True))).convert("RGB")
            def lum(px): return sum(px)
            missing = []
            for i, c in enumerate(info):
                xm, ym = int((c["l"] + c["r"]) / 2), int((c["t"] + c["b"]) / 2)
                inside = lum(full.getpixel((xm, ym)))
                # bottom line: some row within 2px of the bottom edge differs from the card face
                rows = [int(c["b"]) + d for d in (-3, -2, -1, 0)]
                if not any(abs(lum(full.getpixel((xm, y))) - inside) > 12 for y in rows if 0 <= y < full.height):
                    missing.append((i, "bottom"))
                cols = [int(c["r"]) + d for d in (-3, -2, -1, 0)]
                if not any(abs(lum(full.getpixel((x, ym))) - inside) > 12 for x in cols if 0 <= x < full.width):
                    missing.append((i, "right"))
            assert missing == [], f"{stem}@{width}: grid lines missing at {missing}"
        finally:
            ctx.close()


# ---------------------------------------------------------------- final wave: process markers and print

def _settle_home(page):
    for sel in ("#letters", "#services", "#process"):
        page.evaluate("(s) => document.querySelector(s).scrollIntoView({block: 'center', behavior: 'instant'})", sel)
        page.wait_for_function(f"document.querySelector('{sel}').hasAttribute('data-assemble-done')", timeout=9000)
    page.mouse.move(2, 2)
    page.wait_for_timeout(700)


def test_home_process_has_one_marker_row_on_the_line(browser, site_url):
    ctx, page = _page(browser, site_url, "index", width=1280, reduced_motion="no-preference")
    try:
        _settle_home(page)
        r = page.evaluate(
            """() => { const mid = (e, a) => { const b = e.getBoundingClientRect(); return a === 'y' ? b.top + b.height / 2 : b.left + b.width / 2; };
              const line = document.querySelector('.proc-line'), irises = [...document.querySelectorAll('.proc-step .step-iris')];
              return {dots: document.querySelectorAll('.proc-step .dot').length, n: irises.length,
                      dy: irises.map(i => mid(i, 'y') - mid(line, 'y')), dx: line.getBoundingClientRect().left - mid(irises[0], 'x')}; }""")
        assert r["dots"] == 0 and r["n"] == 4
        assert all(abs(d) <= 2 for d in r["dy"]), r      # every marker centred on the line
        assert abs(r["dx"]) <= 2, r                      # the line grows from the first marker
    finally:
        ctx.close()


def test_home_process_stacked_markers_sit_beside_their_text_at_375(browser, site_url):
    ctx, page = _page(browser, site_url, "index", width=375, reduced_motion="no-preference")
    try:
        _settle_home(page)
        r = page.evaluate(
            """() => [...document.querySelectorAll('.proc-step')].map(s => { const i = s.querySelector('.step-iris').getBoundingClientRect(), t = s.querySelector('h3').getBoundingClientRect();
              return [i.right <= t.left + 1, i.top >= s.getBoundingClientRect().top - 1]; })""")
        assert all(a and b for a, b in r), r
        assert page.evaluate("getComputedStyle(document.querySelector('.proc-line')).display") == "none"
    finally:
        ctx.close()


PILLARS = ("partnerships", "ai-solutions", "digital-presence")


@pytest.mark.parametrize("stem", PILLARS)
def test_pillar_process_has_one_marker_row_on_the_line(browser, site_url, stem):
    """The Home process markers, reused on every pillar page: one row of four, centred on the line, line grows from the first."""
    ctx, page = _page(browser, site_url, stem, width=1280, reduced_motion="no-preference")
    try:
        _settle_all(page)
        r = page.evaluate(
            """() => { const mid = (e, a) => { const b = e.getBoundingClientRect(); return a === 'y' ? b.top + b.height / 2 : b.left + b.width / 2; };
              const root = document.querySelector('#process');
              const line = root.querySelector('.proc-line'), irises = [...root.querySelectorAll('.proc-step .step-iris')];
              return {dots: root.querySelectorAll('.proc-step .dot').length, n: irises.length,
                      dy: irises.map(i => mid(i, 'y') - mid(line, 'y')), dx: line.getBoundingClientRect().left - mid(irises[0], 'x'),
                      tr: [...root.querySelectorAll('.proc-step, .proc-line .fill')].map(e => getComputedStyle(e).transform).filter(v => v !== 'none')}; }""")
        assert r["dots"] == 0 and r["n"] == 4
        assert all(abs(d) <= 2 for d in r["dy"]), r
        assert abs(r["dx"]) <= 2, r
        assert r["tr"] == [], f"resting transform on a process step: {r['tr']}"
    finally:
        ctx.close()


@pytest.mark.parametrize("stem", PILLARS)
def test_pillar_process_stacked_markers_sit_beside_their_text_at_375(browser, site_url, stem):
    ctx, page = _page(browser, site_url, stem, width=375, reduced_motion="no-preference")
    try:
        _settle_all(page)
        r = page.evaluate(
            """() => [...document.querySelectorAll('#process .proc-step')].map(s => { const i = s.querySelector('.step-iris').getBoundingClientRect(), t = s.querySelector('h3').getBoundingClientRect();
              return [i.right <= t.left + 1, i.top >= s.getBoundingClientRect().top - 1]; })""")
        assert len(r) == 4 and all(a and b for a, b in r), r
        assert page.evaluate("getComputedStyle(document.querySelector('#process .proc-line')).display") == "none"
    finally:
        ctx.close()


@pytest.mark.parametrize("theme", THEMES)
@pytest.mark.parametrize("stem", ("Services",) + PILLARS)
def test_template_pages_do_not_scroll_sideways_at_375_and_320(browser, site_url, stem, theme):
    for width in (375, 320):
        ctx, page = _page(browser, site_url, stem, width=width, height=800, theme=theme, reduced_motion="no-preference")
        try:
            _settle_all(page)
            sw, cw = page.evaluate("[document.documentElement.scrollWidth, document.documentElement.clientWidth]")
            assert sw <= cw, f"{stem}@{width} [{theme}]: {sw} > {cw}"
        finally:
            ctx.close()


def test_hub_card_lists_and_links_line_up_across_the_row_at_1280(browser, site_url):
    """Icon, title block, buyer line, service list and Explore link share their top edges across the three cards,
    however long a title runs (the AI card's title wraps to two lines)."""
    ctx, page = _page(browser, site_url, "Services", width=1280, reduced_motion="no-preference")
    try:
        _settle_all(page)
        tops = page.evaluate(
            """() => ['.iris-ico', 'h3', '.svc-buyer', '.svc-names', '.svc-arrow'].map(sel =>
              [...document.querySelectorAll('a.svc')].map(a => a.querySelector(sel).getBoundingClientRect().top))""")
        for sel, row in zip(("icon", "title", "buyer line", "list", "link"), tops):
            assert max(row) - min(row) <= 2, f"{sel} top edges differ across the cards: {row}"
        # the list items keep one pitch in every card (a short list must not stretch to fill the row)
        pitch = page.evaluate(
            """() => [...document.querySelectorAll('a.svc .svc-names')].map(ul => { const t = [...ul.children].map(li => li.getBoundingClientRect().top);
              return t.slice(1).map((v, i) => v - t[i]); }).flat()""")
        assert max(pitch) - min(pitch) <= 2, pitch
        bottoms = page.evaluate("[...document.querySelectorAll('a.svc')].map(a => a.getBoundingClientRect().bottom)")
        assert max(bottoms) - min(bottoms) <= 2, bottoms
    finally:
        ctx.close()


def test_home_pillar_cards_line_up_across_the_row_at_1280(browser, site_url):
    """Icon, title, line and Explore link share their top edges across Home's three cards, however long a title runs,
    and nothing is displaced at rest."""
    ctx, page = _page(browser, site_url, "index", width=1280, reduced_motion="no-preference")
    try:
        _settle_all(page)
        tops = page.evaluate(
            """() => ['.iris-ico', 'h3', 'p', '.svc-arrow'].map(sel =>
              [...document.querySelectorAll('#services a.svc')].map(a => a.querySelector(sel).getBoundingClientRect().top))""")
        assert len(tops[0]) == 3
        for sel, row in zip(("icon", "title", "line", "link"), tops):
            assert max(row) - min(row) <= 2, f"{sel} top edges differ across Home's cards: {row}"
        rects = page.evaluate("[...document.querySelectorAll('#services a.svc')].map(a => { const r = a.getBoundingClientRect(); return [r.top, r.bottom, r.width]; })")
        assert max(r[0] for r in rects) - min(r[0] for r in rects) <= 2 and max(r[1] for r in rects) - min(r[1] for r in rects) <= 2, rects
        assert max(r[2] for r in rects) - min(r[2] for r in rects) <= 2, rects      # three equal columns
        # the arrow is visible at rest (touch devices have no hover), and each card is one whole-card link
        assert page.evaluate("[...document.querySelectorAll('#services .svc-arrow')].every(e => getComputedStyle(e).opacity === '1')")
        assert page.evaluate("document.querySelectorAll('#services a.svc a').length") == 0
    finally:
        ctx.close()


@pytest.mark.parametrize("width", (768, 375))
def test_home_pillar_cards_stack_without_sideways_scroll(browser, site_url, width):
    ctx, page = _page(browser, site_url, "index", width=width, reduced_motion="no-preference")
    try:
        _settle_all(page)
        r = page.evaluate("[...document.querySelectorAll('#services a.svc')].map(a => { const b = a.getBoundingClientRect(); return [b.left, b.width]; })")
        assert len(r) == 3 and len({round(x[0]) for x in r}) == 1 and len({round(x[1]) for x in r}) == 1, r
        sw, cw = page.evaluate("[document.documentElement.scrollWidth, document.documentElement.clientWidth]")
        assert sw <= cw
    finally:
        ctx.close()


def test_hub_cards_are_whole_card_links_and_pillar_cards_are_not(browser, site_url):
    ctx, page = _page(browser, site_url, "Services", reduced_motion="no-preference")
    try:
        _settle_all(page)
        cards = page.evaluate("[...document.querySelectorAll('a.svc')].map(a => [a.getAttribute('href'), a.getBoundingClientRect().height > 200])")
        assert [c[0] for c in cards] == ["partnerships.html", "ai-solutions.html", "digital-presence.html"] and all(c[1] for c in cards)
        # the three cards of one row have the same height and top edge
        tops = page.evaluate("[...document.querySelectorAll('a.svc')].map(a => [Math.round(a.getBoundingClientRect().top), Math.round(a.getBoundingClientRect().height)])")
        assert len({t for t, _ in tops}) == 1 and len({h for _, h in tops}) == 1, tops
    finally:
        ctx.close()
    ctx, page = _page(browser, site_url, "ai-solutions", reduced_motion="no-preference")
    try:
        assert page.evaluate("document.querySelectorAll('#what a, #what button').length") == 0
        assert page.evaluate("getComputedStyle(document.querySelector('#what .ps-list li')).cursor") != "pointer"
    finally:
        ctx.close()


def test_print_shows_everything_settled(browser, site_url):
    """Content still in its hidden 'pre' state prints visible; rings do nothing in print."""
    for stem in ("index", "Services", "partnerships", "ai-solutions", "digital-presence", "Projects", "BizCheck"):
        ctx, page = _page(browser, site_url, stem, width=1280, reduced_motion="no-preference")
        try:
            page.wait_for_timeout(600)       # below-the-fold sections are still in the hidden state here
            if stem == "index":
                assert page.evaluate("document.querySelectorAll('[data-assemble=\"pre\"]').length") >= 1
            page.emulate_media(media="print")
            bad = page.evaluate(
                """() => [...document.querySelectorAll('.asm-scatter, .asm-card, .asm-fade, .asm-rise, .asm-grow, .iris-ico, .step-iris')]
                  .map(e => { const c = getComputedStyle(e); return [String(e.className.baseVal ?? e.className), c.opacity, c.transform]; })
                  .filter(([n, o, t]) => parseFloat(o) < 1 || (t !== 'none' && t !== 'matrix(1, 0, 0, 1, 0, 0)'))""")
            assert bad == [], f"{stem}: not settled in print {bad[:3]}"
            circles = page.evaluate(
                """() => [...document.querySelectorAll('.step-iris circle, .iris-ico .fillgold')].filter(e => getComputedStyle(e).transform !== 'none').length""")
            assert circles == 0, stem
            rings = page.evaluate("[...document.querySelectorAll('.ripples')].map(e => getComputedStyle(e).display)")
            assert all(d == "none" for d in rings), (stem, rings)
        finally:
            ctx.close()
