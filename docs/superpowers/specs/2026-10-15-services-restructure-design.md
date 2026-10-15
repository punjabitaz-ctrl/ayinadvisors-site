# Services restructure — design

Date: 2026-10-15
Branch: `restructure-services` (sprints branch off and merge back individually)
Status: awaiting review

## Purpose

AYiN Advisors becomes a three-practice firm. US market entry stops being the site's
identity and folds into B2B Partnerships as one of three co-equal lines.

The three pillars serve **three distinct buyers**, not one:

| Pillar | Buyer |
|---|---|
| B2B Partnerships | International firms entering the US |
| AI Solutions Development | Anyone needing AI built |
| Digital Presence | Businesses needing web, marketing and community |

Because the buyers differ, the homepage cannot lead with any single one, and each
pillar needs its own entry point and its own call to action.

## Information architecture

Three levels. A card leads to a pillar page, which leads to a page per sub-service.

```
/Services                                    hub — three cards
  /partnerships                              pillar
    /partnerships/market-entry-research
    /partnerships/channel-strategy
    /partnerships/partner-introductions
    /partnerships/regional-expansion
  /ai-solutions                              pillar
    /ai-solutions/custom-applications
    /ai-solutions/workflow-automation
    /ai-solutions/operational-efficiency
  /digital-presence                          pillar
    /digital-presence/websites               brand presence
    /digital-presence/digital-marketing      brand online
    /digital-presence/community-content      brand connect
```

14 pages replace one `Services.html`. With the six existing pages the site goes from
7 to 20.

Existing URLs (`/`, `/About`, `/Projects`, `/BizCheck`, `/Contact`) are unchanged, so
nothing inbound breaks. New paths are lowercase and hyphenated. This leaves `/Services`
sitting beside `/partnerships`; renaming it would break inbound links for a cosmetic
gain, so it stays.

Clean URLs already work at the edge — `partnerships/market-entry-research.html` serves
at the extensionless path, the same way `/BizCheck.html` serves at `/BizCheck`.

## Why a build step

The site has no build. Every page carries its own hand-copied nav and footer. At seven
pages that was tolerable; at twenty it is the dominant maintenance cost.

This is not speculative. Both failures already happened:

- Adding BizCheck to the nav required a scripted sweep across seven files.
- The footers had silently drifted — `index` and `BizCheck` said "Valencia" while the
  other four said "Toronto", with the lead sentence hyphenated differently between the
  two variants. Nobody noticed until a grep found it.

That drift occurred at a third of the target scale.

## Build system

```
content/services.json     the three-level tree — single source of truth
templates/
  base.html               head, nav, footer — the shell every page extends
  hub.html                Services hub          } each supplies only
  pillar.html             a pillar page         } a body block into
  service.html            a sub-service page    } base.html
  pages/<name>.html       body of each existing page, lifted verbatim
build.py                  templates x content -> .html at repo root
```

`base.html` is the only place nav and footer exist. Every other template supplies a
body block into it. The six existing pages keep their current body markup in
`templates/pages/`, unchanged, and gain generated chrome.

**Output is written in place at the repo root and committed.**

Cloudflare keeps doing exactly what it does now: no build command, serve the root. The
alternative — building on deploy — was rejected deliberately. `functions/api/*.js`,
`_headers`, `assets/` and the Turnstile wiring all resolve from the root today, and a
deploy-time build introduces a failure mode where a broken build takes the live site
down. The deploy path does not change.

Cost of that choice: generated HTML lives in git beside its templates. Every generated
file gets a header comment marking it generated and naming the template, so nobody
hand-edits one by mistake.

### Generation covers all 20 pages

If only the 14 service pages generate, nav and footer still drift between them and the
six hand-written pages — the exact failure this is meant to end. So `index`, `About`,
`Projects`, `BizCheck`, `Contact` and `404` also move into the template system.

**Their body content is preserved verbatim.** Only their chrome is generated.

`BizCheck.html` needs care: it carries page-specific `<style>`, the Turnstile loader
with its head latch, and its own inline script. All of that is body/head content, not
chrome, and must survive byte-for-byte.

Sprint 1 implemented the content model as `content/site.json` and the templates as
`templates/*.j2`, with per-page `templates/pages/<stem>.body.frag` + `<stem>.json`. The
non-`.html` extensions are deliberate: Cloudflare serves the repo root, so any `.html`
under `templates/` would be published as a page.

