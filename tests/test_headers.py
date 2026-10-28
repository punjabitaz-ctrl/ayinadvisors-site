"""_headers: every page, at the extensionless address Cloudflare serves it from, revalidates on each visit."""
import fnmatch

import build
from conftest import ROOT

REVALIDATE = "Cache-Control: public, max-age=0, must-revalidate"


def _rules() -> dict[str, list[str]]:
    rules, current = {}, None
    for line in (ROOT / "_headers").read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if not line[0].isspace():
            current = line.strip()
            rules[current] = []
        else:
            rules[current].append(line.strip())
    return rules


def _covered(path: str, rules: dict[str, list[str]]) -> bool:
    return any(fnmatch.fnmatchcase(path, pat) and REVALIDATE in hdrs for pat, hdrs in rules.items() if pat != "/*")


def test_every_page_address_revalidates():
    rules = _rules()
    for stem, page in build.load_site()["pages"].items():
        if "canonical" not in page:
            continue
        path = page["canonical"].removeprefix(build.SITE_URL) or "/"
        assert _covered(path, rules), f"{stem}: {path} has no revalidate rule in _headers"


def test_page_rules_never_reach_the_assets():
    """Cloudflare joins the Cache-Control values of every rule that matches, so no page rule may match /assets/."""
    rules = _rules()
    for pat, hdrs in rules.items():
        if REVALIDATE in hdrs:
            assert not fnmatch.fnmatchcase("/assets/styles.css", pat), pat
