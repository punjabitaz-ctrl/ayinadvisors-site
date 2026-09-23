# Deploying

The site is plain static files — no build step. GitHub Actions publishes the
repo root to GitHub Pages on every push to `master`
(`.github/workflows/deploy-pages.yml`).

## Preview URL

https://punjabitaz-ctrl.github.io/ayinadvisors-site/

## Cutting over ayinadvisors.com to GitHub Pages

The domain currently serves the previous host. Do this only once you've
checked the preview URL above.

1. Re-enable the custom domain in this repo:

   ```bash
   git mv CNAME.disabled CNAME
   git commit -m "Point Pages at ayinadvisors.com"
   git push
   ```

2. Point DNS at GitHub Pages:

   | Type  | Name  | Value                          |
   |-------|-------|--------------------------------|
   | A     | @     | 185.199.108.153                |
   | A     | @     | 185.199.109.153                |
   | A     | @     | 185.199.110.153                |
   | A     | @     | 185.199.111.153                |
   | CNAME | www   | punjabitaz-ctrl.github.io      |

   Remove the records pointing at the old host.

3. In repo Settings → Pages, wait for the certificate, then tick
   **Enforce HTTPS**.

`CNAME` stays disabled until step 1, so the preview URL keeps working and the
live site is untouched.

## Contact form

`BizCheck.html` posts to Formspree. Set the endpoint near the bottom of the
file:

```js
var BIZCHECK_ENDPOINT = "https://formspree.io/f/your-form-id";
```

Create a free form at https://formspree.io pointing at hello@ayinadvisors.com
and paste its ID. Until then, submitting opens the visitor's mail client with
the brief pre-filled.

## Local preview

```bash
python -m http.server 4173
```
