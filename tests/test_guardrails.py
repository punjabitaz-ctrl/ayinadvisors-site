import subprocess

import build
from conftest import ROOT, PAGES


def _read(base, stem):
    return (base / f"{stem}.html").read_text(encoding="utf-8")


def test_build_is_idempotent(sandbox):
    build.main()
    first = {s: (sandbox / f"{s}.html").read_bytes() for s in PAGES}
    build.main()
    for s in PAGES:
        assert (sandbox / f"{s}.html").read_bytes() == first[s], s


def test_every_generated_file_is_marked():
    for s in PAGES:
        assert _read(ROOT, s).startswith("<!-- GENERATED"), s


def test_check_clean_sandbox_reports_nothing(sandbox):
    assert build.check() == []


def test_check_mode_detects_hand_edits(sandbox):
    target = sandbox / "About.html"
    target.write_text(target.read_text(encoding="utf-8") + "\n<!-- hand edit -->", encoding="utf-8")
    assert build.check() == ["About.html"]


def test_no_requirements_txt_at_repo_root():
    tracked = subprocess.run(
        ["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, encoding="utf-8", check=True
    ).stdout.splitlines()
    assert "requirements.txt" not in tracked
    assert "dev-requirements.txt" in tracked or (ROOT / "dev-requirements.txt").exists()


def test_check_reports_a_deleted_page_as_stale(sandbox):
    (sandbox / "Contact.html").unlink()
    assert build.check() == ["Contact.html"]
