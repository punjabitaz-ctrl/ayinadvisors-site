#!/usr/bin/env python3
"""Write assets/img/<slug>-{480,960,1600}.webp from the photographs named in content/images.json.

    python tools/optimize_images.py <source-dir>

The source folder is only ever given on the command line (originals are never committed and
their location is not recorded in the repo). Each photograph is cropped to its registry aspect
around its focal point, resized to the three widths (never upscaled), saved without EXIF or
colour-profile metadata, and kept within the per-file size budget. Exits non-zero on a missing
source or a file that cannot meet the budget.
"""
import io
import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from tools import images  # noqa: E402

OUT_DIR = images.ROOT / "assets" / "img"
BUDGET = 160_000  # bytes; stricter than 160 KiB so either reading of "160 KB" holds
QUALITIES = (82, 76, 70, 64, 58, 52, 46, 40)


class OptimizeError(Exception):
    pass


def crop_box(size: tuple[int, int], crop: str, focal: list[float]) -> tuple[int, int, int, int]:
    W, H = size
    a, b = images.ratio(crop)
    if W * b >= H * a:  # source is wider than the target aspect
        ch, cw = H, round(H * a / b)
    else:
        cw, ch = W, round(W * b / a)
    left = min(max(round(focal[0] * W - cw / 2), 0), W - cw)
    top = min(max(round(focal[1] * H - ch / 2), 0), H - ch)
    return left, top, left + cw, top + ch


def encode(im: Image.Image, budget: int) -> bytes:
    for q in QUALITIES:
        buf = io.BytesIO()
        im.save(buf, "WEBP", quality=q, method=6)  # no exif/icc passed: metadata is dropped
        if buf.tell() <= budget:
            return buf.getvalue()
    raise OptimizeError(f"cannot fit {im.size[0]}px image within the {budget // 1000} KB budget")


def optimize(source_dir: Path, out_dir: Path = OUT_DIR, registry: dict | None = None,
             budget: int = BUDGET) -> list[Path]:
    reg = images.load_registry() if registry is None else registry
    source_dir, out_dir = Path(source_dir), Path(out_dir)
    missing = [e["source"] for e in reg.values() if not (source_dir / e["source"]).is_file()]
    if missing:
        raise OptimizeError("missing source file(s): " + ", ".join(missing))
    out_dir.mkdir(parents=True, exist_ok=True)
    written = []
    for slug, e in reg.items():
        with Image.open(source_dir / e["source"]) as src:
            src = src.convert("RGB")
            cropped = src.crop(crop_box(src.size, e["crop"], e["focal"]))
        a, b = images.ratio(e["crop"])
        for w in images.WIDTHS:
            tw = min(w, cropped.width)  # never upscale
            th = round(tw * b / a)
            im = cropped if (tw, th) == cropped.size else cropped.resize((tw, th), Image.LANCZOS)
            try:
                data = encode(im, budget)
            except OptimizeError as err:
                raise OptimizeError(f"{slug}-{w}.webp: {err}") from None
            path = out_dir / f"{slug}-{w}.webp"
            path.write_bytes(data)
            written.append(path)
    return written


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print(__doc__)
        return 2
    try:
        for p in optimize(Path(argv[0])):
            print(f"  {p.name}  {p.stat().st_size / 1024:.1f} KB")
    except OptimizeError as err:
        print(f"error: {err}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
