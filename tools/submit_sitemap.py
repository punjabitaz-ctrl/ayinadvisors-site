"""Submit https://ayinadvisors.com/sitemap.xml to Google Search Console (Search Console API, sitemaps.submit).

Google retired its anonymous sitemap "ping" in 2023; the API is the supported way to tell it a sitemap changed. It
needs a Google Cloud service account added as an Owner of the Search Console property:

    GSC_SERVICE_ACCOUNT_JSON  the service account's JSON key (a GitHub Actions secret)
    GSC_SITE                  the property, default "sc-domain:ayinadvisors.com" (use "https://ayinadvisors.com/"
                              for a URL-prefix property)

Run by .github/workflows/publish-scheduled-posts.yml after a post goes live.
"""
import json
import os
import sys
from urllib.parse import quote

SITEMAP = "https://ayinadvisors.com/sitemap.xml"
SCOPE = "https://www.googleapis.com/auth/webmasters"


def submit_url(site: str, sitemap: str = SITEMAP) -> str:
    return (f"https://www.googleapis.com/webmasters/v3/sites/{quote(site, safe='')}"
            f"/sitemaps/{quote(sitemap, safe='')}")


def main() -> int:
    key = os.environ.get("GSC_SERVICE_ACCOUNT_JSON", "").strip()
    if not key:
        print("GSC_SERVICE_ACCOUNT_JSON is not set; skipping the Search Console submission.")
        return 0
    from google.auth.transport.requests import AuthorizedSession
    from google.oauth2 import service_account

    site = os.environ.get("GSC_SITE", "").strip() or "sc-domain:ayinadvisors.com"
    creds = service_account.Credentials.from_service_account_info(json.loads(key), scopes=[SCOPE])
    response = AuthorizedSession(creds).put(submit_url(site), timeout=30)
    if response.status_code >= 300:
        print(f"Search Console refused the sitemap ({response.status_code}): {response.text[:500]}")
        return 1
    print(f"Submitted {SITEMAP} to {site}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
