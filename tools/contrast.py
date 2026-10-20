"""WCAG 2.x contrast helpers. Colours are '#rrggbb' strings."""


def _rgb(hex_colour: str) -> tuple[int, int, int]:
    h = hex_colour.lstrip("#")
    if len(h) != 6:
        raise ValueError(f"expected #rrggbb, got {hex_colour!r}")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def _hex(rgb) -> str:
    return "#" + "".join(f"{max(0, min(255, int(round(c)))):02x}" for c in rgb)


def _lin(c: int) -> float:
    s = c / 255
    return s / 12.92 if s <= 0.03928 else ((s + 0.055) / 1.055) ** 2.4


def luminance(hex_colour: str) -> float:
    r, g, b = (_lin(c) for c in _rgb(hex_colour))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def ratio(fg: str, bg: str) -> float:
    a, b = luminance(fg), luminance(bg)
    hi, lo = max(a, b), min(a, b)
    return (hi + 0.05) / (lo + 0.05)


def composite(fg: str, alpha: float, bg: str) -> str:
    """Flatten fg at `alpha` over opaque bg into a solid colour."""
    f, b = _rgb(fg), _rgb(bg)
    return _hex(f[i] * alpha + b[i] * (1 - alpha) for i in range(3))


def solve_min_darken(fg: str, backgrounds: list[str], minimum: float) -> str:
    """Lightest darkening of fg (channels scaled by a factor <= 1) that reaches
    `minimum` against every background."""
    base = _rgb(fg)
    for step in range(0, 1001):
        factor = 1 - step / 1000
        cand = _hex(c * factor for c in base)
        if all(ratio(cand, bg) >= minimum for bg in backgrounds):
            return cand
    raise ValueError(f"{fg} cannot reach {minimum}:1 on {backgrounds}")
