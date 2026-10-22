"""No colour literal (hex, rgb(), hsl(), white/black) outside the theme and a reasoned allowlist."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ALLOWLIST = ROOT / "tests" / "color_literal_allowlist.json"

LITERAL = re.compile(
    r"%23[0-9a-fA-F]{6}\b|(?<![&\w/])#[0-9a-fA-F]{8}\b|(?<![&\w/])#[0-9a-fA-F]{6}\b|(?<![&\w/])#[0-9a-fA-F]{3,4}\b"
    r"|\brgba?\([^)]*\)|\bhsla?\([^)]*\)|(?<![\w-])(?:white|black)(?![\w-])"
)


def scanned_files() -> list[Path]:
    files = [p for p in sorted((ROOT / "assets").glob("*.css")) if p.name != "theme.css"]
    files += sorted((ROOT / "templates").glob("*.j2"))
    files += sorted(p for p in (ROOT / "templates" / "pages").iterdir() if p.is_file())
    files.append(ROOT / "assets" / "site.js")
    files.append(ROOT / "assets" / "motion.js")
    # the hero bundle is built from this source; the bundle itself carries three.js and is not scanned
    files += sorted((ROOT / "tools" / "hero3d" / "src").glob("*.js"))
    return files


def found() -> set[tuple[str, str]]:
    out = set()
    for p in scanned_files():
        rel = p.relative_to(ROOT).as_posix()
        for m in LITERAL.finditer(p.read_text(encoding="utf-8")):
            out.add((rel, m.group(0)))
    return out


def allowed() -> list[dict]:
    return json.loads(ALLOWLIST.read_text(encoding="utf-8"))


def test_no_color_literals_outside_the_theme():
    ok = {(e["path"], e["literal"]) for e in allowed()}
    bad = sorted(found() - ok)
    assert not bad, f"{len(bad)} colour literal(s) outside theme/allowlist:\n" + "\n".join(f"  {p}: {l}" for p, l in bad)


def test_allowlist_entries_are_still_used():
    seen = found()
    stale = [e for e in allowed() if (e["path"], e["literal"]) not in seen]
    assert not stale, f"stale allowlist entries: {stale}"


def test_allowlist_entries_have_reasons():
    assert all(e.get("reason", "").strip() for e in allowed())
