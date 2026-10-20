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


# Task 7: set to 0 so that any unreviewed needs-review entry fails the suite.
MAX_UNREVIEWED = None


def _entries() -> list:
    return json.loads(REVIEW.read_text(encoding="utf-8"))["items"]


def _covers(e, page, rule, selector) -> bool:
    return e["page"] == page and e["rule"] == rule and e["selector"] in ("*", selector)


def test_review_entries_are_well_formed():
    bad = []
    for e in _entries():
        if e.get("status") not in ("unreviewed", "justified"):
            bad.append((e.get("page"), e.get("rule"), "status must be 'unreviewed' or 'justified'"))
        elif e["status"] == "justified" and not e.get("reason", "").strip():
            bad.append((e["page"], e["rule"], "justified entry needs a real reason"))
    assert not bad, f"malformed tests/a11y_review.json entries: {bad}"


@pytest.mark.parametrize("stem,width", CASES, ids=IDS)
def test_every_needs_review_item_is_justified(axe_cache, stem, width):
    entries = _entries()
    missing = [
        (stem, r.rule, sel)
        for r in axe_cache(stem, width)[1]
        for sel in r.selectors
        if not any(_covers(e, stem, r.rule, sel) for e in entries)
    ]
    assert not missing, (
        f"axe 'needs review' results with no entry in tests/a11y_review.json: {missing}. "
        "Run `python tools/a11y_ratchet.py --update` to record them as 'unreviewed', then review by hand."
    )


def test_unreviewed_needs_review_count_is_reported(axe_cache):
    unreviewed = [e for e in _entries() if e.get("status") == "unreviewed"]
    msg = f"{len(unreviewed)} needs-review entries are still 'unreviewed' (set status 'justified' with a reason)"
    print(msg)
    if MAX_UNREVIEWED is not None:
        assert len(unreviewed) <= MAX_UNREVIEWED, msg


def test_no_stale_review_entries(axe_cache):
    """An entry matching no current needs-review result must be removed (the tool's --update prunes them)."""
    seen = [(stem, r.rule, sel) for stem, w in CASES for r in axe_cache(stem, w)[1] for sel in r.selectors]
    stale = [
        (e["page"], e["rule"], e["selector"])
        for e in _entries()
        if not any(_covers(e, p, ru, sel) for p, ru, sel in seen)
    ]
    assert not stale, f"stale tests/a11y_review.json entries (run `python tools/a11y_ratchet.py --update`): {stale}"
