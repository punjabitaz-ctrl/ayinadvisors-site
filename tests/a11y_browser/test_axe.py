"""axe-core over every page at three widths, ratcheted against tests/a11y_known_issues.json."""
import json

import pytest

from a11y_browser.conftest import PAGES, ROOT, WIDTHS

pytestmark = pytest.mark.browser

KNOWN = ROOT / "tests" / "a11y_known_issues.json"
REVIEW = ROOT / "tests" / "a11y_review.json"
CASES = [(s, w) for s in PAGES for w in WIDTHS]
IDS = [f"{s}-{w}" for s, w in CASES]


def _known_axe() -> dict:
    return json.loads(KNOWN.read_text(encoding="utf-8")).get("axe", {})


def _counts(stem, width, violations) -> dict:
    return {f"{stem}|{width}|{v.rule}": v.nodes for v in violations}


@pytest.mark.parametrize("stem,width", CASES, ids=IDS)
def test_axe_has_no_new_violations(axe_cache, stem, width):
    known = _known_axe()
    now = _counts(stem, width, axe_cache(stem, width)[0])
    worse = {k: (known.get(k, 0), n) for k, n in now.items() if n > known.get(k, 0)}
    assert not worse, f"new axe violations (recorded, now): {worse}"


@pytest.mark.parametrize("stem,width", CASES, ids=IDS)
def test_axe_ratchet_is_tight(axe_cache, stem, width):
    known = _known_axe()
    now = _counts(stem, width, axe_cache(stem, width)[0])
    prefix = f"{stem}|{width}|"
    better = {k: (n, now.get(k, 0)) for k, n in known.items() if k.startswith(prefix) and now.get(k, 0) < n}
    assert not better, (
        f"axe violations fixed but ratchet not lowered (recorded, now): {better}. "
        "Run `python tools/a11y_ratchet.py --update` and commit tests/a11y_known_issues.json."
    )


def _justified(entries, page, rule, selector) -> bool:
    return any(
        e["page"] == page and e["rule"] == rule and e["selector"] in ("*", selector) and e.get("reason", "").strip()
        for e in entries
    )


@pytest.mark.parametrize("stem,width", CASES, ids=IDS)
def test_every_needs_review_item_is_justified(axe_cache, stem, width):
    entries = json.loads(REVIEW.read_text(encoding="utf-8"))["items"]
    missing = [
        (stem, r.rule, sel)
        for r in axe_cache(stem, width)[1]
        for sel in r.selectors
        if not _justified(entries, stem, r.rule, sel)
    ]
    assert not missing, (
        f"axe 'needs review' results with no justification in tests/a11y_review.json: {missing}"
    )
