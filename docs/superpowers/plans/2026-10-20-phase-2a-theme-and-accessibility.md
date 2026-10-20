# Phase 2a — Theme and Accessibility Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give the site a light-led look built on a generated, contrast-checked colour token system, with photography and an accessibility gate that fails the build on regressions.

**Architecture:** `content/theme.json` is the only place colours are written. `tools/theme.py` resolves it, solves the text-safe golds, checks every required foreground/background pairing, and `build.py` writes `assets/theme.css` from it. Components use contextual role variables (`--ink`, `--surface`, `--accent-ink` …) that a `surface-*` class on each band rebinds, so one component renders correctly on cream, almond, white, navy or gold. Accessibility is enforced in layers: token contrast test, static HTML lint, axe-core in real Chromium, and a manual checklist. A **ratchet file** keeps the suite green mid-sprint while known problems are burned down to zero.

**Tech Stack:** Python 3.14, Jinja2, BeautifulSoup, Pillow, pytest, Playwright (Python) with Chromium, `axe-playwright-python`.

**Spec:** `docs/superpowers/specs/2026-10-20-visual-refresh-and-accessibility-design.md`

## Global Constraints

- Target **WCAG 2.2 level AA**. Contrast minimums: **4.5:1** normal text, **3:1** large text, UI components and focus indicators.
- **Light-led rhythm:** `surface-inverse` (navy) only on the hero or page-head, the nav, the mobile drawer and the footer. Closing call-to-action band is `surface-accent` (gold fill, navy text). Bands alternate `surface-page` (cream) and `surface-alt` (almond); cards are `surface-card` (white).
- Palette: navy `#061325`/`#08182c`, cream `#faf7f0`, paper `#f7f3ea`, almond `#efdecd`, beige `#e8dcc8`, white, gold `#c6a15c`, gold-bright `#ddbd7e`. Gold is a **fill, border or large display type only**; text on light uses the derived `gold-ink`. White text on a gold fill is forbidden (2.43:1); use navy (7.67:1).
- Text roles are **solid colours**, never alpha. Alpha is allowed only for borders, washes and glows, via `color-mix`.
- No colour literal (hex, `rgb()`, `hsl()`, named) outside `content/theme.json`, `assets/theme.css`, and the reasoned allowlist.
- Images: `assets/img/<slug>-{480,960,1600}.webp`, at most **160 KB** per 1600px file, no upscaling, EXIF stripped. Originals are never committed. Every image has non-empty alt or `decorative: true`. Text never sits directly on a photograph.
- Dev dependencies go in `dev-requirements.txt`, **never** a root `requirements.txt`. Deploy path is unchanged: root pages stay generated and committed, no build command on Cloudflare. Only the seven real root `.html` pages are tracked `.html`.
- Page titles keep the em dash. No pricing anywhere. Docs are published by Cloudflare: no personal email addresses, handles, or internal process detail in `docs/`.
- Run Python with `PYTHONUTF8=1` and `python -m pytest`, one command at a time. Tests never write to the real working tree (use `sandbox` or `tmp_path`).
- Work only on branch `phase-2a-theme`. Commits use the repo identity. Never push `master`; do not push at all (the controller pushes).
- **Baseline protocol** (replaces per-test pinned deltas, which cannot express a CSS rewrite). Tasks T1, T3, T4, T5, T6 each declare their expected delta in the task text. Before re-snapshotting, run `python tools/baseline.py diff`; its output must equal the declared delta and nothing else (paste it in the report). Only then run `python tools/baseline.py snapshot` and the full suite. Baselines are never re-snapshotted to turn an unexplained red test green. Lasting protection comes from the baseline-independent tests (chrome identical across pages, rhythm, lint, gate).

## Review Focus

Failure modes the spec implies that no task's happy path would exercise, most likely first. Each is pinned by a named test in the owning task.

