from pathlib import Path
import shutil
import pytest
from build import PAGES  # noqa: F401  (re-exported for tests)

ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="session")
def root() -> Path:
    return ROOT


def baseline_html(stem: str) -> str:
    return (ROOT / "tests" / "baseline" / f"{stem}.snap").read_text(encoding="utf-8")


def built_html(stem: str) -> str:
    return (ROOT / f"{stem}.html").read_text(encoding="utf-8")


@pytest.fixture
def sandbox(tmp_path, monkeypatch):
    """Isolated copy of the build inputs and generated pages; build.ROOT points at it.

    Tests must never write to the real working tree.
    """
    import build
    shutil.copytree(ROOT / "content", tmp_path / "content")
    shutil.copytree(ROOT / "templates" / "pages", tmp_path / "templates" / "pages")
    (tmp_path / "assets").mkdir()
    shutil.copy(ROOT / "assets" / "theme.css", tmp_path / "assets" / "theme.css")
    for s in PAGES:
        shutil.copy(ROOT / f"{s}.html", tmp_path / f"{s}.html")
    monkeypatch.setattr(build, "ROOT", tmp_path)
    return tmp_path
