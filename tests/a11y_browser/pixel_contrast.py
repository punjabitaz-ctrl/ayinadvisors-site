"""Measure real text contrast from rendered pixels, for nodes axe cannot resolve.

axe-core reports "needs review" for text over gradients, images, pseudo-element
fills and similar. For those nodes this module renders the page twice (normal,
and with every glyph made transparent) and compares the two screenshots inside
the element's text boxes: the pixels that change are the glyphs, the pixels
underneath are the background. The worst glyph/background pair is the measured
contrast. Fixed header elements are swept over the whole scroll range because
what sits under a translucent header changes as the page scrolls.
"""
import io

from PIL import Image

HIDE_TEXT_CSS = (
    "*,*::before,*::after{color:transparent!important;-webkit-text-fill-color:transparent!important;"
    "text-shadow:none!important;text-decoration-color:transparent!important;caret-color:transparent!important}"
    "::placeholder{color:transparent!important;-webkit-text-fill-color:transparent!important}"
)
SCROLL_STEP = 350
MIN_VISIBLE_DIFF = 12  # below this the text is indistinguishable from its background

INFO_JS = r"""(sel) => {
  const el = document.querySelector(sel);
  if (!el) return null;
  // Text colour as drawn: computed colour plus the product of alpha and ancestor opacities.
  const paint = (node, pseudo) => {
    const m = getComputedStyle(node, pseudo).color.match(/[\d.]+/g).map(Number);
    let a = m.length > 3 ? m[3] : 1;
    for (let p = node; p; p = p.parentElement) a *= parseFloat(getComputedStyle(p).opacity);
    return [m[0], m[1], m[2], a];
  };
  const rects = [];
  const w = document.createTreeWalker(el, NodeFilter.SHOW_TEXT);
  let n, hasText = false;
  while ((n = w.nextNode())) {
    if (!n.nodeValue.trim()) continue;
    hasText = true;
    const r = document.createRange(); r.selectNodeContents(n);
    const col = paint(n.parentElement, null);
    for (const c of r.getClientRects()) if (c.width > 0 && c.height > 0) rects.push([c.left, c.top, c.right, c.bottom, ...col]);
  }
  if (!rects.length && /^(INPUT|TEXTAREA|SELECT)$/.test(el.tagName)) {
    const c = el.getBoundingClientRect();
    if (c.width > 0) { rects.push([c.left, c.top, c.right, c.bottom, ...paint(el, '::placeholder')]); hasText = true; }
  }
  const cs = getComputedStyle(el);
  let fixed = false;
  for (let p = el; p && p !== document.documentElement; p = p.parentElement) {
    if (getComputedStyle(p).position === 'fixed') { fixed = true; break; }
  }
  return {rects, hasText, fixed, size: parseFloat(cs.fontSize), weight: parseInt(cs.fontWeight, 10) || 400,
          scrollY: window.scrollY};
}"""


def _lin(c: int) -> float:
    c /= 255
    return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4


def _lum(p) -> float:
    return 0.2126 * _lin(p[0]) + 0.7152 * _lin(p[1]) + 0.0722 * _lin(p[2])


