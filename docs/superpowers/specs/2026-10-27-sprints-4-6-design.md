# Sprints 4 to 6: the last six service pages and the 404

Date: 2026-10-27
Branch: `sprints-4-6-finish-rebuild` (off master, with Sprints 1 to 3 live)
Parent design: `2026-10-15-services-restructure-design.md`. This document covers Sprints 4, 5 and 6 together.
Status: the owner asked to continue the rebuild until it is complete. Copy is **drafted by Claude for the owner to
edit**; calls marked *my call* are open to change.

## What ships

1. **Sprint 4, AI Solutions:** `ai-solutions/custom-applications`, `ai-solutions/workflow-automation`,
   `ai-solutions/operational-efficiency`.
2. **Sprint 5, Digital Presence:** `digital-presence/websites`, `digital-presence/digital-marketing`,
   `digital-presence/community-content`.
3. **Sprint 6, the 404:** redesigned around the line "You've found a page that's not ready for Primetime."

With these the site has its twenty pages and the sitemap lists the nineteen indexable ones (the 404 is `noindex`).

## Decisions

- **Same template as Sprint 3.** Each new page is a `services.json` entry flipped to `live` with an `href` and a
  `detail` (tag, paragraph, six deliverables), plus a `site.json` page. No new template or CSS for these pages.
- **Copy** is drafted from the pillar copy the owner already approved in Sprint 2 (the one-line summaries and the
  "start with the problem, not the technology" stance). It describes what each service does and delivers, phrased as
  capabilities. It names no clients, results, numbers or prices. *My call:* the tags are "Build", "Automation" and
  "Diagnosis" for AI Solutions, and the owner's own "Brand presence", "Brand online" and "Brand connect" for Digital
  Presence.
- **404 as a template page** (`"template": "notfound"`): its practice links render from `services.json`, so it cannot
  drift from the practice names.
- **404 paths start at the root.** Cloudflare Pages serves `404.html` for a missing URL at any depth. With relative
  paths, a miss under `/partnerships/` loaded no stylesheet and every link pointed into the wrong folder. The page now
  sets `"root": "/"` in `site.json` (`build.page_root`).
- **404 footer:** the parent design asked this sprint to reconsider the missing footer. *My call:* the 404 now carries
  the shared footer, because its job is to give a lost visitor every route. Reverting is `"footer": false`.
- **404 copy:** keeps the existing eyebrow, the large "404" and the two buttons; the headline becomes the owner's
  Primetime line and the lead sentence gains "or isn't ready yet".

## Constraints (binding, unchanged)

No pricing. No em dashes. No asserted fact the owner has not given. WCAG 2.2 AA in both themes. Never hand-edit a
generated `.html`.

## Not verified in this branch

The Playwright browser suite (`tests/a11y_browser`) could not run in the environment that built this branch, so the
axe gate, pixel contrast and motion checks for the seven changed pages still need a run, and new axe needs-review
entries for them may need adding to `tests/a11y_review.json`. Run `PYTHONUTF8=1 python -m pytest` with Chromium
installed before merging.
