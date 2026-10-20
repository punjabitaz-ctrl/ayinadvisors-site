"""Photography registry and <picture> rendering.

content/images.json is the single source of truth: one entry per photograph with its source
file *name* (never a path), alt text or an explicit decorative flag, focal point and crop.
The optimiser (tools/optimize_images.py) writes assets/img/<slug>-{480,960,1600}.webp from it
and build.expand_image_slots turns <image-slot> placeholders into render_picture output.
"""
import json
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REGISTRY_PATH = ROOT / "content" / "images.json"
WIDTHS = (480, 960, 1600)
DEFAULT_WIDTH = 960
IMG_DIR = "assets/img"
_REQUIRED = ("slug", "source", "focal", "pillar", "crop")


def load_registry(path: Path = REGISTRY_PATH) -> dict:
    """slug -> entry. Raises ValueError naming the slug when an entry is unusable."""
    entries = json.loads(Path(path).read_text(encoding="utf-8"))["images"]
    out: dict[str, dict] = {}
    for e in entries:
        slug = e.get("slug", "?")
        missing = [k for k in _REQUIRED if k not in e]
        if missing:
            raise ValueError(f"image {slug!r}: missing {', '.join(missing)}")
        if slug in out:
            raise ValueError(f"image {slug!r}: duplicate slug")
        has_alt = bool((e.get("alt") or "").strip())
        decorative = e.get("decorative") is True and bool((e.get("reason") or "").strip())
        if not (has_alt or decorative):
            raise ValueError(f"image {slug!r}: needs non-empty alt, or decorative: true with a reason")
        ratio(e["crop"])
        out[slug] = e
    return out


def ratio(crop: str) -> tuple[int, int]:
    a, b = (int(x) for x in crop.split(":"))
    return a, b


def _lookup(slug: str, registry: dict | None) -> dict:
    reg = load_registry() if registry is None else registry
    if slug not in reg:
        raise KeyError(f"unknown image slug {slug!r}; known: {', '.join(sorted(reg))}")
    return reg[slug]


def dimensions(slug: str, width: int, registry: dict | None = None) -> tuple[int, int]:
    """Nominal (width, height) of the crop at `width`."""
    a, b = ratio(_lookup(slug, registry)["crop"])
    return width, round(width * b / a)


def render_picture(slug: str, sizes: str, loading: str = "lazy", cls: str = "",
                   registry: dict | None = None) -> str:
    entry = _lookup(slug, registry)
    if loading not in ("lazy", "eager"):
        raise ValueError(f"loading must be 'lazy' or 'eager', not {loading!r}")
    srcset = ", ".join(f"{IMG_DIR}/{slug}-{w}.webp {w}w" for w in WIDTHS)
    w, h = dimensions(slug, max(WIDTHS), registry)
    alt = "" if entry.get("decorative") is True else escape(entry["alt"].strip(), quote=True)
    cls_attr = f' class="{escape(cls, quote=True)}"' if cls else ""
    return (
        f'<picture><source type="image/webp" srcset="{srcset}" sizes="{escape(sizes, quote=True)}">'
        f'<img src="{IMG_DIR}/{slug}-{DEFAULT_WIDTH}.webp" width="{w}" height="{h}" alt="{alt}"'
        f'{cls_attr} loading="{loading}" decoding="async"></picture>'
    )
