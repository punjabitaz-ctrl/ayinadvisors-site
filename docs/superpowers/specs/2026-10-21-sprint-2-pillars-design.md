# Sprint 2: three pillars go live

Date: 2026-10-21
Branch: `sprint-2-pillars` (off master, with Phases 2a to 2c live)
Parent design: `2026-10-15-services-restructure-design.md` (information architecture, sprint definitions, "no pricing anywhere"). This document is Sprint 2 only.
Status: the owner said "continue sprint 2". Copy is **drafted by Claude for the owner to edit**; calls marked *my call* are open to change.

## What ships (one unit, per the parent design)

1. **Services hub** (the existing `Services` page, rewritten): three pillar cards.
2. **Three pillar pages**: `partnerships`, `ai-solutions`, `digital-presence` (root pages, so clean URLs `/partnerships`, `/ai-solutions`, `/digital-presence`).
3. **Homepage repositioning** to speak to three buyers, with the new tagline.
4. Nav, footer, titles, descriptions, sitemap updated to match. Sub-services are **listed** on pillar pages but **not linked** (their pages arrive in Sprints 3 to 5).

Done when: nav routes correctly, no dead links, the homepage speaks to three buyers, the whole accessibility gate passes in both themes, no pricing anywhere.

## Decisions

- **Content source of truth:** `content/services.json` holds the three pillars and their sub-services (slug, name, one-line summary, status). Hub, pillar pages, Home cards and footer render from it, so Sprints 3 to 5 only flip a status and add a page. *My call:* pillar and hub bodies are generated from Jinja templates fed by this file, not hand-written fragments.
- **Tagline:** "Business Solutions for a Digital World". Page title for Home: "AYiN Advisors — Business Solutions for a Digital World" (*my call:* the em dash, because page titles keep the em dash site-wide; the owner typed a hyphen, so please confirm).
- **The four existing market-entry services keep their full existing copy** and move, verbatim, onto the Partnerships pillar page below the pillar introduction (their anchors `#research`, `#channel`, `#introductions`, `#expansion` stay valid on the new page). Old links to `Services.html#research` and friends will land on the hub; *my call:* accepted, because the site is new enough that few inbound links exist, and Sprint 3 gives each its own page.
- **US-specific Home sections move to the Partnerships page**: the "Why the US market" band (wireframe globe, photograph, the four stats) becomes the Partnerships pillar's proof band. Nothing is deleted. The Home process section becomes a generic engagement process.
- **Home hero stats:** only claims the site already made are kept; no new numbers are invented. *My call:* "3 practices", the existing "90 days to a first qualified partner" scoped to the Partnerships practice, and "100% channel-led, founder-aligned" reworded as the founder-led working style. The owner should review.
- **Copy for the AI Solutions and Digital Presence pillars** is drafted from the owner's shorthand: AI Solutions solves problems through custom applications, workflow automation and operational efficiency; Digital Presence covers websites (brand presence), digital marketing (brand online) and community and content (brand connect). Plain, concrete, no hype, no pricing, no invented client claims, no invented statistics.
- **Visual system:** reuse Phase 2a to 2c components (iris markers and icons, ripples, letters band, assemble and tilt motion, tokens, both themes). The three pillars get distinct iris icons. No new colour literals.
- **Sitemap** is generated from `content/site.json` by `build.py` (the parent design asked for this) and checked by `--check`; priority per page defined in `site.json`.
- **404, About, Projects, BizCheck, Contact bodies** are not rewritten in this sprint. Their titles and descriptions only change where they now mislead (About's description); nav and footer are shared.

## Non-goals

- Sub-service pages (Sprints 3 to 5), the 404 redesign (Sprint 6), the Projects page, pricing, new photography beyond reusing the existing four images.

## Constraints (binding)

- WCAG 2.2 AA in both themes at zero known issues; the gate covers every new page.
- No copy change that asserts a fact not already on the site or given by the owner. Placeholders are phrased as capabilities, not results.
- Cloudflare serves the repo root: new pages are generated root `.html` files and the "only real pages are tracked HTML" test is updated from `site.json`; templates stay `.j2` and `.frag`.
- No pricing. No personal info in docs. Page titles keep the em dash.