**Baseline policy.** Sprint 1's frozen `tests/baseline/*.snap` are a one-time proof that
the generated pages match the pre-build site. After Sprint 1 merges, a sprint that
intentionally changes visible output states an explicit, pinned delta in its own test (as
Sprint 1 did for the footer); durable protection comes from baseline-independent
invariants (chrome identical across pages, links resolve, forms/ids/scripts present,
accessibility and contrast gates). Baselines are re-snapshotted from merged output at the
start of the next sprint, never edited to turn a red test green.

### Also generated

`sitemap.xml`, from the same content tree — 20 URLs, no longer hand-maintained.

## What does not change

Design system and `assets/styles.css`; both Turnstile Pages Functions and their
environment variables; `_headers` and the enforcing CSP; BizCheck's page
and its gold nav pill; the white consultation buttons; the deploy path; DNS and the
www redirect. `robots.txt` gained `Disallow` lines for `/templates/ /content/ /tests/ /docs/`
in the `*` group (advisory); everything else in it is unchanged.

## Content

B2B Partnerships inherits the four services' existing copy from the live site, which is
already written and good.

The pillar pages and the seven new sub-service pages need copy. Source material is the
owner's shorthand:

- **AI Solutions Development** — solving problems through custom applications, workflow
  automation and operational efficiency.
- **Digital Presence** — websites (brand presence), digital marketing (brand online),
  community and content (brand connect).

Copy for new pages is drafted from that for owner review and edit. Draft copy is a deliverable of each sprint,
not a prerequisite for starting the build system.

**Pricing appears nowhere on the site.** This is a standing constraint, not an
oversight.

## Sprints

Each sprint is a branch off `restructure-services`, merged when complete. **Every merge
must leave the live site coherent** — no sprint may ship a state where the homepage
promises something the site cannot deliver.

**Sprint 1 — Build system, zero visible change.**
Content model, templates, `build.py`. Regenerate the six existing pages. No new pages,
no copy, nothing a visitor can see.

*Done when,* verified against live production rather than assumed:
- Every generated page's **visible DOM is equivalent** to the page it replaces.
  Byte-identical output is not the bar and not achievable — generated files carry a
  header comment and normalised whitespace. The test is that nav links, footer text,
  headings, body copy and asset references all match.
- Both forms still submit and deliver.
- CSP still enforcing with zero violations; no console errors.
- `BizCheck.html` keeps its page `<style>`, Turnstile head latch and inline script
  intact.

**Sprint 2 — Three pillars go live.**
Services hub, three pillar pages, and the homepage repositioning, together. They must
ship as one unit: a hub promising three pillars while the homepage still says "See the
American Business market clearly" would be incoherent. Sub-services are listed on
pillar pages but not yet linked.
*Done when:* nav routes correctly, no dead links, homepage speaks to three buyers.

**Sprint 3 — B2B Partnerships sub-pages.**
Four pages from existing copy; pillar page links activate.

**Sprint 4 — AI Solutions sub-pages.**
Three pages, new copy.

**Sprint 5 — Digital Presence sub-pages.**
Three pages, new copy.

**Sprint 6 — The 404 page.** Last, deliberately.
A redesign in the AYiN visual language, led by the line *"You've found a page that's
not ready for Primetime."* It goes last because a 404's job is to recover a lost
visitor, and it cannot route them anywhere useful until the twenty pages it would route
them to exist. Earlier sprints regenerate `404.html` verbatim, including its currently
missing footer, which this sprint reconsiders.

Sitemap regenerates every sprint automatically.

The implementation plan is written **per sprint**, not once for all five. Sprint 1
carries nearly all the technical risk and none of the copy; the later sprints are
largely the same work repeated with different content, and planning them in detail now
would be guessing at copy that does not exist yet.

## Risks

**A generated file gets hand-edited and the change is lost on next build.** Mitigated by
the header comment on every generated file, and by `build.py` reporting any output that
differs from what it expects to overwrite.

**Sprint 1 silently changes an existing page.** This is the highest risk, because those
pages carry working forms and a CSP that took real effort. Mitigated by diffing rendered
output against current production before merge, rather than trusting the templates.

## Success criteria

- 20 pages live, every sub-service on its own indexable URL
- Nav and footer defined once; changing either touches one file
- Adding a sub-service is a `services.json` edit plus a build
- Both forms still deliver; CSP still enforcing; no console errors
- Existing URLs unchanged; sitemap lists all 20
- No pricing anywhere

## Resolved

1. **Copy** — every pillar and sub-service page is drafted for owner review and edit.
   Not blocking Sprint 1.
2. **`Projects`** — left as is. Not reorganised by pillar in this restructure.
