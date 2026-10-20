# Visual refresh and accessibility — design

Date: 2026-10-20
Branch: `phase-2a-theme` (off `master` after Sprint 1)
Status: awaiting review
Covers: Phase 2a in full; Phase 2b, 2c and Phase 3 in outline.

## Purpose

Soften the site's dark look with white, beige/gold and almond, bring in photography, and make
accessibility a property of the design system rather than a repair job afterwards. Target is
**WCAG 2.2 level AA**.

## Decisions already made

| Decision | Choice |
|---|---|
| Page rhythm | **Light-led.** Navy only in the hero and the footer. Almond, cream and white carry the page. The closing call-to-action band is a gold fill. |
| Palette | Existing navy and cream, plus white, beige and almond. Gold stays the brand accent. |
| Accessibility enforcement | **Full gate**: contrast-checked tokens, a static HTML lint, axe-core in real Chromium, and a per-sprint manual checklist. |
| Order of work | Theme tokens (2a) before the Phase 1 content sprints 2 to 6, so the fourteen new pages are built once in the new look. |
| Site tagline | "AYiN Advisors - Business Solutions for a Digital World". Applied with the Sprint 2 homepage rewrite, not now. |
| Pricing | Appears nowhere on the site. |

Not yet decided: whether 2b and 2c also run before the Phase 1 content sprints. That is a separate
call once 2a has landed.

## What the audit found

An axe-core 4.10.2 run over the seven generated pages, with the WCAG 2.0 to 2.2 AA tags and axe's
best-practice rules, found only these problems. Alt text, form labels, link names, language, ARIA
validity and bypass blocks all pass.

| Rule | Where |
|---|---|
| `color-contrast` (serious) | Every page except 404: 3 to 14 elements each |
| `heading-order` | Every page except 404 |
| `region` | Content outside landmarks, every page |
| `landmark-one-main` | About has no `<main>` |

The contrast failures have five root causes:

1. `--gold-deep` `#a8854a` on the paper surface `#f7f3ea`: 3.09:1, on small eyebrow labels.
2. The footer's bottom-bar text `#72787e` on navy `#061325`: 4.17:1, on **every** page.
3. Projects: slate `#5d6c7b` on navy 3.45:1, `#747b82` on `#08182c` 4.16:1, gold-deep on `#232b33` 4.17:1.
4. Decorative ghost numerals (`#efe9da` on cream, 1.09 to 1.13:1) on Projects and BizCheck. These are
   decoration and should be marked as such, not recoloured.
5. Projects: `#f9f5ed` on `#faf7f0`, 1.01:1, on two small elements. Unexplained: either near-invisible
   text or axe misreading a gradient. Must be investigated before 2a changes that page.

Axe also reports about 20 contrast items per page as "needs review" (text over the canvas and
gradients). Automation cannot resolve those; they need a human sign-off recorded in an allowlist.

### What automation cannot see

Still owed, and covered by the manual checklist and the browser behaviour tests rather than axe:
keyboard order, visible focus, focus hidden behind the sticky nav (WCAG 2.4.11), reduced motion,
a pause control for auto-moving content (2.2.2), target size of 24px (2.5.8), reflow at 320px,
200% zoom, text spacing, a screen-reader pass, and Turnstile accessibility.

## Why the palette needs a new text token

Contrast measured for the palette you described (AA needs 4.5:1 for normal text, 3:1 for large):

| Text colour | on white | on cream | on almond `#efdecd` | on beige `#e8dcc8` |
|---|---|---|---|---|
| Brand gold `#c6a15c` | 2.43 | 2.27 | **1.85** | **1.79** |
| Existing `--gold-deep` | 3.43 | 3.21 | **2.61** | **2.53** |
| Existing slate `#5d6c7b` | 5.39 | 5.04 | **4.11** | **3.98** |
| Navy `#061325` | 18.6 | 17.4 | 14.2 | 13.8 |

Consequences:

- Gold is safe as a **fill**, a border, or large display type. As small text on a light surface it fails.
- A dedicated text-safe gold ("gold-ink") is needed: about `#8c7241` on white, `#866d3e` on cream,
  `#766037` on almond. The generator solves for the minimum darkening that clears 4.5:1 rather than
  hand-picking.
- Introducing almond and beige breaks the existing muted-text slate, so a darker muted ink is needed.
- White text on a gold fill is 2.43:1. The BizCheck nav pill must use navy text (7.67:1).

## Phase 2a design

