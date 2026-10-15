import subprocess

from conftest import ROOT, PAGES


def test_only_the_seven_real_pages_are_tracked_html():
    out = subprocess.run(
        ["git", "ls-files", "*.html"], cwd=ROOT, capture_output=True,
        text=True, encoding="utf-8", check=True,
    ).stdout.split()
    assert set(out) == {f"{s}.html" for s in PAGES}, sorted(set(out) - {f"{s}.html" for s in PAGES})
