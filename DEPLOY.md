# Deploying

Static files, no build step. Hosted on **Cloudflare Pages** (project
`ayin-advisors`), which deploys automatically from this repo on every push to
`master`.

- Live: https://ayinadvisors.com
- Pages origin: https://ayin-advisors.pages.dev

## Cloudflare Pages settings

| Setting          | Value  |
|------------------|--------|
| Build command    | *(none)* |
| Output directory | `/`    |
| Branch           | `master` |

Cloudflare Pages serves clean URLs automatically: `/BizCheck.html` 308-redirects
to `/BizCheck`. Keep the `.html` files named as they are — the redirect is
handled at the edge, and inbound links to either form work.

## DNS

Managed in Cloudflare. Both records are proxied (orange cloud):

| Type  | Name | Content                  |
|-------|------|--------------------------|
| CNAME | `@`  | `ayin-advisors.pages.dev` |
| CNAME | `www`| `ayinadvisors.com`        |

`www` must also be added as a **custom domain on the Pages project**
(Workers & Pages → ayin-advisors → Custom domains), otherwise Cloudflare
proxies the hostname but no origin is bound to it and it returns a 522.

## BizCheck form

`BizCheck.html` posts to `/api/bizcheck` — a Pages Function that verifies the
Turnstile token server-side before relaying to Formspree. The Formspree URL is
never in the page; it lives in the `FORMSPREE_ENDPOINT` variable.

Required Pages environment variables (Settings → Environment variables →
**Production**, then redeploy — Pages binds them at build time):

| Variable | Value | Type |
|---|---|---|
| `TURNSTILE_SECRET` | Turnstile widget secret | Encrypt |
| `TURNSTILE_HOSTNAMES` | `ayinadvisors.com` | Plaintext |
| `FORMSPREE_ENDPOINT` | the Formspree form URL | Encrypt |

`TURNSTILE_HOSTNAMES` must not include `localhost` in production, or a token
minted locally would be accepted.

Do not enable Formspree's own reCAPTCHA on this form. It only works when a
browser posts directly to Formspree; the Function posts server-to-server, so
Formspree rejects with *"In order to submit via AJAX, you need to set a custom
key or reCAPTCHA must be disabled"*. Turnstile already covers it, and runs
before Formspree is contacted at all.

If the endpoint is ever committed to this public repo, rotate it — history
outlives the file.

## Contact form

`Contact.html` posts to `/api/contact`, hardened identically to BizCheck. It
reuses the same Turnstile widget and the same `TURNSTILE_SECRET` /
`TURNSTILE_HOSTNAMES`, with its own action (`contact`) so the two surfaces stay
distinguishable at siteverify, and its own form:

| Variable | Value | Type |
|---|---|---|
| `CONTACT_FORMSPREE_ENDPOINT` | the contact form's Formspree URL | Encrypt |

Its previous endpoint was public in page source and in this repo's history, so
rotate it rather than reusing it.

## Local preview

```bash
python -m http.server 4173
```

Note: the site must be served over HTTP, not opened as `file://` — relative
asset paths won't resolve otherwise.

## Building

The site is generated: run `python build.py` to render the seven root pages
from `content/site.json`, `templates/` and `templates/pages/`.

- **Never edit a root `.html` file.** Edit `content/site.json`, `templates/` or
  `templates/pages/`, then rebuild and commit the regenerated output.
- `python build.py --check` reports any page that has drifted from its
  templates (`stale: none` and exit 0 when clean, otherwise lists names, exit 1).
- Install tooling with `pip install -r dev-requirements.txt`; run tests with
  `PYTHONUTF8=1 python -m pytest`.
- Templates are named `.j2` and page body fragments `.frag` because Cloudflare
  Pages serves the whole repo root: no `.html` other than the seven real pages
  may be committed (`tests/test_no_stray_html.py` enforces this).
- The dev dependency file is deliberately **not** named `requirements.txt`:
  Cloudflare Pages may auto-run `pip install -r requirements.txt`, and a failure
  there would break the production deploy for a build the deploy does not use.
  The generated `.html` is committed; Cloudflare runs no build.

## Testing

`tests/baseline/*.snap` are frozen snapshots taken before the build system
existed. They are a one-time proof that the generated pages match the pre-build
site, not a permanent contract. After Sprint 1 merges, a sprint that
intentionally changes visible output states an explicit, pinned delta in its own
test (as Sprint 1 did for the footer). Durable protection comes from
baseline-independent invariants: chrome identical across pages, links resolve,
forms/ids/scripts present, accessibility and contrast gates. Baselines are
re-snapshotted from merged output at the start of the next sprint, never edited
to turn a red test green.

## Accessibility gate (development only)

The gate is part of the normal test run; it does not affect the deploy path.

```
pip install -r dev-requirements.txt
python -m playwright install chromium     # browser tests need Chromium
python -m pytest tests                    # includes the gate
python -m pytest tests -m "not browser"   # static checks only, no Chromium
python tools/a11y_ratchet.py              # print current static + axe totals
python tools/a11y_ratchet.py --update     # record a lower total after fixing problems
```

- Tests marked `browser` drive headless Chromium against the repo root served
  on a local port; if Chromium is not installed they skip with the install
  command in the reason.
- The ratchet (`tests/a11y_known_issues.json`) records known problems: the
  suite fails on any new problem and also when a problem is fixed but the
  ratchet was not lowered, so the totals only go down.
- axe "needs review" results must each have a written reason in
  `tests/a11y_review.json`.
- Tests marked `xfail(strict=True)` are known defects with a named fixing task;
  one that starts passing fails the run until the marker is removed.
