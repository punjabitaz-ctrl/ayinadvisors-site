"""In-memory page used by the motion tests.

The real pages do not carry the T1 components yet, so the tests serve this
document from a Playwright route (never written to disk); CSS and JS are the
real site assets.
"""
FIXTURE_PATH = "/__motion_fixture.html"

_IRIS = (
    '<svg class="iris-ico" viewBox="0 0 54 54" fill="none" stroke="currentColor" stroke-width="1.3" aria-hidden="true">'
    '<circle cx="27" cy="27" r="22"/><circle cx="27" cy="27" r="12"/><circle class="fillgold" cx="27" cy="27" r="3.6" stroke="none"/>'
    '<path d="M27 2v8M27 44v8" stroke-linecap="round"/></svg>'
)


def _ripples(side):
    return (
        f'<svg class="ripples {side}" viewBox="0 0 400 400" aria-hidden="true" data-drift="0.12">'
        + "".join(f'<circle cx="200" cy="200" r="{r}"/>' for r in (40, 78, 118, 158, 198, 239))
        + '<circle class="drop" cx="200" cy="200" r="3.5"/></svg>'
    )


def _card(n):
    return (
        f'<a class="svc asm-card" href="#c{n}" style="display:block;padding:24px;border:1px solid currentColor">'
        f'{_IRIS}<h3>Card {n}</h3><p>Body text for card {n}.</p></a>'
    )


def _step(n):
    return (
        '<div class="proc-step asm-rise"><svg class="step-iris" viewBox="0 0 34 34" fill="none" stroke="currentColor" aria-hidden="true">'
        f'<circle cx="17" cy="17" r="3" fill="currentColor" stroke="none"/></svg><h3>Step {n}</h3></div>'
    )


FIXTURE_HTML = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>motion fixture</title>
<script>document.documentElement.classList.add('js');</script>
<link rel="stylesheet" href="assets/theme.css"><link rel="stylesheet" href="assets/styles.css">
</head><body>
<div style="height:900px">top spacer</div>
<div class="letters surface-alt assemble" id="letters" data-assemble>
  <div class="wrap">
    <div class="letters-row asm-stage" role="img" aria-label="The letter ayin: the eye.">
      <div class="lt asm-scatter"><span class="glyph ar" aria-hidden="true">ع</span><span class="cap">Arabic</span></div>
      <span class="lt-sep asm-fade" aria-hidden="true">+</span>
      <div class="lt asm-scatter"><span class="glyph he" aria-hidden="true">ע</span><span class="cap">Hebrew</span></div>
      <span class="lt-sep asm-fade" aria-hidden="true">+</span>
      <div class="lt asm-scatter"><span class="glyph la" aria-hidden="true">O</span><span class="cap">Latin</span></div>
    </div>
    <p class="letters-line asm-fade">One letter, to see.</p>
  </div>
</div>
<div style="height:1000px">spacer</div>
<section class="section surface-page has-ripples assemble" id="services" data-assemble>
  {_ripples("ripples-r")}
  <div class="wrap"><div class="svc-grid asm-stage" style="display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:16px">
    {_card(1)}{_card(2)}{_card(3)}{_card(4)}
  </div></div>
</section>
<div style="height:1000px">spacer</div>
<section class="section surface-alt has-ripples assemble" id="process" data-assemble>
  {_ripples("ripples-l")}
  <div class="wrap"><div class="proc-wrap asm-stage">
    <div class="proc-line" style="height:2px"><div class="fill asm-grow" style="height:2px;background:currentColor"></div></div>
    <div class="proc-grid" style="display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr))">{_step(1)}{_step(2)}{_step(3)}{_step(4)}</div>
  </div></div>
</section>
<div style="height:1400px">end spacer</div>
<script src="assets/site.js"></script>
</body></html>
"""

# Same page on a long document: services (and its ripple) sit about 4000px down.
FIXTURE_LONG_PATH = "/__motion_fixture_long.html"
FIXTURE_LONG_HTML = FIXTURE_HTML.replace("height:900px", "height:4000px").replace("height:1400px", "height:3000px")
