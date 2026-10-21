# Deploying

Static files, no build step. Hosted on **Cloudflare Pages** (project
`ayin-advisors`), which deploys automatically from this repo on every push to
`master`.

- Live: https://ayinadvisors.com
- Pages origin: https://ayin-advisors.pages.dev

## Cloudflare Pages settings

| Setting          | Value  |
|------------------|--------|
| Build command    | *(none)* |
| Output directory | `/`    |
| Branch           | `master` |

Cloudflare Pages serves clean URLs automatically: `/BizCheck.html` 308-redirects
to `/BizCheck`. Keep the `.html` files named as they are — the redirect is
handled at the edge, and inbound links to either form work.

## DNS

Managed in Cloudflare. Both records are proxied (orange cloud):

| Type  | Name | Content                  |
|-------|------|--------------------------|
| CNAME | `@`  | `ayin-advisors.pages.dev` |
| CNAME | `www`| `ayinadvisors.com`        |

`www` must also be added as a **custom domain on the Pages project**
(Workers & Pages → ayin-advisors → Custom domains), otherwise Cloudflare
proxies the hostname but no origin is bound to it and it returns a 522.

## BizCheck form

`BizCheck.html` posts to `/api/bizcheck` — a Pages Function that verifies the
Turnstile token server-side before relaying to Formspree. The Formspree URL is
never in the page; it lives in the `FORMSPREE_ENDPOINT` variable.

Required Pages environment variables (Settings → Environment variables →
**Production**, then redeploy — Pages binds them at build time):

| Variable | Value | Type |
|---|---|---|
| `TURNSTILE_SECRET` | Turnstile widget secret | Encrypt |
| `TURNSTILE_HOSTNAMES` | `ayinadvisors.com` | Plaintext |
| `FORMSPREE_ENDPOINT` | the Formspree form URL | Encrypt |

`TURNSTILE_HOSTNAMES` must not include `localhost` in production, or a token
minted locally would be accepted.

Do not enable Formspree's own reCAPTCHA on this form. It only works when a
browser posts directly to Formspree; the Function posts server-to-server, so
Formspree rejects with *"In order to submit via AJAX, you need to set a custom
key or reCAPTCHA must be disabled"*. Turnstile already covers it, and runs
before Formspree is contacted at all.

If the endpoint is ever committed to this public repo, rotate it — history
outlives the file.

## Contact form

`Contact.html` posts to `/api/contact`, hardened identically to BizCheck. It
reuses the same Turnstile widget and the same `TURNSTILE_SECRET` /
`TURNSTILE_HOSTNAMES`, with its own action (`contact`) so the two surfaces stay
distinguishable at siteverify, and its own form:

| Variable | Value | Type |
|---|---|---|
| `CONTACT_FORMSPREE_ENDPOINT` | the contact form's Formspree URL | Encrypt |

Its previous endpoint was public in page source and in this repo's history, so
rotate it rather than reusing it.

## Local preview

```bash
python -m http.server 4173
```

Note: the site must be served over HTTP, not opened as `file://` — relative
asset paths won't resolve otherwise.

## Building

The site is generated: run `python build.py` to render the seven root pages
from `content/site.json`, `templates/` and `templates/pages/`.

- **Never edit a root `.html` file.** Edit `content/site.json`, `templates/` or
  `templates/pages/`, then rebuild and commit the regenerated output.
- `python build.py --check` reports any page that has drifted from its
  templates (`stale: none` and exit 0 when clean, otherwise lists names, exit 1).
- Install tooling with `pip install -r dev-requirements.txt`; run tests with
  `PYTHONUTF8=1 python -m pytest`.
- Templates are named `.j2` and page body fragments `.frag` because Cloudflare
  Pages serves the whole repo root: no `.html` other than the seven real pages
  may be committed (`tests/test_no_stray_html.py` enforces this).
- The dev dependency file is deliberately **not** named `requirements.txt`:
  Cloudflare Pages may auto-run `pip install -r requirements.txt`, and a failure
  there would break the production deploy for a build the deploy does not use.
  The generated `.html` is committed; Cloudflare runs no build.

## Testing

`tests/baseline/*.snap` are frozen snapshots taken before the build system
existed. They are a one-time proof that the generated pages match the pre-build
site, not a permanent contract. After Sprint 1 merges, a sprint that
intentionally changes visible output states an explicit, pinned delta in its own
test (as Sprint 1 did for the footer). Durable protection comes from
baseline-independent invariants: chrome identical across pages, links resolve,
forms/ids/scripts present, accessibility and contrast gates. Baselines are
re-snapshotted from merged output at the start of the next sprint, never edited
to turn a red test green.

## Theme (generated)

