"""axe-core over every page at three widths: zero violations, and every "needs review" result justified."""
import json

import pytest

from a11y_browser.conftest import PAGES, ROOT, WIDTHS

pytestmark = pytest.mark.browser

REVIEW = ROOT / "tests" / "a11y_review.json"
CASES = [(s, w) for s in PAGES for w in WIDTHS]
IDS = [f"{s}-{w}" for s, w in CASES]


@pytest.mark.parametrize("stem,width", CASES, ids=IDS)
def test_axe_reports_no_violations(axe_cache, stem, width):
    found = {v.rule: (v.nodes, v.selectors[:5]) for v in axe_cache(stem, width)[0]}
    assert not found, f"{stem}@{width}: axe violations (rule: (nodes, first selectors)): {found}"


# Any entry still marked "unreviewed" fails the suite: a needs-review item is either fixed or justified.
MAX_UNREVIEWED = 0


def _entries() -> list:
    return json.loads(REVIEW.read_text(encoding="utf-8"))["items"]


def _covers(e, page, rule, selector) -> bool:
    return e["page"] == page and e["rule"] == rule and e["selector"] in ("*", selector)


def test_review_entries_are_well_formed():
    bad = []
    for e in _entries():
        if e.get("status") not in ("unreviewed", "justified"):
            bad.append((e.get("page"), e.get("rule"), "status must be 'unreviewed' or 'justified'"))
        elif e["status"] == "justified" and len(e.get("reason", "").strip()) < 40:
            bad.append((e["page"], e["rule"], "justified entry needs a specific reason"))
        elif e["status"] == "justified" and e["rule"] == "color-contrast" and "test_review_contrast" not in e["reason"]:
            bad.append((e["page"], e["rule"], "a colour-contrast justification must cite the pixel measurement test"))
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
        "Fix the cause, or add an entry with status 'justified' and a specific, verified reason."
    )


def test_no_unreviewed_needs_review_entries():
    unreviewed = [e for e in _entries() if e.get("status") == "unreviewed"]
    msg = f"{len(unreviewed)} needs-review entries are still 'unreviewed' (set status 'justified' with a reason)"
    print(msg)
    assert len(unreviewed) <= MAX_UNREVIEWED, msg


def test_no_stale_review_entries(axe_cache):
    """An entry matching no current needs-review result must be removed (the tool's --update prunes them)."""
    seen = [(stem, r.rule, sel) for stem, w in CASES for r in axe_cache(stem, w)[1] for sel in r.selectors]
    stale = [
        (e["page"], e["rule"], e["selector"])
        for e in _entries()
        if not any(_covers(e, p, ru, sel) for p, ru, sel in seen)
    ]
    assert not stale, f"stale tests/a11y_review.json entries (delete them): {stale}"
