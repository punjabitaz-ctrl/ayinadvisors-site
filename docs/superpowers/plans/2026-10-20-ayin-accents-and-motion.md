# Phase 2b: AYiN Accents and Motion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give the Home sections after the hero AYiN-specific accents (ayin letter band, spring ripples, iris markers) with 3D, assembling motion and parallax, then roll the shared components out to the other pages, without breaking the accessibility gate.

**Architecture:** Reusable CSS components in `assets/styles.css` (with motion tokens) and one small motion module in `assets/site.js` driven by `data-` attributes. Markup lives in page fragments; inline SVG icons live in a small partial/snippet file so they are defined once. All motion is gated by `prefers-reduced-motion`.

**Tech Stack:** Jinja2/build.py, plain CSS and JS, existing Playwright + axe gate.

**Spec:** `docs/superpowers/specs/2026-10-20-ayin-accents-and-motion-design.md`

## Global Constraints

- The Phase 2a gate stays at zero: `python -m pytest tests -q` (static lint, axe at 320/768/1280, behaviour, pixel-contrast, rhythm, no colour literals) must pass at the end of every task. No ratchet exists any more; do not add one.
- All decorative elements `aria-hidden="true"`, not focusable. The letters group is `role="img"` with an `aria-label` stating the meaning. Reduced motion: final state, no transitions, no tilt, no parallax, no ripple emission.
- No element animates on its own for more than 5 seconds; nothing flashes; ripples run at most 5 s after entering view then rest.
- No colour literals outside `content/theme.json`, `assets/theme.css` and the reasoned allowlist. Use theme roles. The only new allowlist candidates are SVG presentation values, and these must use `currentColor`/CSS variables instead.
- No horizontal scroll at 320px; no new third-party scripts; CSP, forms and Turnstile untouched. Fonts: subsetted Google Fonts request limited to the glyph characters used (via `text=`), allowed by the existing CSP; the page must read correctly if the font fails to load.
- Transforms and opacity only inside animations; observers unobserve after the first run.
- Baseline protocol: declare the delta, run `python tools/baseline.py diff`, paste output, then `python tools/baseline.py snapshot`. Never snapshot to turn an unexplained red test green. Run Python with `PYTHONUTF8=1` and `python -m pytest`, one command at a time; tests never write to the real tree. Work only on `phase-2b-accents`; never push.
- Copy: no em dashes in new visible copy except where the existing site already uses them; no pricing; no personal info in docs.

## Review Focus

1. **Reduced motion leaves content hidden or mis-placed.** `test_reduced_motion_shows_final_state` (T1): with the preference on, no element has `opacity < 1`, a non-identity 3D transform, or a running animation.
2. **Content invisible if JS fails or the observer never fires.** Initial hidden state is applied only by JS adding a class (`html.js`), never by CSS alone (T1 test with JS disabled: everything visible).
3. **Horizontal scroll from rotated/offset 3D elements and ripples at 320px.** Existing `test_no_horizontal_scroll_at_320` (all pages) must stay green; sections get `overflow: clip` where needed (T2, T3).
4. **Font failure hides the meaning.** `test_letters_band_has_text_label` asserts `role="img"` with a label containing "eye" semantics and `aria-hidden` on glyphs (T2).
5. **Animation longer than 5 s.** `test_no_long_running_animation_after_load` samples `document.getAnimations()` 6 s after the bands have entered view: none running except those already existing before this plan (hero iris/scrolldot, which Phase 3 owns) (T2).

## File Structure

| File | Responsibility |
|---|---|
| `assets/styles.css` | Motion tokens, `.accent-*` components (letters band, ripples, iris marker, 3D card, assemble states) |
| `assets/site.js` | `data-assemble` observer, pointer tilt, scroll parallax, all gated by reduce |
| `templates/_iris.j2` or `content/icons.json` + build expansion | Iris icon snippets defined once |
| `templates/pages/*.body.frag` | Placement of accents |
| `tests/test_motion_*.py`, `tests/a11y_browser/test_motion.py` | Pinned behaviour |
| `docs/accessibility/2026-10-2b-review.md` | Dated review of the new motion |

---

### Task 1: Motion foundation and components

**Files:** Modify `assets/styles.css`, `assets/site.js`, `templates/base.j2` (only if the `html.js` class is not already set), `build.py` (only if icon snippets are expanded at build); Create `tests/a11y_browser/test_motion.py`, tests for any build helper.

**Interfaces:** Produces CSS classes `.ripples` (+ `.ripples-r`, `.ripples-l`), `.iris-mark`, `.iris-ico`, `.letters` band classes, `.assemble` container with `data-assemble` states `pre`/`in`, `.tilt3d`; JS `data-assemble` on a section starts its children's assembling when it enters view; `data-tilt` on a card enables pointer tilt; `data-parallax` already exists for the hero, reuse its convention for ripples. Consumed by T2 and T3.

