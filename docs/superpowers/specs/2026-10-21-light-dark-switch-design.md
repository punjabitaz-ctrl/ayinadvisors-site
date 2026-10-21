# Phase 2c: light and dark switch

Date: 2026-10-21
Branch: `phase-2c-theme-switch` (off Phase 2b, which is live)
Status: scope approved in the Phase 2 spec ("respects the system preference, persists the choice, no flash, labelled button with `aria-pressed`"); the owner said "continue" to start. Calls marked *my call* are the builder's and are open to the owner.

## Why

The site is light-led since Phase 2a, with navy on the hero, nav and footer. The owner asked for a switch so visitors can choose a light or a dark look. Phase 2a already generates and contrast-tests a complete dark token set, and no component uses a colour literal, so this is a mechanism plus a thorough dark-mode audit, not a rewrite.

## Decisions

1. **Default follows the system.** First visit: use `prefers-color-scheme`. If the visitor has never chosen, the page follows the system, including live changes. *My call:* with no system preference signal, light.
2. **The choice persists** in `localStorage` (key `ayin-theme`, values `light` or `dark`), read inside `try/catch`; if storage is blocked the toggle still works for the visit and the site falls back to the system preference next time.
3. **No flash of the wrong theme.** A tiny inline script in `<head>`, before the stylesheet, sets `data-theme` on `<html>` from storage or the system preference. The CSP already permits inline scripts.
4. **Works without JavaScript.** `theme.css` also carries `@media (prefers-color-scheme: dark)` rules scoped to `:root:not([data-theme])`, so a visitor with a dark system and no scripts still gets dark. The toggle button is hidden when scripts do not run.
5. **The control** is a button in the nav (and in the mobile drawer), labelled for assistive tech with a stable name ("Dark mode") and `aria-pressed` reflecting the state, with a visible sun/moon icon (decorative, `aria-hidden`), at least 44px high on touch, two-tone focus ring from the existing system. *My call:* a stable label plus `aria-pressed`, as the Phase 2 spec says, not a changing label.
6. **`color-scheme`** is set per theme so native controls, scrollbars and form widgets match. `<meta name="theme-color">` follows the active theme.
7. **Dark appearance.** The navy hero, nav, drawer and footer stay navy in both themes. In dark mode the page and alternate bands become two dark surfaces from the existing dark token set, cards one step lighter, and the closing call-to-action band stays gold with navy text (it is the one accent surface in both). *My call:* photographs get a slight dim in dark mode (brightness about 0.9) so they do not glare, applied by CSS only.
8. **Everything that held a fixed colour moves to the theme:** the logo mark and wordmark, the iris and BizCheck canvases in `site.js` (read their colours from CSS variables and redraw on theme change), the select arrow in forms, the Turnstile widget theme (follows the active theme where Cloudflare allows it; otherwise it is left on `auto`), and the letters band, iris icons and ripples (already roles-based; verified).
9. **The accessibility gate runs in both themes.** axe at 320/768/1280 and the pixel-contrast test run for light and for dark; static lint, rhythm and the form-control boundary contrast test run in both; the colour-literal test still applies.

## Non-goals

- No third theme, no per-section themes, no auto-switch by time of day.
- No change to copy, links, forms, the Turnstile server verification, or the CSP.
- No pause control for infinite animations (Phase 3).
- No forced-colours redesign beyond keeping it working.

## Accessibility constraints (binding)

- WCAG 2.2 AA in both themes, same gate, zero known issues.
- The toggle is operable by keyboard and touch, announces its state, and does not move focus when activated.
- Switching never reflows layout and never hides content; transition between themes is instant (no animated colour fades) under reduced motion, and short (at most 200 ms, colours only) otherwise. *My call.*
- The visitor's choice is never overridden by the system after they have chosen.

## Out of scope / later

Services restructure (Sprints 2 to 6), Phase 3 accessibility statement and pause controls.
