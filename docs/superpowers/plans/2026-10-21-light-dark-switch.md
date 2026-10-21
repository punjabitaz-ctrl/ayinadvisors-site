# Phase 2c: Light and Dark Switch Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let visitors switch between a light and a dark look, defaulting to their system, with no flash, persisted, accessible, and the whole accessibility gate passing in both themes.

**Architecture:** `tools/theme.py` already generates `[data-theme="dark"]` blocks. Add system-preference media blocks and `color-scheme`; a small head script sets `data-theme` before paint; a toggle button in the nav and drawer flips it and persists it; fixed colours (logo, canvases, select arrow, Turnstile theme) move to theme variables; the gate matrix doubles to both themes.

**Tech Stack:** Jinja2/build.py, generated CSS, plain JS, Playwright + axe.

**Spec:** `docs/superpowers/specs/2026-10-21-light-dark-switch-design.md`

## Global Constraints

- WCAG 2.2 AA in both themes: `python -m pytest tests -q` (static lint, axe at 320/768/1280, behaviour, pixel-contrast, rhythm, colour literals, form-control boundary contrast) passes at the end of every task; from Task 2 the browser gate runs in BOTH themes. Zero known issues, no ratchet.
- No colour literals outside `content/theme.json`, `assets/theme.css` and the reasoned allowlist; the allowlist may only shrink or change reasons (logo and canvas colours become theme-driven).
- Theme choice: `localStorage` key `ayin-theme`, values `light`|`dark`, always inside try/catch; system preference is the default until the visitor chooses; head script sets `data-theme` on `<html>` before first paint; the page works without JavaScript (system dark via a CSS media rule on `:root:not([data-theme])`, toggle hidden without JS).
- Toggle: `<button>` with stable accessible name "Dark mode" and `aria-pressed`, decorative `aria-hidden` icon, ≥44px touch target, visible focus ring, keyboard operable, focus stays on it, present in both the nav and the mobile drawer.
- `color-scheme` set per theme; `<meta name="theme-color">` follows the active theme (navy in both; document the value used).
- Colour transitions on theme change: none under reduced motion, otherwise ≤200 ms colours only, never layout properties.
- CSP, forms, Turnstile verification and copy untouched; no new third-party scripts; inline head script is the only new inline script (CSP already allows inline).
- Baseline protocol: declare the delta, `python tools/baseline.py diff`, paste output, then `python tools/baseline.py snapshot`; never snapshot to turn an unexplained red test green. Run Python with `PYTHONUTF8=1` and `python -m pytest`, one command at a time; tests never write to the real tree. Work only on `phase-2c-theme-switch`; never push.
- No personal info in docs (Cloudflare publishes them); no em dashes in new visible copy.

## Review Focus

1. **Flash of wrong theme.** Test that with a stored `dark` choice and a light system (and the reverse) `html[data-theme]` is already correct at `DOMContentLoaded`, before first paint (inline script in head, before the stylesheet), and the first rendered frame uses the right background.
2. **Storage blocked or throwing.** Toggle still works for the visit; no uncaught exception; page loads in the system theme.
3. **System change after choosing.** A stored choice is never overridden by a system change; with no stored choice the page follows system changes live.
4. **Dark-only contrast failures** that token pairings miss (components using the wrong role, translucent fills, images, the logo, canvases, placeholders, focus rings, selection, hover states). Gate in dark must find them; fix at the source.
5. **Toggle semantics.** Name stays "Dark mode"; `aria-pressed` matches `data-theme`; nav and drawer buttons stay in sync; hidden without JS; 44px target; visible focus in both themes.

## File Structure

| File | Responsibility |
|---|---|
| `tools/theme.py`, `content/theme.json`, `assets/theme.css` | Add `color-scheme`, `prefers-color-scheme` rules scoped to `:root:not([data-theme])`, keep explicit `data-theme` blocks |
| `templates/base.j2` | Head script, toggle in nav and drawer, theme-color meta handling |
| `assets/site.js` | Toggle logic, system-change listener, canvas colour re-read |
| `assets/styles.css` | Toggle styles, dark fixes, image dim, colour transitions |
| `templates/_logo.j2`, `_footer.j2` | Logo fills via CSS variables |
| `tests/a11y_browser/*` | Gate matrix over both themes; theme behaviour tests |
| `docs/accessibility/2026-10-2c-review.md` | Dated review, what a human must still check |

---

### Task 1: Mechanism: tokens, head script, toggle

**Files:** Modify `tools/theme.py`, `assets/theme.css` (generated), `templates/base.j2`, `assets/site.js`, `assets/styles.css`, tests for theme; Create `tests/a11y_browser/test_theme_switch.py`, `tests/test_theme_media.py`

**Interfaces:** Produces `html[data-theme="light"|"dark"]` contract; `window` storage key `ayin-theme`; CSS class `.theme-toggle` (button) with `aria-pressed`; the generator emits `color-scheme` and media blocks. Consumed by Task 2 and 3.