- [ ] **Step 1: Tests first.** `test_reduced_motion_shows_final_state`, `test_content_visible_without_js`, `test_tilt_and_parallax_inert_under_reduced_motion` (pointer events and scroll leave transforms unchanged), `test_assemble_runs_once` (second view does not replay). Run: FAIL.
- [ ] **Step 2:** Implement the CSS components using theme roles (accent-ink/accent-fill/line-gold), motion tokens (durations, one expo-out easing), the reduce media query, `overflow: clip` helper, and the JS module (observer + tilt + parallax) matching the mockup's behaviour: cards assemble from alternating angles with `translateZ`, glyphs from scattered positions, icon strokes draw ring by ring via dasharray, process line grows, steps rise in sequence; ripples emit for at most 5 s once, then rest as static rings; parallax drifts ripples at about 0.12 scroll with slight rotation.
- [ ] **Step 3:** Run the new tests and the full suite. Declared delta: none to generated pages (components not placed yet) except `head`/`inline_styles` if CSS lives in page head; `assets/*` only otherwise. `python tools/baseline.py diff`, snapshot if it matches.
- [ ] **Step 4:** Commit.

---

### Task 2: Home: letters band, ripples, iris markers

**Files:** Modify `templates/pages/index.body.frag`, `templates/pages/index.json` (font link in `head_extra`), `assets/styles.css`; extend `tests/a11y_browser/test_motion.py`, `tests/test_rhythm.py` if the marquee is referenced.

**Interfaces:** Consumes T1 components.

- [ ] **Step 1: Tests first.** `test_letters_band_has_text_label` (group `role="img"`, aria-label states the meaning, glyph spans `aria-hidden`, four glyphs ع ע 𐤏 O present), `test_marquee_is_replaced` (no `.marquee` on Home), `test_no_long_running_animation_after_load` (Review Focus 5), `test_home_rhythm_still_alternates` (existing rhythm tests keep passing with the band as `surface-alt`).
- [ ] **Step 2:** Replace the marquee with the letters band (`surface-alt`, same position). Add ripples behind `#services` (right) and `#process` (left) headings, the iris eyebrow marker (replacing the `sec-index` dash number on the two eyebrows), four iris card icons (focus, linked rings, two irises, widening arcs) replacing `.svc-num`, process-step iris growth (1 to 4 rings). Font: add the subsetted stylesheet link for the glyph fonts in `index.json` `head_extra`, `display=swap`.
- [ ] **Step 3:** Regenerate. **Declared delta:** Home only: `head` (font link), `body_rest`/`doc_shape` (band, ripples, icons, markers), possibly `assets`; no other page changes. Run `python tools/baseline.py diff`, confirm, snapshot, full suite twice (default).
- [ ] **Step 4:** Screenshots at 1280 and 375 of Home including mid-assemble and settled states; look at them; check no overflow at 320; check text contrast stays on solid surfaces.
- [ ] **Step 5:** Commit.

---

### Task 3: Roll out to the other pages and review doc

**Files:** Modify `templates/pages/{About,Services,Projects,BizCheck,Contact}.body.frag`, `assets/styles.css`; Create `docs/accessibility/2026-10-2b-review.md`; Modify `DEPLOY.md` (motion notes, short).

**Interfaces:** Consumes T1 components (T2 patterns).

- [ ] **Step 1: Tests first.** `test_every_section_head_has_the_iris_marker` (pages with `.sec-head` eyebrows use the marker, aria-hidden), `test_card_grids_assemble_and_tilt_hooks_present` (`data-tilt`/assemble on Services, Projects card grids; BizCheck steps).
- [ ] **Step 2:** Apply the iris eyebrow marker to every section head; ripples behind one heading per page where it fits (not on hero or form pages); assemble/tilt on the card grids on Services and Projects and the BizCheck step cards; leave forms, Turnstile, hero canvases and Contact form untouched.
- [ ] **Step 3:** Regenerate. **Declared delta:** `body_rest`/`doc_shape` class and decorative-SVG additions on About, Services, Projects, BizCheck, Contact (marker only), plus CSS. No copy, link, id, form-field or script-text change. Diff, confirm, snapshot, full suite twice including browser tests.
- [ ] **Step 4:** Write the review doc (motion inventory, reduced-motion verification, 2.2.2 reasoning, what was not performed by a human) and short `DEPLOY.md` note. No personal info.
- [ ] **Step 5:** Screenshots of all seven pages at 1280 and 375; look at each; `python build.py --check` stale: none; clean tree.
- [ ] **Step 6:** Commit.

---

## Self-review notes

- Spec coverage: letters band (T2), ripples with 5 s cap (T1/T2), iris markers and icons (T2/T3), 3D cards and tilt (T1/T3), assemble and parallax (T1), reduced motion and no-JS (T1), rollout (T3).
- The existing hero iris and scrolldot animations are out of scope (Phase 3).
- The Phoenician and Arabic glyph rendering depends on the subsetted font; the label carries the meaning if it fails.
