"""tools/a11y_ratchet.py must only ever lower the ratchet unless told otherwise (tmp_path only)."""
import json

import pytest

from tools import a11y_ratchet as rt


def _setup(tmp_path, static, axe):
    known, review = tmp_path / "known.json", tmp_path / "review.json"
    known.write_text(json.dumps({"static": static, "axe": axe}), encoding="utf-8")
    review.write_text(json.dumps({"items": []}), encoding="utf-8")
    return known, review


def test_update_lowering_and_removing_is_allowed(tmp_path):
    known, review = _setup(tmp_path, {"a|r": 3, "b|r": 1}, {"a|320|x": 5})
    rt.write_ratchet(known, review, {"a|r": 2}, {}, [])
    assert json.loads(known.read_text()) == {"static": {"a|r": 2}, "axe": {}}


@pytest.mark.parametrize("static,axe", [
    ({"a|r": 4}, {"a|320|x": 5}),          # static raised
    ({"a|r": 3}, {"a|320|x": 6}),          # axe raised
    ({"a|r": 3, "c|new": 1}, {"a|320|x": 5}),  # new key with count > 0
])
def test_update_refuses_to_raise_without_flag(tmp_path, static, axe):
    known, review = _setup(tmp_path, {"a|r": 3}, {"a|320|x": 5})
    before = known.read_text()
    with pytest.raises(SystemExit, match="allow-increase"):
        rt.write_ratchet(known, review, static, axe, [])
    assert known.read_text() == before


def test_allow_increase_permits_a_raise(tmp_path):
    known, review = _setup(tmp_path, {"a|r": 3}, {})
    rt.write_ratchet(known, review, {"a|r": 9}, {}, [], allow_increase=True)
    assert json.loads(known.read_text())["static"] == {"a|r": 9}


def test_review_sync_adds_unreviewed_and_prunes_stale(tmp_path):
    known, review = _setup(tmp_path, {}, {})
    review.write_text(json.dumps({"items": [
        {"page": "p", "rule": "r", "selector": "gone", "status": "justified", "reason": "x"},
        {"page": "p", "rule": "r", "selector": "kept", "status": "justified", "reason": "checked"},
    ]}), encoding="utf-8")
    rt.write_ratchet(known, review, {}, {}, [("p", "r", "kept"), ("p", "r", "new")])
    items = {i["selector"]: i for i in json.loads(review.read_text())["items"]}
    assert set(items) == {"kept", "new"}
    assert items["kept"]["status"] == "justified" and items["new"]["status"] == "unreviewed"
