import shutil
from pathlib import Path

import pytest

from conftest import ROOT, PAGES
from tools import baseline


@pytest.fixture
def tree(tmp_path):
    """Isolated copy of the generated root pages and their snapshots."""
    for s in PAGES:
        shutil.copy(ROOT / f"{s}.html", tmp_path / f"{s}.html")
    shutil.copytree(ROOT / "tests" / "baseline", tmp_path / "tests" / "baseline")
    return tmp_path


def test_diff_is_empty_when_pages_equal_snapshots():
    assert baseline.diff() == {}


def test_diff_names_the_changed_key(tree):
    p = tree / "About.html"
    p.write_text(p.read_text(encoding="utf-8").replace("<title>", "<title>Changed ", 1), encoding="utf-8")
    assert baseline.diff(tree) == {"About": ["title"]}


def test_snapshot_overwrites_only_the_snapshot_files(tree):
    p = tree / "About.html"
    p.write_text(p.read_text(encoding="utf-8").replace("<title>", "<title>Changed ", 1), encoding="utf-8")
    pages_before = {s: (tree / f"{s}.html").read_bytes() for s in PAGES}
    real_before = (ROOT / "tests" / "baseline" / "About.snap").read_bytes()
    baseline.snapshot(tree)
    assert baseline.diff(tree) == {}
    assert (tree / "tests" / "baseline" / "About.snap").read_bytes() == p.read_bytes()
    assert {s: (tree / f"{s}.html").read_bytes() for s in PAGES} == pages_before
    assert sorted(x.name for x in (tree / "tests" / "baseline").iterdir()) == sorted(f"{s}.snap" for s in PAGES)
    assert (ROOT / "tests" / "baseline" / "About.snap").read_bytes() == real_before