def ratio(a, b) -> float:
    la, lb = _lum(a), _lum(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def required_ratio(size_px: float, weight: int) -> float:
    return 3.0 if size_px >= 24 or (size_px >= 18.66 and weight >= 700) else 4.5


def _image(png: bytes) -> Image.Image:
    return Image.open(io.BytesIO(png)).convert("RGB")


def worst_ratio(shown: Image.Image, hidden: Image.Image, rects, dx=0, dy=0):
    """Minimum glyph/background contrast inside `rects` (page or viewport px, offset by dx/dy).

    Returns None when nothing is visible at all (no pixel differs).
    """
    glyphs = []  # (diff, glyph colour as drawn, background pixel)
    for l, t, r, b, cr, cg, cb, ca in rects:
        box = (max(0, int(l + dx)), max(0, int(t + dy)), min(shown.width, int(r + dx) + 1), min(shown.height, int(b + dy) + 1))
        if box[2] <= box[0] or box[3] <= box[1]:
            continue
        s, h = list(shown.crop(box).get_flattened_data()), list(hidden.crop(box).get_flattened_data())
        for sp, hp in zip(s, h):
            d = max(abs(sp[0] - hp[0]), abs(sp[1] - hp[1]), abs(sp[2] - hp[2]))
            if d:
                # Sub-pixel (LCD) anti-aliasing fringes the glyph edges, so the glyph colour is
                # rebuilt from the computed colour over the pixel's own background, not read from the fringe.
                fg = tuple(round(ca * c + (1 - ca) * h) for c, h in zip((cr, cg, cb), hp))
                glyphs.append((d, fg, hp))
    if not glyphs:
        return None
    top = max(g[0] for g in glyphs)
    if top < MIN_VISIBLE_DIFF:
        return 1.0
    core = [g for g in glyphs if g[0] >= 0.6 * top]
    return min(ratio(sp, hp) for _, sp, hp in core)


SETTLE_JS = "new Promise(r => requestAnimationFrame(() => requestAnimationFrame(() => setTimeout(r, 60))))"


def _shot(page, **kw) -> Image.Image:
    page.evaluate(SETTLE_JS)
    return _image(page.screenshot(**kw))


def measure(page, selectors):
    """{selector: {'ratio': float|None, 'required': float, 'note': str}} for the page as loaded.

    The page must already be at its final width with reveal content forced visible.
    """
    out = {}
    page.evaluate("window.scrollTo(0, 0)")
    infos = {s: page.evaluate(INFO_JS, s) for s in selectors}
    flow = [s for s, i in infos.items() if i and not i["fixed"]]
    fixed = [s for s, i in infos.items() if i and i["fixed"]]

    if flow:
        navhide = page.add_style_tag(content=".nav{visibility:hidden!important}")
        page.evaluate("window.scrollTo(0, 0)")
        shown = _shot(page, full_page=True)
        h = page.add_style_tag(content=HIDE_TEXT_CSS)
        hidden = _shot(page, full_page=True)
        page.evaluate("(el) => el.remove()", h)
        page.evaluate("(el) => el.remove()", navhide)
        for s in flow:
            i = infos[s]
            out[s] = {"ratio": worst_ratio(shown, hidden, i["rects"]) if i["rects"] else None,
                      "required": required_ratio(i["size"], i["weight"]), "note": "flow", "hasText": i["hasText"]}

    if fixed:
        vh = page.evaluate("window.innerHeight")
        total = page.evaluate("document.documentElement.scrollHeight")
        ys = list(range(0, max(0, total - vh) + 1, SCROLL_STEP)) + [max(0, total - vh)]
        worst: dict[str, float | None] = {s: None for s in fixed}
        for y in dict.fromkeys(ys):
            page.evaluate("(y) => window.scrollTo(0, y)", y)
            page.evaluate("Promise.all(document.getAnimations().map(a => a.finished.catch(() => 0)))")
            page.wait_for_timeout(80)
            cur = {s: page.evaluate(INFO_JS, s) for s in fixed}
            shown = _shot(page)
            h = page.add_style_tag(content=HIDE_TEXT_CSS)
            hidden = _shot(page)
            page.evaluate("(el) => el.remove()", h)
            for s in fixed:
                if not cur[s]["rects"]:
                    continue
                r = worst_ratio(shown, hidden, cur[s]["rects"])
                if r is not None and (worst[s] is None or r < worst[s]):
                    worst[s] = r
        for s in fixed:
            i = infos[s]
            out[s] = {"ratio": worst[s], "required": required_ratio(i["size"], i["weight"]), "note": "fixed, swept over scroll",
                      "hasText": i["hasText"]}
        page.evaluate("window.scrollTo(0, 0)")
    for s, i in infos.items():
        if i is None:
            out[s] = {"ratio": None, "required": 4.5, "note": "selector not found", "hasText": True}
    return out
