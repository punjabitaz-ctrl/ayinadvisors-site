# Sprint 2: Three Pillars Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship the Services hub, three pillar pages and the repositioned homepage as one coherent unit, driven by a `content/services.json` tree, with nav, footer, titles and a generated sitemap updated.

**Architecture:** `content/services.json` defines pillars and sub-services. `build.py` gains template-rendered pages (`"template"` key in `content/site.json` pages) alongside existing fragment pages; a hub template and a pillar template render from the JSON. The sitemap is generated from `site.json`. Existing components (iris icons, ripples, letters band, assemble and tilt motion, tokens, themes) are reused.

**Tech Stack:** Jinja2/build.py, plain CSS and JS, the existing Playwright + axe gate.

**Spec:** `docs/superpowers/specs/2026-10-21-sprint-2-pillars-design.md` (parent: `2026-10-15-services-restructure-design.md`)

## Global Constraints

- `python -m pytest tests -q` passes at the end of every task (about 12 minutes, growing with pages); zero known accessibility issues in both themes for EVERY page including new ones; no ratchet; stale review-entry tests stay honest; colour-literal test passes (no new literals).
- New pages are root pages `partnerships`, `ai-solutions`, `digital-presence`; hub is the existing `Services` page. Canonicals follow the existing convention (`https://ayinadvisors.com/<Stem>.html` style used by current pages: use `https://ayinadvisors.com/partnerships.html` etc.). Page titles keep the em dash. Tagline: "Business Solutions for a Digital World"; Home title "AYiN Advisors — Business Solutions for a Digital World".
- Sub-services are listed but NOT linked (no `href` to non-existent pages); no dead links (a test crawls every internal href/anchor on every page).
- No pricing anywhere; no invented statistics, clients, results or testimonials; copy is drafted from the owner's shorthand and the existing site text; the four existing market-entry services keep their existing copy verbatim.
- Cloudflare serves the repo root: only real pages are tracked `.html`; templates stay `.j2`/`.frag`/`.json`; `tests/test_no_stray_html.py` follows `site.json`. Dev deps only in `dev-requirements.txt`.
- Baseline protocol: declare the delta; `python tools/baseline.py diff`; paste output; `python tools/baseline.py snapshot` (snapshots for new pages are created, existing pages' deltas are declared per task). Never snapshot to turn an unexplained red test green. `PYTHONUTF8=1`, `python -m pytest`, one command at a time; tests never write to the real tree. Work only on branch `sprint-2-pillars`; never push.
- Docs are published: no personal info, no local paths, no internal process detail.

## Review Focus

1. **Dead links and anchors** after moving the four services and the why-US band: a test crawling all internal hrefs and fragment ids on every page (T1, enforced in T2 to T4).
2. **Stale claims**: Home or meta text still saying "US market entry" as the whole identity, or the nav/footer "Practice" column still pointing at `Services.html#research` (T3).
3. **Copy that asserts invented facts** (numbers, clients, results). A test blocks digits in AI and Digital pillar copy except the step ordinals, and reviewers must read the copy (T2, T3).
4. **New pages missing from the gate matrix**: `tests/a11y_browser` parametrisation derives from `build.PAGES`; a test asserts every `site.json` page appears in the axe, pixel and 320px matrices (T1).
5. **Sitemap drift**: generated sitemap equals what `--check` expects and lists exactly the `site.json` pages with canonical URLs (T1).

## File Structure

| File | Responsibility |
|---|---|
| `content/services.json` | Pillars and sub-services: slug, name, summary, status, icon id |
| `content/site.json` | Pages (adds 3, `template` key, sitemap priority), nav, footer |
| `templates/hub.body.j2`, `templates/pillar.body.j2` | Hub and pillar bodies rendered from the JSON |
| `templates/pages/*.body.frag` | Existing pages; `Services` fragment retired in favour of the hub template; four-service detail moves into partnerships |
| `build.py` | Template pages, sitemap generation, `--check` coverage |
| `tests/test_links.py`, `tests/test_services_content.py`, `tests/test_sitemap.py` | Dead links, content rules, sitemap |
| `docs/accessibility/2026-10-s2-review.md` | Dated review |

---

### Task 1: Content model, template pages, sitemap, test net

**Files:** Create `content/services.json`, `templates/hub.body.j2`, `templates/pillar.body.j2`, `tests/test_links.py`, `tests/test_services_content.py`, `tests/test_sitemap.py`; Modify `build.py`, `content/site.json`, `tests/test_no_stray_html.py`, `tests/conftest.py` (sandbox must copy new inputs), `sitemap.xml` (generated)

**Interfaces:** Produces `content/services.json` shape `{"pillars":[{"slug","stem","name","tagline","buyer","summary","icon","services":[{"slug","name","summary","status":"planned|live","href"?}]}]}`; `site.json` pages gain optional `"template": "hub"|"pillar"` and `"pillar": "<slug>"`, and `"sitemap": {"priority": "0.8"}`; `build.render_all()` renders template pages; `build.render_sitemap() -> str`; `check()` also covers the sitemap. Consumed by T2 to T4.

- [ ] **Step 1: Tests first (RED).** `test_services_json_shape` (3 pillars, slugs/stems unique, every service has name+summary, status only `planned|live`, no `href` unless `live`); `test_every_site_page_is_in_the_gate_matrix` (Review Focus 4); `test_sitemap_matches_site_json` (exact URL list with canonicals and priorities, valid XML); `test_sitemap_is_fresh` via `build.check()`; `test_no_dead_internal_links_or_anchors` (crawl generated root pages; resolve hrefs to generated pages/assets and `#fragment` ids) ; `test_no_pricing_words` (regex for `$`, "price", "pricing", "per month", "/mo" on pillar/hub/Home text excluding the stats `$24T`); `test_no_invented_digits_in_new_pillar_copy`.
- [ ] **Step 2:** Implement `content/services.json` with the three pillars and ten sub-services in `planned` status, with draft names/summaries per the parent design (B2B: market-entry-research, channel-strategy, partner-introductions, regional-expansion with the existing names and one-line summaries from the current site; AI: custom applications, workflow automation, operational efficiency; Digital: websites (brand presence), digital marketing (brand online), community and content (brand connect)).
- [ ] **Step 3:** Extend `build.py` for template pages, add the three pages and sitemap priorities to `site.json`, generate `sitemap.xml`, extend `check()`. Create minimal valid `hub.body.j2` and `pillar.body.j2` shells (full copy in T2) that render the hero/page-head, one band listing the pillar's services unlinked, and the CTA, using existing components, so the gate and link tests have real pages. Update sandbox/conftest and the stray-html test to derive from `site.json`.
- [ ] **Step 4:** Regenerate. **Declared delta:** `Services` page body (hub shell replaces the old detail — the old four-service markup is preserved in git and moved in T2; to keep T1 green, keep it present on the partnerships shell verbatim in this task), new snapshots for three pages, nav/footer facts unchanged. Diff, confirm, snapshot, full suite.
- [ ] **Step 5:** Commit.

---

### Task 2: Hub and pillar pages with drafted copy

**Files:** Modify `templates/hub.body.j2`, `templates/pillar.body.j2`, `content/services.json`, `content/site.json` (titles/descriptions), `assets/styles.css`, page `.json` head CSS if needed; Create per-pillar copy in `content/services.json` (headline, lead, intro paragraphs, "who it is for", "how we work", sub-service blurbs), the partnerships proof band fragment (moved Why-US band: wireframe globe, photograph, stats) `templates/partials/partnerships-proof.frag`

**Interfaces:** Consumes T1. Produces final hub and pillar pages. Sub-services are rendered as non-link cards marked "coming soon" is NOT allowed (no "coming soon" copy); render them as informative cards without arrows or links.

- [ ] **Step 1: Tests first (RED).** `test_hub_lists_three_pillars_linking_to_their_pages`; `test_each_pillar_lists_its_services_unlinked` (service names present, no anchor to non-existent pages); `test_partnerships_keeps_the_four_services_verbatim` (the four existing detail blocks' text equals the text at the base commit — snapshot the strings in a fixture file under `tests/fixtures/`), `test_partnerships_has_the_us_proof_band` (globe, stats `$24T`, `50`, `70%`, `3x`), `test_pillar_pages_have_one_h1_and_expected_headings` (static lint passes), plus the Phase 2 component tests for any new `assemble` use (at-rest alignment, transient depth, ripples clear of text with their own geometry tests).
- [ ] **Step 2:** Write the hub (hero in page-head style, three large pillar cards each with its iris icon, the buyer sentence, three bullet service names, and a "Explore" link to the pillar page) and the pillar template (page-head with eyebrow naming the buyer, intro, "what we do" sub-service cards (unlinked), "how we work" generic process, "who it is for", CTA band). Draft the copy for all three pillars per the spec decisions; Partnerships additionally includes the verbatim four-service detail and the moved Why-US proof band.
- [ ] **Step 3:** Rhythm: bands alternate page/alt with the gold CTA last; cards use the card surface; photographs as in Phase 2a (us-night moves with the proof band to Partnerships). Both themes.
- [ ] **Step 4:** Regenerate. **Declared delta:** Services (hub), the three pillar pages, nothing else. Diff, confirm, snapshot, full suite (both themes), screenshots of the four pages at 1280 and 375 in both themes, looked at.
- [ ] **Step 5:** Commit.

---

### Task 3: Homepage repositioning, nav, footer, titles

**Files:** Modify `templates/pages/index.body.frag`, `templates/pages/index.json`, `content/site.json` (Home title/description/tagline, About description, footer columns/tagline/strapline), `content/services.json` as needed, `assets/styles.css`

**Interfaces:** Consumes T1 and T2.

- [ ] **Step 1: Tests first (RED).** `test_home_title_and_description_use_the_tagline`; `test_home_has_three_pillar_cards_linking_to_pillar_pages`; `test_home_no_longer_leads_with_us_only` (hero h1 does not contain "American"; US-only band removed from Home); `test_footer_practice_column_lists_pillars_and_services_unlinked_or_pillar_links` (no `Services.html#research`-style anchors remain anywhere in generated pages); `test_nav_still_routes` (all nav hrefs resolve); `test_about_description_not_us_only`.
- [ ] **Step 2:** Rewrite Home: hero (h1 "Business solutions for a digital world." with the italic accent on "digital world.", eyebrow "AYiN Advisors", lead naming the three practices, the existing two CTAs); stats per the spec decisions; keep the letters band; "What we do" becomes three pillar cards (iris icons, link to the pillar pages); generic "How we work" process (Diagnose, Design, Deliver, Enable) with the existing component; the Why-US band is removed from Home (moved in T2) and replaced by a "Who we work with" band showing the three buyers; keep "Who we are" and the CTA (CTA lead reworded to be practice-neutral). Update footer: tagline, strapline ("Business solutions for a digital world."), "Practice" column to the three pillars (linked) with their services listed unlinked beneath or as plain text, per what keeps the chrome identical across pages.
- [ ] **Step 3:** Regenerate. **Declared delta:** Home body/head, all pages' footer subtree (chrome stays identical across pages: update the chrome invariant honestly), titles/descriptions in `site.json` for Home and About. Diff, confirm, snapshot, full suite.
- [ ] **Step 4:** Screenshots of Home at 1280 and 375 in both themes, settled and mid-assemble; look at them.
- [ ] **Step 5:** Commit.

---

### Task 4: Gate, polish, review doc

**Files:** Modify tests and `tests/a11y_review.json` as needed, `assets/styles.css`; Create `docs/accessibility/2026-10-s2-review.md`; Modify `DEPLOY.md`, `docs/accessibility/checklist.md`

- [ ] **Step 1:** Run the full gate in both themes on all eleven pages; fix every real failure at the source (no blanket review entries; stable selectors; specific reasons verified by the pixel test); at-rest alignment, grid lines, 320px scroll, forced colours and print for the new pages.
- [ ] **Step 2:** Verify the owner-facing pieces: a crawl proving no dead links, a read-through of all new copy against the "no invented facts, no pricing" rule (report any sentence that makes a factual claim so the owner can confirm), and the forms untouched.
- [ ] **Step 3:** Write the dated review doc (what was tested, what is drafted copy awaiting owner edit, what a human must check) and update DEPLOY.md (sitemap generation, `services.json`, how Sprints 3 to 5 add pages) and the checklist.
- [ ] **Step 4:** Full suite twice, `python build.py --check` stale: none, clean tree; screenshots of all new/changed pages in both themes at both widths, looked at.
- [ ] **Step 5:** Commit.

---

## Self-review notes

- Spec coverage: hub, pillars, Home repositioning, nav/footer/titles/sitemap, listed-not-linked sub-services, no pricing, tagline, gate (T1 to T4).
- Moved, not deleted: the four services (to Partnerships) and the Why-US band (to Partnerships).
- Open for the owner: tagline dash, drafted copy, hero stats wording, old `Services.html#...` deep links now land on the hub.
