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

## Contact form

`BizCheck.html` posts to Formspree (`https://formspree.io/f/xrpbkony`) via
`fetch` with `Accept: application/json`, and swaps the form for a success panel
on `{"ok":true}`. The honeypot posts as `_gotcha` so Formspree's own spam filter
sees it. If the POST fails, the error surfaces hello@ayinadvisors.com so nobody
is left without somewhere to send the brief.

## Local preview

```bash
python -m http.server 4173
```

Note: the site must be served over HTTP, not opened as `file://` — relative
asset paths won't resolve otherwise.