### Token architecture

`content/theme.json` is the single source of colour truth. It holds:

1. **Raw palette**: named swatches (navy, cream, almond, beige, white, gold, and so on).
2. **Semantic roles** mapped per theme:
   - surfaces: `surface-page`, `surface-alt`, `surface-card`, `surface-inverse`
   - text: `ink`, `ink-muted`, `ink-inverse`, `ink-inverse-muted`
   - accent: `accent-fill`, `on-accent`, `accent-ink` (text on light), `accent-ink-inverse` (text on navy)
   - `line`, `focus-ring`
3. **Declared pairings**: every foreground/background combination the design uses, each with its
   required ratio (4.5 normal text, 3.0 large text and UI components).

`build.py` generates `assets/theme.css` from it (committed output, like the pages; `--check` covers
it). Both a `light` set and a `dark` set are defined from day one, even though only the light-led set
ships in 2a. Phase 2c then becomes a token swap and a toggle rather than a rewrite.

Components may reference only semantic roles, never raw swatches or colour literals. A lint test
fails on any hex, `rgb()`, `hsl()` or named colour in `assets/*.css`, templates, page fragments or
inline styles, outside the theme definition and a short allowlist that carries a reason per entry
(for example the logo SVG, and the canvas colours in `site.js`, which become token-driven in 2c).

### Page rhythm (option C, light-led)

- Hero: navy with the iris canvas, as today.
- Content bands: `surface-page` (cream or white) and `surface-alt` (almond), alternating.
- Cards: `surface-card` (white).
- Closing call-to-action band: gold fill with navy text.
- Footer: navy.

Existing `.navy` and `.paper` section classes map onto the new surfaces. Every section currently
navy that is not the hero or footer becomes light. This changes class attributes in the page
fragments, so per the baseline policy it is pinned as an explicit, declared class-mapping delta in
its own test, not a silent edit.

### Photography

Thirteen Unsplash JPEGs (31.5 MB, 3000 to 7000px). The licence permits commercial use without
attribution. Originals are never committed.

- `tools/optimize_images.py <source-dir>` reads `content/images.json` (slug, source file, alt text or
  a decorative flag, focal point, pillar, crop) and writes `assets/img/<slug>-{480,960,1600}.webp`
  (no upscaling, EXIF stripped). Budget: at most 160 KB per 1600px file.
- A template macro renders `<picture>`/`<img>` with `srcset`, `sizes`, explicit `width`/`height`
  (no layout shift), `decoding="async"` and `loading="lazy"` except above the fold. The build fails
  if a slug is missing from the registry.
- Alt text is mandatory: an image has non-empty `alt` or `decorative: true` in the registry, or the
  static lint fails.
- Text never sits directly on a photograph, except under a hero scrim whose contrast is recorded in
  the manual-review allowlist.
- Placement in 2a, on existing pages only (the pillar pages get their sets in Phase 1 Sprint 2):

  | Page | Photo |
  |---|---|
  | Home, "why the US market" band | US at night (dark photo shown in a light band as a framed card) |
  | About | Daylit skyscrapers |
  | Contact | Globe |
  | BizCheck | Lightbulb on the peach gradient |
  | Projects | None |

- Held back for later: the conference room (legible slide text and identifiable people) and the
  social-media-logos shot (third-party trademarks). Both suit the Digital Presence pillar if wanted.

### Accessibility floor inside 2a

The minimum needed for the gates to go green, all of which touch shared chrome or tokens:

- the five contrast root causes fixed through tokens (root cause 4 by marking the numerals decorative);
- a skip link as the first focusable element, and one `<main id="main">` per page;
- heading order corrected on every page;
- a two-tone focus ring token with at least 3:1 against both adjacent colours, plus
  `scroll-padding-top` equal to the sticky nav height so focus is never hidden behind it;
- `prefers-reduced-motion` honoured by the iris canvas, reveal transitions, magnetic buttons and the
  marquee;
- minimum interactive target size of 24px.

Deferred to Phase 3: a visible pause control for auto-moving content, the public accessibility
statement, the screen-reader pass, and a full cognitive and plain-language review.

### The accessibility gate

Four layers, cheapest first. All run from `python -m pytest`; the browser layer is marked so a quick
run can skip it.

1. **Token contrast** (`tests/test_theme_contrast.py`): every declared pairing in every theme must meet
   its required ratio, with alpha-composited colours resolved against their surface.
