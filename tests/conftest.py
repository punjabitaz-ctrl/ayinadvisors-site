from pathlib import Path
import shutil
import pytest
from build import PAGES  # noqa: F401  (re-exported for tests)

ROOT = Path(__file__).resolve().parent.parent


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "browser: drives headless Chromium (needs `python -m playwright install chromium`); "
        "skips cleanly when the browser is unavailable. Deselect with -m 'not browser'.",
    )


@pytest.fixture(scope="session")
def root() -> Path:
    return ROOT


def baseline_html(stem: str) -> str:
    return (ROOT / "tests" / "baseline" / (stem.replace("/", "__") + ".snap")).read_text(encoding="utf-8")


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
    # template-rendered pages (hub, pillars) read their bodies from templates/*.j2 and content/services.json
    for j2 in (ROOT / "templates").glob("*.j2"):
        shutil.copy(j2, tmp_path / "templates" / j2.name)
    shutil.copy(ROOT / "sitemap.xml", tmp_path / "sitemap.xml")
    (tmp_path / "assets").mkdir()
    shutil.copy(ROOT / "assets" / "theme.css", tmp_path / "assets" / "theme.css")
    for s in PAGES:
        (tmp_path / f"{s}.html").parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(ROOT / f"{s}.html", tmp_path / f"{s}.html")
    monkeypatch.setattr(build, "ROOT", tmp_path)
    return tmp_path
