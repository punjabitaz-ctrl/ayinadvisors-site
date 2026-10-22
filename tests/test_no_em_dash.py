"""Owner rule: no em dash anywhere in the site, hyphen only."""
import subprocess

from conftest import ROOT

EM = "—"
BINARY = (".webp", ".jpg", ".png", ".ico", ".snap")


def test_no_em_dash_in_any_tracked_text_file():
    files = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True).stdout.split("\n")
    bad = []
    for f in files:
        if not f or f.endswith(BINARY) or f == "tests/test_no_em_dash.py" or f.startswith("tests/baseline/"):
            continue
        try:
            text = (ROOT / f).read_text(encoding="utf-8")
        except (UnicodeDecodeError, FileNotFoundError):
            continue
        # tests may mention the character only to assert its absence
        lines = [l for l in text.splitlines() if EM in l and f"{chr(34)}{EM}{chr(34)} not in" not in l]
        if lines:
            bad.append(f)
    assert not bad, f"em dash found in: {bad}"
