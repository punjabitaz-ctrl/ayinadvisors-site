"""Draw apple-touch-icon.png (180x180) from the same geometry as favicon.svg.

iOS does not use an SVG touch icon, so the home-screen icon needs a PNG. It is drawn full-bleed (iOS rounds the
corners itself) at 4x and scaled down for smooth edges. Run: python tools/touch_icon.py
"""
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
NAVY = (6, 19, 37)
GOLD = (198, 161, 92)
HALF_GOLD = tuple((g + n) // 2 for g, n in zip(GOLD, NAVY))  # the 0.5-opacity ring of favicon.svg, over navy
SIZE, SS = 180, 4


def draw() -> Image.Image:
    k = SIZE * SS / 40  # favicon.svg units -> supersampled pixels
    img = Image.new("RGB", (SIZE * SS, SIZE * SS), NAVY)
    d = ImageDraw.Draw(img)

    def circle(r, fill=None, outline=None, width=0.0):
        c = 20 * k
        d.ellipse([c - r * k, c - r * k, c + r * k, c + r * k], fill=fill, outline=outline, width=round(width * k))

    circle(14 + 0.65, outline=GOLD, width=1.3)
    circle(8.4 + 0.55, outline=HALF_GOLD, width=1.1)
    circle(4.4, fill=GOLD)
    circle(1.7, fill=NAVY)
    return img.resize((SIZE, SIZE), Image.LANCZOS)


if __name__ == "__main__":
    out = ROOT / "apple-touch-icon.png"
    draw().save(out, optimize=True)
    print(f"  wrote {out.name}")