2. **Static lint** (`tests/test_a11y_static.py`, no browser): exactly one `<main>` and one `<h1>` per
   page; heading levels never skip; `html[lang]`; image alt policy against the registry; every form
   control labelled; unique ids; links and buttons have accessible names; no `aria-hidden` on
   focusable elements; no positive `tabindex`; skip link first and its target exists;
   `target="_blank"` carries `rel`.
3. **Browser audit** (`-m browser`): Playwright with Chromium and axe-core, over every page, in light
   and dark, at 320, 768 and 1280px. Zero violations across the WCAG 2.0 to 2.2 AA tags plus
   best-practice. Items axe marks "needs review" must be listed in `tests/a11y_review.json` with a
   justification, so none pass silently. Behaviour checks: tab order reaches the main content, focus
   outline is visible, focus is not obscured by the sticky nav, no horizontal scroll at 320px, and
   reduced motion disables the canvas and transitions.
4. **Manual checklist** (`docs/accessibility/checklist.md`): keyboard walkthrough, 200% and 400% zoom,
   forced colours, a screen-reader spot check, link and alt-text quality, form error flows. Completed
   and dated per sprint.

Tooling: `playwright` and `axe-playwright-python` go in `dev-requirements.txt`, never a root
`requirements.txt` (Cloudflare Pages may auto-install that and a failure would break the production
deploy). Chromium is already installed for Playwright on this machine.

Definition of done for every sprint from here on: all four layers pass for what changed, any new
component has an accessibility note, and no allowlist entry lacks a reason.

### Baseline handling

Sprint 1's frozen snapshots proved the generated pages equal the pre-build site. They are
re-snapshotted from merged output at the start of 2a (T0), so the footer unification stops being a
standing exception. From then on 2a's intentional changes are expressed as declared deltas (the
class-mapping table, the added skip link and `<main>`), and baseline-independent invariants (chrome
identical across pages, links resolve, forms, ids and scripts present) provide the lasting protection.

## Plan outline for 2a

Each task is test-first and individually reviewable.

- **T0** Re-snapshot baselines from merged output; investigate root cause 5 on Projects.
- **T1** `theme.json`, the generator, and the contrast test (red against today's colours).
- **T2** Static HTML lint and the browser gate wired up, red against today's pages.
- **T3** Migrate `assets/styles.css`, page fragments and inline styles to semantic tokens; the colour-literal lint goes green.
- **T4** Light-led rhythm: section variants, the class-mapping delta, gold CTA band.
- **T5** Image pipeline, registry and macro; place the five photos.
- **T6** Accessibility floor: skip link, `<main>`, heading order, focus ring, reduced motion, target size.
- **T7** All gates green, per-page visual review, manual checklist completed, docs updated.

## Phase 2b, 2c and Phase 3 outline

- **2b**: more light colour, textures and surface styling around the pages. Built on the 2a tokens.
- **2c**: the light/dark switch. Respects `prefers-color-scheme`, persists the choice, avoids a flash of
  the wrong theme, and the control is a labelled button with `aria-pressed`. The dark token set already
  exists from 2a; the canvas colours become token-driven here.
- **Phase 3**: a full WCAG 2.2 AA review against the checklist, the pause control, the public
  accessibility statement (target level, feedback contact, known limitations, date), the screen-reader
  pass, and closing out every "needs review" allowlist entry.

## Risks

- **Token migration touches every CSS rule.** Mitigated by the contrast and literal-colour lints, a
  per-page visual review, and the structural parity checks staying in place.
- **Image weight.** Mitigated by the per-file budget, lazy loading, and `srcset`.
- **Gold misused as text on light.** Prevented by the pairing test; the generator will not emit an
  undeclared pair.
- **Text over photos.** Prevented by rule; the one exception (hero scrim) is allowlisted with a reason.
- **Internal folders are fetchable by URL** because Cloudflare serves the repo root. Unchanged from
  Sprint 1; a `public/` output folder would fix it and is worth doing before more assets land here.
- **Playwright version drift against the installed Chromium.** Pin the version and document the
  `playwright install chromium` step.

## Open questions

1. Whether 2b and 2c also precede the Phase 1 content sprints (recommended: decide after 2a).
2. Projects root cause 5 (the `#f9f5ed` text): investigated in T0 before anything changes there.
3. Exact gold-ink values: solved by the generator, then eyeballed on the real pages.
4. Whether to switch the Pages output to a `public/` folder before the image assets arrive.