- [ ] **Step 1: Tests first (RED).** `test_theme_css_has_system_dark_rules_scoped_to_unset_theme` (generated CSS contains `@media (prefers-color-scheme: dark)` with `:root:not([data-theme])` and the complete role set per context, and `color-scheme`); `test_theme_css_is_fresh` still green; browser: `test_no_flash_stored_choice_beats_system[light|dark]` (attribute set at DOMContentLoaded via an init script that records `document.documentElement.dataset.theme` at first parse), `test_follows_system_when_no_choice_and_live_changes`, `test_stored_choice_not_overridden_by_system_change`, `test_storage_blocked_still_toggles` (override `localStorage` to throw), `test_toggle_semantics` (name "Dark mode", `aria-pressed` tracks, nav and drawer in sync, focus stays), `test_toggle_hidden_without_js`, `test_toggle_target_size_44`, `test_theme_switch_does_not_shift_layout` (document height and key element rects equal before and after).
- [ ] **Step 2:** Extend `tools/theme.py` `render_css` to emit `color-scheme`, system-dark media rules for `:root:not([data-theme])` and the surface contexts, keep explicit `[data-theme="dark"]` and add explicit `[data-theme="light"]` precedence; regenerate with `python build.py`.
- [ ] **Step 3:** Add the inline head script (before the stylesheet link) to `base.j2`; add the toggle button (sun/moon decorative SVG) to the nav and drawer; `site.js` toggle handler (flip, persist in try/catch, update `aria-pressed` on all toggles, update `meta[name=theme-color]`, dispatch a `themechange` event) and `matchMedia` change listener only when no stored choice; toggle hidden unless `html.js`; toggle styling with theme roles, two-tone focus ring, 44px target; colour transitions ≤200 ms, none under reduced motion.
- [ ] **Step 4:** Regenerate. **Declared delta:** all pages: `head` (script, meta), nav and drawer subtree (toggle; update the cross-page chrome invariant honestly: still identical across pages), `doc_shape`; no content, link, id (besides toggle ids), form or script-text change. Diff, confirm, snapshot, full suite.
- [ ] **Step 5:** Commit.

---

### Task 2: Dark audit: gate in both themes, fixes

**Files:** Modify `tests/a11y_browser/conftest.py` and tests (theme parametrisation), `assets/styles.css`, `assets/site.js`, `templates/_logo.j2`, `templates/_footer.j2`, `templates/pages/*.json|frag`, `tests/color_literal_allowlist.json`, `tests/a11y_review.json`

**Interfaces:** Consumes Task 1's `data-theme` contract.

- [ ] **Step 1: Tests first (RED).** Parametrise the axe gate, the pixel-contrast review test, the form-control boundary test, the at-rest alignment tests and the 320px scroll test over `theme in (light, dark)` (set via emulated storage/`color_scheme`, assert the attribute). Add `test_logo_and_canvas_follow_theme` (computed fill of the logo mark differs between themes and meets 3:1 against the nav surface in both; canvas colour variables read by `site.js` change on `themechange`), `test_select_arrow_follows_theme`, `test_images_dimmed_only_in_dark`.
- [ ] **Step 2:** Run the gate in dark; collect every failure. Fix at the source (wrong role, translucent fills, placeholders, selection, hover, borders, focus rings, images, hero overlays, canvases, letters band, iris icons, ripples, cards, the gold CTA band, BizCheck form card, Contact fields, Turnstile theme passthrough where possible). Logo SVG fills and canvas colours move to CSS variables (shrink the colour-literal allowlist accordingly; the select-arrow data URI becomes theme-aware via CSS mask or two variants). Add the photo dim for dark.
- [ ] **Step 3:** Any axe needs-review nodes that remain in dark get specific entries with stable selectors verified by the pixel test; no blanket justification; stale entries removed.
- [ ] **Step 4:** Regenerate. **Declared delta:** styles and logo/footer markup only (fills to variables), page head CSS where needed; no copy, link, id, form or script-text change beyond `site.js` colour handling. Diff, confirm, snapshot, full suite twice (about 10 minutes per run).
- [ ] **Step 5:** Screenshots of all seven pages at 1280 and 375 in BOTH themes into the scratchpad; look at every one and report concrete findings (invisible text, glare, clashes, lost borders, wrong band colours, logo legibility).
- [ ] **Step 6:** Commit.

---

### Task 3: Polish, forced colours, docs

**Files:** Create `docs/accessibility/2026-10-2c-review.md`; Modify `DEPLOY.md`, `docs/accessibility/checklist.md` (add the dark-mode items)

- [ ] **Step 1:** Verify forced-colours and print in both themes (toggle visible and legible in forced colours, print always prints the light look); fix what breaks, with tests.
- [ ] **Step 2:** Check the Turnstile widget theme on Contact and BizCheck in dark (server verification untouched); document the behaviour.
- [ ] **Step 3:** Write the dated review doc (what was tested in both themes, how the no-flash guarantee is tested, known limits, and a plain list of what a human must still check: real screen reader on the toggle, real devices in dark mode, real forced-colours and high-contrast settings). Update DEPLOY.md and the checklist. No personal info, no local paths.
- [ ] **Step 4:** Full suite twice, `python build.py --check` stale: none, clean tree, screenshots of both themes final pass.
- [ ] **Step 5:** Commit.

---

## Self-review notes

- Spec coverage: system default and persistence (T1), no flash and no-JS (T1), control semantics (T1), colour-scheme and theme-color (T1), dark appearance and fixed colours (T2), gate in both themes (T2), forced colours, print, docs (T3).
- Out of scope: pause controls (Phase 3), services restructure sprints.