Every colour on the site comes from `content/theme.json` (palette, per-surface
roles, derived text tones, required contrast pairings). `python build.py` turns
it into `assets/theme.css`, so **`assets/theme.css` is generated: never edit it
by hand**. The build refuses to write the file if any declared pairing (normal
text 4.5:1, large text and UI 3:1, including hover and placeholder states, in
every surface context and both themes) fails, and the tests re-check the same
pairings. Colour literals are not allowed anywhere else (`tests/test_no_color_literals.py`).
To change a colour, edit `content/theme.json`, run `python build.py` and commit
the regenerated `assets/theme.css` with the pages.

### Light/dark switch

Dark is a second token set in `content/theme.json`; `assets/theme.css` carries
both (generated, never edited by hand). There is nothing to configure at deploy.

- `html[data-theme="light"|"dark"]` is set by a small inline script in `<head>`,
  before the stylesheet link, so the first paint is already in the right theme.
  It reads `localStorage['ayin-theme']` (always in try/catch) and otherwise the
  system preference. `assets/site.js` handles the toggle button, persistence,
  `meta theme-color` and a `themechange` event.
- Without JavaScript the page follows the system theme through a CSS media rule
  scoped to `:root:not([data-theme])`, and the toggle is hidden.
- `@media print` re-declares the light roles, so print is always the light look.
- The gate runs both themes: browser tests are parametrised over light and dark
  (system scheme emulated plus the stored choice), so a full
  `PYTHONUTF8=1 python -m pytest tests` takes about 12 minutes.
- Review notes and the manual checks: `docs/accessibility/2026-10-2c-review.md`.

## Images (pipeline)

Photography is registered in `content/images.json` (slug, source file name,
alt text or `decorative: true`, focal point, crop). Pages place a photo with an
`<image-slot slug="...">` element; `build.py` expands it to a `<picture>` with
480, 960 and 1600px WebP sources. Originals are never committed. To (re)generate
the files, pass the folder that holds the originals on the command line:

```bash
python tools/optimize_images.py <folder-with-originals>
```

Output goes to `assets/img/<slug>-{480,960,1600}.webp` (EXIF stripped, never
upscaled, each 1600px file within 160 KB); commit the results, then run
`python build.py`. Changing only alt text needs no optimiser run.

## Accessibility gate (development only)

The gate is part of the normal test run; it does not affect the deploy path.

```
pip install -r dev-requirements.txt
python -m playwright install chromium     # browser tests need Chromium
PYTHONUTF8=1 python -m pytest tests                    # includes the gate, both themes (about 12 minutes)
PYTHONUTF8=1 python -m pytest tests -m "not browser"   # static checks only, no Chromium
```

- Tests marked `browser` drive headless Chromium against the repo root served
  on a local port; if Chromium is not installed they skip with the install
  command in the reason.
- The standard is zero: axe-core reports no violations on any page at 320, 768
  and 1280px, and the static lint reports nothing. There is no tolerance file.
- axe "needs review" results (text over gradients, translucent headers,
  decorative layers) each need an entry in `tests/a11y_review.json` with
  `status: "justified"` and a specific reason, and
  `tests/a11y_browser/test_review_contrast.py` backs every such entry by
  measuring real glyph-on-background contrast from rendered pixels. Stale
  entries and `unreviewed` entries fail the suite.
- Behaviour checks (keyboard order, focus visibility, sticky-header focus
  clearance, mobile menu, 320px reflow, reduced motion) live in
  `tests/a11y_browser/test_behaviour.py`.
- Manual checks that automation cannot do are listed in
  `docs/accessibility/checklist.md`; the dated results are in `docs/accessibility/`.

## Motion notes

The accents (letters band, ripples, iris markers, assembling and tilting cards)
are plain CSS and `assets/site.js`; there is nothing to configure or deploy
separately.

- Content is never hidden by CSS alone. The hidden starting state is applied
  only by `site.js`, so a page whose script is blocked or fails shows everything.
- With the visitor's reduced-motion preference on, every element is in its
  final state: no assemble, no tilt, no parallax drift, no ripple emission.
- Nothing animates on its own for more than 5 seconds after entering view
  (ripples emit once, then rest). These loops predate the accents and are
  tracked for Phase 3, which must give them a pause control: the hero canvases
  (Home, BizCheck, Contact), the Home hero scroll hint, the Home "Why" globe
  pulse, the Services and Projects header motif rotation, the About eye scan
  line and the Projects "In Testing" status-dot pulse.
- Home loads one extra Google Fonts stylesheet, limited with `text=` to the four
  letter glyphs. The existing CSP already allows it; if the font fails, the
  band's text label still carries the meaning.
- Details and what has not been checked by a person are in
  `docs/accessibility/2026-10-2b-review.md`.
