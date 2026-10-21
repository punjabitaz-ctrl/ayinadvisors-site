# Phase 2b: AYiN accents and motion

Date: 2026-10-20
Branch: `phase-2b-accents` (off Phase 2a, which is live)
Status: approved by the owner after reviewing two mockups ("move forward with them")

## Why

After Phase 2a the light-led pages are accessible but plain: the sections after the Home hero are text on flat colour with nothing that says *AYiN*. The owner asked for accents drawn from what the name means, plus a three-dimensional feel and assembling motion for flair.

## The meaning we draw from

- Arabic ʿayn (ع): the eye; a spring of water; "the very thing itself".
- Hebrew ayin (ע): the eye; a spring (the "Ein" in place names). The same sound, spelled אין, is the Kabbalistic "nothing from which everything comes".
- Phoenician ʿayin (𐤏): the original letter was a drawing of an eye; it became the Greek and Latin O. Persian, Amharic and Syriac keep the letter and the meaning.

## Decisions (owner approved unless marked *my call*)

1. **One letter, three scripts** replaces the Home ticker strip: ع · ע · 𐤏 · O with captions and the line "One letter, three thousand years, and every language that kept it kept its meaning: to see." The glyphs assemble from scattered 3D positions when the band scrolls into view, have a layered 3D extrusion, and respond to the pointer with a gentle tilt. Removing the ticker also removes an endless animation. *My call:* glyphs come from a subsetted web font (the characters only), with an accessible text label on the group so the meaning never depends on the font loading.
2. **Spring ripples**: thin concentric gold rings behind section headings, emitted from a point, drifting with scroll (parallax). *My call:* the emission plays for at most 5 seconds when the section enters view, then rests as static rings. This satisfies WCAG 2.2.2 without needing a pause button for it.
3. **Iris markers**: the "01 — WHAT WE DO" dash gets a small iris glyph; each of the four service cards gets its own iris drawing (focus, linked rings, two irises, widening arcs) that draws itself ring by ring; the process steps show an iris growing ring by ring ("nothing to something").
4. **Three-dimensional look and movement**: cards assemble from different angles and depths and tilt with the pointer, with the icon and text lifted onto separate layers; the process steps rise in sequence while the line grows from a point.
5. Applies to Home first (sections after the hero). The same components then roll out to the other pages' section heads and card grids.

## Non-goals

- No motion that carries information; everything is decorative and `aria-hidden`.
- Idea 4 (geometric star tile) is dropped for now; textures are not part of this slice.
- No pause control for infinite animation here (Phase 3 handles the existing hero and any remaining loops).
- No new third-party scripts; no change to forms, Turnstile or the CSP.

## Accessibility constraints (binding, the Phase 2a gate stays at zero)

- Every new decorative element is `aria-hidden="true"` and not focusable. The letters group gets `role="img"` with a full label.
- `prefers-reduced-motion: reduce`: content is simply in its final state; no assembling, tilt, parallax or ripple emission.
- Nothing flashes; no element animates for more than 5 seconds on its own.
- No horizontal scroll at 320px (3D transforms and ripples clipped by their section).
- Contrast: decorative lines are not text; any text stays on solid surfaces with the Phase 2a tokens.
- Colours come from theme roles (`--accent-ink`, `--accent-fill`, `--line-gold`); no new literals.
- The pointer effects must not trap touch scrolling.

## Performance

Transforms and opacity only; `will-change` limited to the elements animating; the observer unobserves after the first run; no layout-triggering properties in loops.

## Out of scope / later

Phase 2c (light/dark switch), services restructure sprints, Phase 3 (WCAG statement, pause control).
