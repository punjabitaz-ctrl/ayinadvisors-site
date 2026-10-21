# Accessibility checklist

Target: WCAG 2.2 level AA. Run this list before a release that changes layout,
colour, navigation or forms, and record the outcome in a dated review file in
this folder. Items marked "automated" run in the test suite
(`PYTHONUTF8=1 python -m pytest tests`); the others need a person.

Record each item as one of: **pass** (with what was observed), **fail** (with the
fix or a ticket), or **not performed** (say why and who completes it). Never mark
an item pass that was not actually exercised.

## 1. Keyboard walkthrough (every page)

- [ ] The first Tab stop is the "Skip to main content" link, and activating it moves focus into `<main>` (automated: Home).
- [ ] Tab reaches every link, button and form control in a sensible visual order; Shift+Tab reverses it. No keyboard trap.
- [ ] Every focused control shows a focus indicator of at least 2px (automated: Home; walk the other pages by hand).
- [ ] A focused control is never hidden behind the sticky header (automated: Home).
- [ ] Mobile width: the closed menu's links are not reachable by Tab; the menu button reports `aria-expanded`; Escape closes the menu and returns focus to the button (automated).
- [ ] The current page's navigation link is marked `aria-current="page"` (automated).

## 2. Zoom and reflow

- [ ] 200% zoom (about 640 CSS px wide): no horizontal scrolling, no clipped text, nothing overlapping.
- [ ] 400% zoom (320 CSS px wide): the same, with content in one column (automated: scroll width and clipped text at 320px on every page).
- [ ] Text can be enlarged without loss of content or function; no fixed-height boxes cut text off.

## 3. Colour and contrast

- [ ] Every declared text and component pairing passes at build time, in both themes and every surface (automated).
- [ ] axe-core reports zero violations at 320, 768 and 1280px (automated).
- [ ] Every axe "needs review" item is justified in `tests/a11y_review.json` and backed by a pixel measurement (automated).
- [ ] Forced-colours mode: pages stay legible, controls keep a visible boundary, icons built from backgrounds (such as the menu bars) are still drawn.
- [ ] Forced-colours mode as a real operating-system setting (Windows contrast themes), not only browser emulation.

## 3b. Dark mode and the theme switch

- [ ] The full gate (axe, pixel contrast, boundary contrast, behaviour) passes in both themes (automated).
- [ ] With a stored choice and an opposite system theme, the page is in the chosen theme from the first paint, with no flash (automated).
- [ ] The switch is named "Dark mode", reports `aria-pressed`, and the top bar and mobile menu copies stay in sync (automated). With a real screen reader, the name and the on/off state are announced in both places.
- [ ] Blocked storage: the switch still works for the visit and nothing breaks (automated).
- [ ] Real phone and tablet in dark mode: no glare or banding, nothing too faint, photographs look right.
- [ ] Forced colours (Windows contrast themes): the switch has a visible boundary and its on/off state is clear without colour.
- [ ] Print or Save as PDF from a dark browser prints the light look without the switch (automated in emulation).
- [ ] Turnstile on the live Contact and BizCheck pages renders in the expected theme in both themes and a submission succeeds. A toggle after the widget has rendered applies on the next render or page load.

## 4. Screen reader spot check

- [ ] With a real screen reader (for example NVDA with Firefox or Chrome, VoiceOver with Safari): landmarks are announced (banner, two labelled navigations, main, footer), headings form a sensible outline, the menu button announces its expanded or collapsed state, and the form error is read aloud.

## 5. Links, images and content

- [ ] Link text makes sense out of context; no "click here" or "read more"; two links with the same name go to the same place.
- [ ] Every informative image has a specific, neutral alternative text; decorative graphics are hidden from assistive technology.
- [ ] Headings do not skip levels; each page has one `<h1>`.
- [ ] Page language is declared; page titles are unique and descriptive.

## 6. Forms (Contact and BizCheck)

- [ ] Every control has a visible label.
- [ ] Submitting with required fields empty or an invalid email: the error is announced (`role="alert"`), names the fields to fix, each field is marked `aria-invalid` and tied to the message, and focus moves to the first problem field (automated).
- [ ] Fixing a field and resubmitting clears its invalid state (automated).
- [ ] The verification (Turnstile) step is reachable and operable by keyboard, and its failure message is announced. Needs the live site; automated tests block third-party scripts.

## 7. Motion

- [ ] With reduced motion requested, no CSS animation runs (automated).
- [ ] Nothing flashes more than three times per second.
