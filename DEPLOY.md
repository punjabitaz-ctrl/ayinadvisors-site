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
to `/BizCheck`. Keep the `.html` files named as they are - the redirect is
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

`BizCheck.html` posts to `/api/bizcheck` - a Pages Function that verifies the
Turnstile token server-side before relaying to Formspree. The Formspree URL is
never in the page; it lives in the `FORMSPREE_ENDPOINT` variable.

Required Pages environment variables (Settings → Environment variables →
**Production**, then redeploy - Pages binds them at build time):

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

If the endpoint is ever committed to this public repo, rotate it - history
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

Note: the site must be served over HTTP, not opened as `file://` - relative
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
- **Adding a service page** (a sub-page in a folder, e.g. `partnerships/channel-strategy.html`): in
  `content/services.json` give the service `"status": "live"`, an `"href"` (`<pillar>/<slug>.html`) and a
  `"detail"` (`tag`, `text`, `deliverables`); in `content/site.json` add a page keyed by its stem
  (`"partnerships/<slug>"`) with `"template": "service"`, `"pillar"`, `"service"`, canonical, title
  `"<Name> - AYiN Advisors"`, a 120-160 character description and sitemap priority `0.7`. Rebuild; the build
  creates the folder. Pages in a folder get a `root` prefix (`""` at the root, `"../"` one level down) that the
  shared templates apply to every site-relative link and asset through the `|ru(root)` filter (use it on any new
  href in a template). Baseline snapshots of folder pages are stored with `/` replaced by `__`.
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

## 3D hero, smooth scroll and depth (Phase 2d)

Three pieces, all self-hosted (no CDN; the CSP is unchanged because `script-src 'self'` already covers them):

- **Smooth scroll and depth parallax, every page.** `assets/vendor/lenis.min.js`, `gsap.min.js`, `ScrollTrigger.min.js`
  and `assets/motion.js`, loaded with `defer` from `<head>` (`templates/base.j2`). Versions and hashes are pinned in
  `assets/vendor/MANIFEST.json`; licences (Lenis MIT, GSAP standard "no charge" licence, three.js MIT) are in
  `assets/vendor/LICENSES.md`. Reduced motion: none of it runs. Touch scrolling is native.
- **WebGL hero iris, Home only.** `assets/hero3d.js` is built from `tools/hero3d/src/main.js` with esbuild (three.js,
  tree-shaken) and **committed**, because Cloudflare serves the repo root with no build command. It starts only on
  screens at least 720px wide with a hover-capable or fine pointer, no reduced motion and no data-saver; if WebGL is
  missing, the context is lost or anything throws, it removes its canvas and the original 2D hero canvas (`#iris`,
  `assets/site.js`) carries on. It renders on demand (no idle loop) and reads its colours from the page's CSS roles.
- **Rebuilding** (only needed after editing `tools/hero3d/src/main.js` or changing a pin in `tools/hero3d/package.json`):

  ```
  cd tools/hero3d
  npm ci
  npm run build     # writes assets/hero3d.js and assets/hero3d.build.json
  npm run vendor    # only after changing the lenis/gsap pins: refreshes assets/vendor/*.min.js and MANIFEST.json
  ```

  Commit the regenerated files. `node_modules/` is git-ignored and `/tools/` is disallowed in `robots.txt`.
  `tests/test_hero3d_static.py` fails if the committed bundle no longer matches the source and lockfile hashes
  (it compares recorded hashes, so it needs neither node nor esbuild).
- **Budgets** (enforced by the same test): `hero3d.js` at most 200 KB gzipped, the three vendor files together at most
  120 KB gzipped. Hero text never waits for the bundle (all scripts are deferred; the 2D canvas paints first and the
  3D canvas fades in over it with no layout shift).
- **ScrollTrigger housekeeping.** Two built-in ScrollTrigger timers would keep the page awake while idle (a per-frame
  `_rafBugFix` loop and a 250 ms poll). `assets/motion.js` drops the first and replaces the second; the browser test
  `test_render_loop_stops_when_input_stops` fails if an upgrade brings either back, so re-run it after bumping GSAP.
- **Fallbacks, in order:** reduced motion, narrow screen, touch-only, data-saver, no WebGL, an exception, a lost
  context, a missing script (a blocked CDN-free file): each leaves the 2D hero and the normal browser scrolling.
