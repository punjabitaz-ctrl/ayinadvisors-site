"""Resolve content/theme.json into solid colours, check contrast, emit assets/theme.css."""
import json
from pathlib import Path

from tools.contrast import composite, ratio, solve_min_darken

ROOT = Path(__file__).resolve().parent.parent
THEME_PATH = ROOT / "content" / "theme.json"

CONTEXTS = ("page", "alt", "card", "inverse", "accent")
ROLES = (
    "surface", "ink", "ink-muted", "accent-ink", "line", "field-bg", "field-border",
    "field-ink", "field-placeholder", "focus-ring", "danger-ink", "success-ink",
)

# (fg role, bg role, minimum, label) checked in every context of every theme.
CONTEXT_PAIRINGS = (
    ("ink", "surface", 4.5, "body text"),
    ("ink-muted", "surface", 4.5, "muted text"),
    ("accent-ink", "surface", 4.5, "accent text"),
    ("danger-ink", "surface", 4.5, "error text"),
    ("success-ink", "surface", 4.5, "success text"),
    ("field-ink", "field-bg", 4.5, "field text"),
    ("field-placeholder", "field-bg", 4.5, "placeholder"),
    ("field-border", "surface", 3.0, "field border"),
    ("focus-ring", "surface", 3.0, "focus ring"),
)
GLOBAL_PAIRINGS = (("on-accent", "accent-fill", 4.5, "button label"),)


def load_theme(path: Path = THEME_PATH) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _evaluate(expr, theme: dict, derived: dict, lookup):
    """Evaluate a value expression to '#rrggbb'.

    lookup(role) resolves a bare role name ('surface', 'field-bg') in the current context.
    """
    if isinstance(expr, str):
        if expr.startswith("#"):
            return expr.lower()
        if expr.startswith("@"):
            name = expr[1:]
            if name in derived:
                return derived[name]
            if name in theme["palette"]:
                return theme["palette"][name].lower()
            raise KeyError(f"unknown palette/derived name {expr!r}")
        return lookup(expr)
    if "mix" in expr:
        fg, alpha, bg = expr["mix"]
        return composite(_evaluate(fg, theme, derived, lookup), alpha, _evaluate(bg, theme, derived, lookup))
    if "solve" in expr:
        return solve_min_darken(
            _evaluate(expr["solve"], theme, derived, lookup),
            [_evaluate(b, theme, derived, lookup) for b in expr["on"]],
            expr["min"],
        )
    raise ValueError(f"bad expression {expr!r}")


def _resolve_theme(spec: dict, theme: dict, derived: dict, globals_: dict) -> dict:
    out: dict[str, dict[str, str]] = {}
    for ctx, roles in spec.items():
        cache: dict[str, str] = {}

        def lookup(role, roles=roles, cache=cache):
            if role not in cache:
                cache[role] = _evaluate(roles[role], theme, derived, lookup)
            return cache[role]

        out[ctx] = {role: lookup(role) for role in roles}
    out["global"] = dict(globals_)
    return out


def resolve(theme: dict) -> dict:
    """{theme: {context: {role: '#rrggbb'}}}; the 'global' context holds accent-fill etc."""
    derived: dict[str, str] = {}
    for name, expr in theme["derive"].items():
        derived[name] = _evaluate(expr, theme, derived, lambda r: (_ for _ in ()).throw(KeyError(r)))
    globals_ = {
        k: _evaluate(v, theme, derived, lambda r: (_ for _ in ()).throw(KeyError(r)))
        for k, v in theme["globals"].items()
    }
    return {name: _resolve_theme(spec, theme, derived, globals_) for name, spec in theme["themes"].items()}


def _get(resolved_theme: dict, ctx: str, role: str) -> str:
    return resolved_theme[ctx].get(role) or resolved_theme["global"][role]


