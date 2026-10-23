"""Compare or refresh the parity snapshots in tests/baseline/.

    python tools/baseline.py diff       # per page, the page_facts keys that differ
    python tools/baseline.py snapshot   # copy each generated root page over its .snap
"""
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
for _p in (ROOT, ROOT / "tests"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from build import PAGES  # noqa: E402
from parity import page_facts  # noqa: E402


def snap_name(stem: str) -> str:
    """Snapshot file name for a page stem: a subfolder page "a/b" is stored as "a__b.snap"."""
    return stem.replace("/", "__") + ".snap"


def _snap(root: Path, stem: str) -> Path:
    return root / "tests" / "baseline" / snap_name(stem)


def diff(root: Path = ROOT) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for stem in PAGES:
        built = page_facts((root / f"{stem}.html").read_text(encoding="utf-8"))
        if not _snap(root, stem).exists():
            out[stem] = ["(new page: no snapshot)"]
            continue
        base = page_facts(_snap(root, stem).read_text(encoding="utf-8"))
        keys = [k for k in built if built[k] != base.get(k)]
        if keys:
            out[stem] = keys
    return out


def snapshot(root: Path = ROOT) -> None:
    for stem in PAGES:
        shutil.copyfile(root / f"{stem}.html", _snap(root, stem))


def main(argv: list[str]) -> int:
    if len(argv) != 1 or argv[0] not in ("diff", "snapshot"):
        print(__doc__)
        return 2
    if argv[0] == "diff":
        d = diff()
        if not d:
            print("diff: none")
        for stem, keys in d.items():
            print(f"{stem}: {', '.join(keys)}")
    else:
        snapshot()
        print(f"snapshot: {len(PAGES)} pages")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