1. **A nested context inheriting the wrong tokens.** A `surface-inverse` hero or footer inside a light page must not pick up the parent's `--ink`. Generator emits the complete role set per context; `test_every_context_defines_every_role` (T1).
2. **Contrast of states, not just rest.** Link hover, button hover, placeholder and error text on each surface. Generated pairings include them; `test_state_pairings_are_declared_and_pass` (T1).
3. **An image with a typo'd slug or missing alt shipping silently.** `test_unknown_image_slot_fails_the_build`, `test_registry_requires_alt_or_decorative` (T5).
4. **New photo cards causing horizontal scroll at 320px.** `test_no_horizontal_scroll_at_320` (T2 gate, green by T7).
5. **Focus hidden behind the sticky nav, or a decorative animation ignoring reduced motion.** `test_focus_is_not_obscured_by_the_sticky_nav`, `test_reduced_motion_disables_animation` (T2 gate, fixed in T6).

## File Structure

| File | Responsibility |
|---|---|
| `tools/contrast.py` | WCAG luminance/ratio, alpha composite, minimum-darken solver |
| `tools/theme.py` | Load and resolve `theme.json`, generate required pairings, check them, render CSS |
| `content/theme.json` | Palette, derive rules, contexts per theme, extra pairings |
| `assets/theme.css` | Generated; never hand-edited |
| `tools/images.py`, `tools/optimize_images.py` | Registry loader and `<picture>` renderer; one-shot optimiser CLI |
| `content/images.json` | Image registry (slug, source file, alt or decorative, crop, focal point) |
| `tests/a11y_browser/` | Playwright + axe gate and behaviour tests |
| `tests/a11y_known_issues.json` | The ratchet: today's known problems, burned to empty |
| `tools/a11y_ratchet.py` | Rewrites the ratchet from current results |
| `tools/baseline.py` | Diffs generated pages against baselines; re-snapshots after a declared delta |
| `docs/accessibility/checklist.md` | Manual checklist, completed and dated per sprint |

---

### Task 0: Fresh baselines, the baseline tool, and the Projects badge

**Files:** Create `tools/baseline.py`, `tests/test_baseline_tool.py`; Modify `tests/baseline/*.snap`, `tests/test_parity.py`

**Interfaces:** Produces `tools/baseline.py` with `diff() -> dict[str, list[str]]` (per page, the `page_facts` keys that differ between the generated root page and its snapshot) and `snapshot() -> None` (copies each generated root page over `tests/baseline/<stem>.snap`); `python tools/baseline.py diff|snapshot` prints/does the same. Produces baselines equal to merged output, so no footer exception remains.

