from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parent.parent
PAGES = ["index", "About", "Services", "Projects", "BizCheck", "Contact", "404"]


@pytest.fixture(scope="session")
def root() -> Path:
    return ROOT


def baseline_html(stem: str) -> str:
    return (ROOT / "tests" / "baseline" / f"{stem}.snap").read_text(encoding="utf-8")


def built_html(stem: str) -> str:
    return (ROOT / f"{stem}.html").read_text(encoding="utf-8")
