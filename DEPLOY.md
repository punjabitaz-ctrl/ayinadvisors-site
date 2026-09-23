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

## Contact form — not yet hardened

`Contact.html` still posts **directly from the browser to Formspree**, with its
endpoint visible in page source. That is the same weakness BizCheck had before
the Function: anyone can read the URL and POST to it, skipping every
client-side check. Route it through a Function the same way when convenient.

## Local preview

```bash
python -m http.server 4173
```

Note: the site must be served over HTTP, not opened as `file://` — relative
asset paths won't resolve otherwise.