- [ ] **Step 0:** Write `tests/test_baseline_tool.py`: `test_diff_is_empty_when_pages_equal_snapshots`; `test_diff_names_the_changed_key` (against a `tmp_path` copy where one page's `<title>` is edited, expects `{"About": ["title"]}`); `test_snapshot_overwrites_only_the_snapshot_files`. Run: FAIL, then implement `tools/baseline.py` using `tests/parity.page_facts`.

- [ ] **Step 1:** Copy each generated root page over `tests/baseline/<stem>.snap`. Remove the `FOOTER_UNIFIED`/`FOOTER_ADDED`/`FOOTER_REMOVED` special-casing and `test_footer_delta_is_exactly_the_agreed_links` from `tests/test_parity.py`; the generic per-key and `doc_shape` comparisons now apply to every page unmodified.
- [ ] **Step 2:** Run `python -m pytest tests -q`. Expected: all pass. Run `python build.py --check`. Expected: `stale: none`.
- [ ] **Step 3:** Record the known finding in the commit message: `.badge-dev` on Projects cards 3 and 4 is cream text on a light card (1.01:1), a real invisible-text bug fixed in T3 through tokens.
- [ ] **Step 4:** Commit.

---

### Task 1: Contrast library, theme data, generator

**Files:** Create `tools/contrast.py`, `tools/theme.py`, `content/theme.json`, `assets/theme.css`, `tests/test_contrast.py`, `tests/test_theme.py`; Modify `build.py`, `templates/base.j2`, `robots.txt`, `tests/test_robots.py`

**Interfaces:**
- Produces in `tools/contrast.py`: `ratio(fg: str, bg: str) -> float`, `composite(fg: str, alpha: float, bg: str) -> str`, `solve_min_darken(fg: str, backgrounds: list[str], minimum: float) -> str` (the lightest darkening of `fg` reaching `minimum` against every background).
- Produces in `tools/theme.py`: `load_theme(path: Path = THEME_PATH) -> dict`, `resolve(theme: dict) -> dict` (`{theme: {context: {role: "#rrggbb"}}}`, derived values solved), `required_pairings(resolved) -> list[Pairing]` where `Pairing = (theme, context, fg_role, bg_role, minimum, label)`, `failures(resolved) -> list[str]`, `render_css(resolved) -> str`.
- Produces in `build.py`: `render_theme() -> str`; `main()` writes `assets/theme.css`; `check()` also reports `assets/theme.css` when stale.
- Contexts: `page`, `alt`, `card`, `inverse`, `accent`. Roles per context: `surface`, `ink`, `ink-muted`, `accent-ink`, `line`, `field-bg`, `field-border`, `field-ink`, `field-placeholder`, `focus-ring`, `danger-ink`, `success-ink`. Global: `accent-fill`, `on-accent`.
- `base.j2` emits `<link rel="stylesheet" href="assets/theme.css">` immediately before `{{ head_extra }}`.

- [ ] **Step 1: Write the failing tests.**
  - `tests/test_contrast.py`: `ratio("#c6a15c","#ffffff")` ≈ 2.43; `ratio("#061325","#c6a15c")` ≈ 7.67; `ratio("#72787e","#061325")` ≈ 4.17 (all `pytest.approx(abs=0.01)`); `composite` of cream at 0.5 over navy equals a hex whose ratio against navy matches the direct computation; `solve_min_darken("#c6a15c", ["#efdecd"], 4.5)` returns a colour with `ratio ≥ 4.5` while one 1% lighter step gives `< 4.5`.
  - `tests/test_theme.py`: `test_every_context_defines_every_role`; `test_all_required_pairings_pass` (empty `failures`) for both `light` and `dark`; `test_state_pairings_are_declared_and_pass` (link hover, button hover, placeholder, error text each appear in `required_pairings`); `test_gold_ink_is_text_safe_on_every_light_surface` (≥ 4.5 on white, cream, almond, beige); `test_text_roles_are_solid` (no `rgba(`/alpha in any `ink*`, `accent-ink`, `*-ink` role); `test_theme_css_is_fresh` (`assets/theme.css` equals `build.render_theme()`); `test_dark_theme_defines_the_same_roles_as_light`.
- [ ] **Step 2:** Run both files. Expected: FAIL, `ModuleNotFoundError: tools.contrast`.
- [ ] **Step 3:** Implement `tools/contrast.py` (WCAG 2.x relative luminance; solver steps the darkening factor until every background passes).
- [ ] **Step 4:** Write `content/theme.json`: `palette`, `derive` (`gold-ink` from `gold`, `ink-muted` from slate `#5d6c7b` solved against white/cream/almond/beige at 4.5, `ink-inverse-muted` solved on navy at 4.5), `themes.light` and `themes.dark` each with all five contexts, `pairings` for extras. Cream-at-alpha text from the old CSS collapses to three inverse tones: `ink` (cream), `ink-muted` (soft, ≥ 7:1), and the muted tone ≥ 4.5:1.
- [ ] **Step 5:** Implement `tools/theme.py`. `required_pairings` is generated from the role list so a new context cannot skip a check: `ink/surface` 4.5, `ink-muted/surface` 4.5, `accent-ink/surface` 4.5, `danger-ink/surface` 4.5, `success-ink/surface` 4.5, `field-ink/field-bg` 4.5, `field-placeholder/field-bg` 4.5, `field-border/surface` 3.0, `focus-ring/surface` 3.0, global `on-accent/accent-fill` 4.5, and `accent-fill/surface` 3.0 for display type on `inverse`. `render_css` emits `:root` default (light, `page` context) plus `.surface-<context>` blocks and `[data-theme="dark"] .surface-<context>` blocks, each with the complete role set.
- [ ] **Step 6:** Wire `build.py` and `base.j2`. Run `python build.py`. **Declared delta:** the `head` fact of all seven pages gains exactly one `<link rel="stylesheet" href="assets/theme.css">`, and nothing else changes. Run `python tools/baseline.py diff`, confirm that is all it reports, then `python tools/baseline.py snapshot`.
- [ ] **Step 7:** Run the full suite. Expected: all pass; `python build.py --check` → `stale: none`.
- [ ] **Step 8:** `tools/` is a new folder Cloudflare will serve: add `Disallow: /tools/` to the `*` group of `robots.txt` (everything else in that file unchanged) and add `"tools"` to the directories `tests/test_robots.py` asserts. Run the robots tests. Expected: pass.
- [ ] **Step 9:** Commit.

---

### Task 2: The accessibility gate, ratcheted

**Files:** Create `tests/test_a11y_static.py`, `tests/a11y_browser/conftest.py`, `tests/a11y_browser/test_axe.py`, `tests/a11y_browser/test_behaviour.py`, `tests/a11y_known_issues.json`, `tools/a11y_ratchet.py`, `tests/a11y_review.json`; Modify `dev-requirements.txt`, `tests/conftest.py`, `DEPLOY.md`

**Interfaces:**
- `dev-requirements.txt` gains pinned `playwright` and `axe-playwright-python`; `tests/conftest.py` registers the `browser` marker. The documented setup step is `playwright install chromium`.
- `tests/test_a11y_static.py`: `lint_page(stem: str, html: str) -> list[tuple[str, str]]` returning `(rule_id, detail)`. Rule ids: `main-landmark`, `h1-count`, `heading-order`, `html-lang`, `img-alt`, `form-labels`, `unique-ids`, `link-names`, `button-names`, `aria-hidden-focusable`, `tabindex-positive`, `skip-link`, `target-blank-rel`.
- `tests/a11y_browser/conftest.py`: session fixture `site_url` serving the repo root from a `ThreadingHTTPServer` on a free port with logging silenced; `run_axe(page, width) -> list[Violation]` using WCAG 2.0–2.2 A/AA tags plus best-practice, with `.reveal` elements forced visible first.
- Ratchet file shape: `{"static": {"<stem>|<rule>": n}, "axe": {"<stem>|<width>|<rule>": nodes}}`. `tools/a11y_ratchet.py --update` rewrites it from current results.
- `tests/a11y_review.json`: `{"items": [{"page","rule","selector","reason"}]}`; every axe "needs review" result must match an entry.

- [ ] **Step 1: Write the tests.**
  - Static: `test_static_lint_has_no_new_problems` (current counts ≤ ratchet for every key; any key not in the ratchet must be 0) and `test_static_ratchet_is_tight` (a count lower than recorded fails with the instruction to run `tools/a11y_ratchet.py --update`).
  - Axe, parametrised over `PAGES` × widths `320, 768, 1280`: `test_axe_has_no_new_violations` and `test_axe_ratchet_is_tight`, same semantics; `test_every_needs_review_item_is_justified`.
  - Behaviour (`-m browser`): `test_tab_order_reaches_main_content`, `test_focus_outline_is_visible` (computed outline width ≥ 2px on every focusable control on Home), `test_focus_is_not_obscured_by_the_sticky_nav`, `test_no_horizontal_scroll_at_320`, `test_reduced_motion_disables_animation` (emulated `prefers-reduced-motion: reduce` leaves no running CSS animation and the iris loop idle).
- [ ] **Step 2:** `pip install -r dev-requirements.txt` and `playwright install chromium`. Run the behaviour tests and static lint. Expected: the **behaviour tests that detect real defects FAIL** (no skip link, hidden focus, motion); mark exactly those with `@pytest.mark.xfail(strict=True, reason="fixed in Task 6")` so the suite stays green and an unexpected pass is flagged.
- [ ] **Step 3:** Implement the lint rules and the Playwright fixtures. Run `python tools/a11y_ratchet.py --update` once to record today's state (7 pages: contrast, heading order, regions, and the missing `<main>` on four pages).
- [ ] **Step 4:** Run the full suite. Expected: all pass; the strict-xfail tests report as xfail. Add the gate commands and the "browser tests need Chromium" note to `DEPLOY.md`.
- [ ] **Step 5:** Commit.

---

### Task 3: Migrate to tokens

**Files:** Modify `assets/styles.css`, `templates/base.j2`, `templates/_footer.j2`, `templates/pages/*.json` (`head_extra`, `body_scripts`), `templates/pages/*.body.frag`; Create `tests/test_no_color_literals.py`, `tests/color_literal_allowlist.json`; regenerate pages.

**Interfaces:** Consumes the roles and contexts from T1. Produces a codebase with no colour literals outside the theme and the allowlist.

- [ ] **Step 1: Write the failing test** `tests/test_no_color_literals.py::test_no_color_literals_outside_the_theme`. It scans `assets/*.css` (except `theme.css`), `templates/*.j2`, `templates/pages/*`, and `assets/site.js` for hex, `rgb()`, `hsl()` and named colours (`white`, `black`), and fails on any not covered by `tests/color_literal_allowlist.json` (`{"path","literal","reason"}`). Also `test_allowlist_entries_are_still_used` so it cannot rot.
- [ ] **Step 2:** Run. Expected: FAIL listing ~180 literals.
- [ ] **Step 3:** Migrate by these decisions:
  - Components read only contextual roles. Navy bands, nav, drawer, footer and heroes get `surface-inverse` (nav/footer in `base.j2`); existing `.paper` becomes `surface-page`; `.navy` becomes `surface-inverse` for now (T4 re-maps bands).
  - Cream-at-alpha text: α ≥ 0.78 → `--ink`; 0.62–0.77 → the soft inverse tone; below 0.62 → `--ink-muted`. This fixes the footer-bottom text on every page.
  - Gold-at-alpha borders, glows and washes → `color-mix(in srgb, var(--accent-fill) N%, transparent)`.
  - Status colours (`#c0654a`, `#4a9c72`, `#e89b86`) → `--danger-ink`, `--success-ink`, `--line`-family roles.
  - `.badge-dev` and similar dark-card components switch to contextual roles, which makes the invisible Projects badge readable on light cards.
  - Decorative ghost numerals (`.project-index`, BizCheck step numbers) get `aria-hidden="true"` rather than recolouring.
  - Allowlist, each with a reason: the logo SVG fills, and the iris canvas colours in `site.js` (token-driven in Phase 2c).
- [ ] **Step 4:** Regenerate pages (`python build.py`). **Declared delta:** `head` and `inline_styles` text (the CSS rewrite), `class` tokens on the `surface-*` bands and on nav/footer, added `aria-hidden="true"` on the ghost numerals. `nav`, `drawer`, `nav_cta`, links, ids, form fields, `inline_scripts` text (apart from `site.js` colour handling) and page text must NOT change. Run `python tools/baseline.py diff`, confirm it reports only those keys, then `python tools/baseline.py snapshot`.
- [ ] **Step 5:** Run `python tools/a11y_ratchet.py --update`; the `color-contrast` entries must shrink or vanish. Run the full suite. Expected: all pass.
- [ ] **Step 6:** Capture 1280px and 375px screenshots of all seven pages before and after into the scratchpad and review them side by side for unintended change.
- [ ] **Step 7:** Commit.

---

### Task 4: Light-led rhythm

**Files:** Modify `templates/pages/*.body.frag`, `assets/styles.css`; Create `tests/test_rhythm.py`

**Interfaces:** Consumes `surface-*` contexts. Produces the band mapping below; its declared delta is exactly the band class changes in `BAND_MAP` plus the removed `iris2` canvas.

- [ ] **Step 1: Write the tests.**
  - `tests/test_rhythm.py`: `test_inverse_surface_only_on_hero_nav_drawer_footer`; `test_no_two_adjacent_bands_share_a_surface`; `test_final_band_is_the_gold_cta` (every page that has one); `test_cards_use_the_card_surface`.
- [ ] **Step 2:** Run. Expected: FAIL.
- [ ] **Step 3:** Apply `BAND_MAP`. Heroes (`hero`, `pagehead`, `bc-hero`, `contact-hero`, `nf`) stay `surface-inverse`.

  | Page | Band | Becomes |
  |---|---|---|
  | Home | `#services` paper | `surface-page` |
  | Home | `#process` navy | `surface-alt` |
  | Home | `#why` paper | `surface-page` |
  | Home | `#about` navy | `surface-alt` |
  | Home | CTA navy | `surface-accent` |
  | Home | marquee strip | `surface-alt` |
  | About | paper | `surface-page` |
  | About | stat band (`section.navy`) | `surface-alt` |
  | About | paper | `surface-page` |
  | About | navy (`h2`+`h3`) | `surface-alt` |
  | About | CTA | `surface-accent` |
  | Services, Projects | `main` paper | `surface-page` |
  | Services, Projects | CTA | `surface-accent` |
  | BizCheck | `#how` paper | `surface-page` |
  | BizCheck | `#panel` navy | `surface-alt` |
  | BizCheck | `#sample` paper | `surface-page` |
  | BizCheck | `#submit` navy | `surface-alt`; form card becomes `surface-card`; the decorative `iris2` canvas is removed |
  | Contact, 404 | hero | unchanged (`surface-inverse`) |

- [ ] **Step 4:** Regenerate pages. Run `python tools/baseline.py diff`; it must report only `body_rest`/`doc_shape` class changes matching `BAND_MAP` and the `iris2` removal, then `python tools/baseline.py snapshot`. Run the full suite and the ratchet update. Expected: all pass; contrast entries remain at or below T3's.
- [ ] **Step 5:** Screenshot review at 1280px and 375px.
- [ ] **Step 6:** Commit.

---

### Task 5: Photography

**Files:** Create `tools/images.py`, `tools/optimize_images.py`, `content/images.json`, `assets/img/*.webp`, `tests/test_images.py`; Modify `build.py`, `templates/pages/{index,About,BizCheck,Contact}.body.frag`, `assets/styles.css`, `dev-requirements.txt` (Pillow)

**Interfaces:**
- `tools/images.py`: `load_registry(path: Path = REGISTRY_PATH) -> dict`, `render_picture(slug: str, sizes: str, loading: str = "lazy", cls: str = "") -> str`.
- `tools/optimize_images.py <source-dir>`: reads the registry, writes the three widths per slug, never upscales, strips EXIF, exits non-zero on a missing source or a file over 160 KB.
- Pages use a placeholder `<image-slot slug="us-night" sizes="…" loading="lazy"></image-slot>` in fragments; `build.expand_image_slots(html: str) -> str` replaces it with `render_picture(...)` and raises `KeyError` naming the slug if unknown.
- Registry (slug → source file name; the source folder is the owner's stock-images folder, passed on the command line and never recorded in the repo): `us-night` ← `nasa-1lfI7wkGWZ4-unsplash.jpg`, `skyscrapers` ← `sean-pollock-PhYq704ffdA-unsplash.jpg`, `globe` ← `kyle-glenn-nXt5HtLmlgE-unsplash.jpg`, `lightbulb` ← `diego-ph-fIq0tET6llw-unsplash.jpg`. Four photos; Projects gets none.

- [ ] **Step 1: Write the tests.**
  - `test_registry_requires_alt_or_decorative`; `test_every_registry_slug_has_all_three_files`; `test_no_1600_file_exceeds_160kb`; `test_render_picture_has_srcset_sizes_dimensions_and_alt` (width/height attributes present, `decoding="async"`); `test_above_the_fold_images_are_not_lazy` (a slot with `loading="eager"` renders eager); `test_unknown_image_slot_fails_the_build`; `test_no_background_image_under_text` (CSS `background-image: url(` only in the allowlist).
- [ ] **Step 2:** Run. Expected: FAIL, missing modules.
- [ ] **Step 3:** Implement `tools/images.py` and `build.expand_image_slots`; call it in `render_all`.
- [ ] **Step 4:** Run `python tools/optimize_images.py "<source dir>"` and commit the generated `assets/img/*.webp` only.
- [ ] **Step 5:** Place the slots and the supporting CSS: Home `#why` band (`us-night`, framed card beside the figures), About first page band (`skyscrapers`), Contact intro column (`globe`), BizCheck `#how` band (`lightbulb`). Photos sit beside or above text on solid surfaces, never behind it.
- [ ] **Step 6:** Regenerate. **Declared delta:** the four placements add one `<picture>` (with its wrapper) each to Home, About, Contact and BizCheck, plus new CSS; Services and Projects are unchanged. Run `python tools/baseline.py diff`, confirm, snapshot, then the full suite and the ratchet update. Expected: all pass; `test_no_horizontal_scroll_at_320` still green.
- [ ] **Step 7:** Commit.

---

### Task 6: The accessibility floor

**Files:** Modify `templates/base.j2`, `templates/_footer.j2`, `assets/styles.css`, `assets/site.js`, `templates/pages/*.body.frag`

**Interfaces:** Consumes the T2 gate; the strict-xfail marks added there are removed here as each defect is fixed.

- [ ] **Step 1:** Remove the `xfail` marks one by one as each fix lands; a strict xfail that starts passing fails the suite until its mark is removed, which is the signal.
- [ ] **Step 2:** Skip link as the first focusable element in `base.j2` (`<a class="skip-link" href="#main">`), visible on focus, styled with tokens.
- [ ] **Step 3:** Exactly one `<main id="main">` per page, wrapping all primary content after the hero/page-head: Home, About, BizCheck and Contact gain one; Services, Projects and 404 gain `id="main"`.
- [ ] **Step 4:** Heading order: footer column headings `h4` → `h2` (CSS selector updated); Home's `#about` band `h4` → `h3`. The static lint `heading-order` entry must reach zero.
- [ ] **Step 5:** Focus: a two-tone `:focus-visible` ring from the `focus-ring` role per context; `html { scroll-padding-top: calc(var(--nav-h) + 16px) }`.
- [ ] **Step 6:** Reduced motion: honour `prefers-reduced-motion: reduce` for reveal transitions, parallax, magnetic buttons, counters, the marquee and the iris loop; `.reveal` content is simply visible.
- [ ] **Step 7:** Target size: every interactive control at least 24×24 CSS px (chips, nav toggle, footer links).
- [ ] **Step 8:** Regenerate. **Declared delta:** the skip link, `<main id="main">` wrappers, footer heading level `h4` → `h2`, Home's `h4` → `h3`, and the new focus/motion/target-size CSS. Run `python tools/baseline.py diff`, confirm, snapshot, then `python tools/a11y_ratchet.py --update`. Expected: every `static` entry and the axe `landmark-one-main`, `region`, `heading-order` entries are gone.
- [ ] **Step 9:** Commit.

---

### Task 7: Zero known issues, checklist, and review

**Files:** Modify `tests/a11y_known_issues.json`, `DEPLOY.md`; Create `docs/accessibility/checklist.md`, `docs/accessibility/2026-10-2a-review.md`

- [ ] **Step 1: Write `test_a11y_ratchet_is_empty`** (both sections `{}`); run it. Expected: FAIL while anything remains.
- [ ] **Step 2:** Fix whatever remains (contrast stragglers, `needs review` items either resolved or justified in `tests/a11y_review.json`). Re-run `python tools/a11y_ratchet.py --update` until the file is `{"static": {}, "axe": {}}`.
- [ ] **Step 3:** Remove the ratchet machinery's tolerance: the axe and static tests now simply assert zero. Keep `a11y_ratchet.py` only if still useful; otherwise delete it.
- [ ] **Step 4:** Write `docs/accessibility/checklist.md` (keyboard walkthrough, 200%/400% zoom, forced colours, screen-reader spot check, link and alt-text quality, form error flow) and complete and date it for this sprint in `2026-10-2a-review.md`.
- [ ] **Step 5:** Update `DEPLOY.md`: theme generation, the image pipeline, running the gate, and that `assets/theme.css` is generated.
- [ ] **Step 6:** Run the full suite (default and `-m browser`) twice; confirm a clean tree afterwards; `python build.py --check` → `stale: none`.
- [ ] **Step 7:** Commit.

---

## Self-review notes

- Spec coverage: tokens/generator (T1), pairings and states (T1), gate layers 1–4 (T1, T2, T7), rhythm and CTA band (T4), photography and placement (T5), accessibility floor (T6), baseline handling (T0, pinned deltas throughout), Phase 2b/2c/3 are out of scope here and stay in the spec.
- The spec's "five photos" line in conversation was four photos here; the spec table lists four placements and Projects has none.
- Out of scope, deliberately: pause control, accessibility statement, screen-reader pass (Phase 3), the dark theme in the browser matrix (Phase 2c; the dark tokens are generated and contrast-tested now).