def required_pairings(resolved: dict, theme: dict | None = None) -> list[tuple]:
    """Every (theme, context, fg_role, bg_role, minimum, label) the design relies on."""
    theme = theme or load_theme()
    out = []
    for th, ctxs in resolved.items():
        real = [c for c in ctxs if c != "global"]
        for ctx in real:
            out.extend((th, ctx, fg, bg, m, label) for fg, bg, m, label in CONTEXT_PAIRINGS)
        out.extend((th, "global", fg, bg, m, label) for fg, bg, m, label in GLOBAL_PAIRINGS)
        for extra in theme.get("pairings", []):
            targets = real if extra["contexts"] == "*" else extra["contexts"]
            for ctx in targets:
                out.append((th, ctx, extra["fg"], extra["bg"], extra["min"], extra["label"]))
    return out


def failures(resolved: dict, theme: dict | None = None) -> list[str]:
    bad = []
    for th, ctx, fg, bg, minimum, label in required_pairings(resolved, theme):
        a, b = _get(resolved[th], ctx, fg), _get(resolved[th], ctx, bg)
        r = ratio(a, b)
        if r < minimum:
            bad.append(f"{th}/{ctx}: {label} ({fg} {a} on {bg} {b}) {r:.2f} < {minimum}")
    return bad


def _block(selector: str, roles: dict[str, str], scheme: str | None = None) -> str:
    lines = [f"{selector} {{"]
    if scheme:
        lines.append(f"  color-scheme: {scheme};")
    lines += [f"  --{role}: {value};" for role, value in roles.items()]
    lines.append("}")
    return "\n".join(lines)


def _surface_block(selector: str, roles: dict[str, str]) -> str:
    lines = [f"{selector} {{"]
    for role, value in roles.items():
        lines.append(f"  --{role}: {value};")
    lines.append("  background-color: var(--surface);")
    lines.append("  color: var(--ink);")
    lines.append("}")
    return "\n".join(lines)


def _indent(block: str) -> str:
    return "\n".join(("  " + ln) if ln else ln for ln in block.split("\n"))


def render_css(resolved: dict) -> str:
    """Light by default (:root + surfaces), an explicit light/dark per html[data-theme], and the
    dark set again inside a prefers-color-scheme media rule scoped to :root:not([data-theme]) so a
    visitor without JavaScript on a dark system still gets dark, while any explicit choice (which
    the head script writes to data-theme) is never overridden by the system."""
    parts = ["/* GENERATED by build.py from content/theme.json -- do not edit directly */"]
    light, dark = resolved["light"], resolved["dark"]
    parts.append(_block(":root", {**light["page"], **light["global"]}, "light"))
    parts += [_surface_block(f".surface-{c}", light[c]) for c in CONTEXTS]
    parts.append(':root[data-theme="light"] {\n  color-scheme: light;\n}')
    media = [_block(":root:not([data-theme])", {**dark["page"], **dark["global"]}, "dark")]
    media += [_surface_block(f":root:not([data-theme]) .surface-{c}", dark[c]) for c in CONTEXTS]
    parts.append("@media (prefers-color-scheme: dark) {\n" + "\n\n".join(_indent(b) for b in media) + "\n}")
    parts.append(_block(':root[data-theme="dark"]', {**dark["page"], **dark["global"]}, "dark"))
    parts += [_surface_block(f'[data-theme="dark"] .surface-{c}', dark[c]) for c in CONTEXTS]
    # Print always prints the light look, whatever the screen theme: the light set again, last, with a selector at
    # least as specific as every dark rule above (it covers both an explicit data-theme and none at all).
    both = ':root[data-theme], :root:not([data-theme])'
    pr = [_block(both, {**light["page"], **light["global"]}, "light")]
    pr += [_surface_block(", ".join(f"{r} .surface-{c}" for r in (':root[data-theme]', ':root:not([data-theme])')), light[c]) for c in CONTEXTS]
    parts.append("@media print {\n" + "\n\n".join(_indent(b) for b in pr) + "\n}")
    return "\n\n".join(parts) + "\n"
