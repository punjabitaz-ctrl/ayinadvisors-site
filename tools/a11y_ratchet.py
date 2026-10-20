#!/usr/bin/env python3
"""Record today's accessibility problems so the gate can only get stricter.

    python tools/a11y_ratchet.py            # print current static + axe totals
    python tools/a11y_ratchet.py --update   # lower/remove recorded problems; refuses to raise any
                                            # count unless --allow-increase is given. Also syncs
                                            # tests/a11y_review.json (new items 'unreviewed', stale pruned)

Needs Chromium for the axe half: `python -m playwright install chromium`.
Static counts need no browser; with --static-only the axe section is kept as is.
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT), str(ROOT / "tests")]

KNOWN = ROOT / "tests" / "a11y_known_issues.json"
REVIEW = ROOT / "tests" / "a11y_review.json"
# Auto-recorded needs-review entries are "unreviewed" (no reason); a human sets
# "status": "justified" and writes a real "reason" after checking by hand.


def current_axe() -> tuple[dict, list]:
    from playwright.sync_api import sync_playwright
    from a11y_browser.conftest import PAGES, WIDTHS, collect_axe, start_server

    server, url = start_server()
    axe: dict[str, int] = {}
    review: set[tuple] = set()
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            for stem in PAGES:
                for width in WIDTHS:
                    viol, rev = collect_axe(browser, url, stem, width)
                    for v in viol:
                        axe[f"{stem}|{width}|{v.rule}"] = v.nodes
                    for r in rev:
                        review.update((stem, r.rule, sel) for sel in r.selectors)
            browser.close()
    finally:
        server.shutdown()
        server.server_close()
    return dict(sorted(axe.items())), sorted(review)


def increases(old: dict, new: dict) -> dict:
    """Keys whose count would rise (or that are new with a count > 0), per section."""
    out = {}
    for section in ("static", "axe"):
        o, n = old.get(section, {}), new.get(section, {})
        bad = {k: (o.get(k, 0), v) for k, v in n.items() if v > o.get(k, 0)}
        if bad:
            out[section] = bad
    return out


def write_ratchet(known_path, review_path, static, axe, review, allow_increase=False):
    """Rewrite the ratchet files. Refuses to raise any recorded count unless allow_increase.

    Also prunes review entries that match no current needs-review result and
    adds new ones as status "unreviewed".
    """
    known_path, review_path = Path(known_path), Path(review_path)
    old = json.loads(known_path.read_text(encoding="utf-8")) if known_path.exists() else {"static": {}, "axe": {}}
    worse = increases(old, {"static": static, "axe": axe})
    if worse and not allow_increase:
        raise SystemExit(
            "refusing to RAISE the ratchet (pass --allow-increase to override): "
            + json.dumps(worse, sort_keys=True)
        )
    known_path.write_text(json.dumps({"static": static, "axe": axe}, indent=2, sort_keys=True) + chr(10), encoding="utf-8")
    if review is None:  # static-only run: leave the review file alone
        return
    items = json.loads(review_path.read_text(encoding="utf-8"))["items"] if review_path.exists() else []
    current = set(review)
    items = [i for i in items if (i["page"], i["rule"], i["selector"]) in current or i["selector"] == "*"]
    have = {(i["page"], i["rule"], i["selector"]) for i in items}
    for page, rule, sel in review:
        if (page, rule, sel) not in have and (page, rule, "*") not in have:
            items.append({"page": page, "rule": rule, "selector": sel, "status": "unreviewed", "reason": ""})
    items.sort(key=lambda i: (i["page"], i["rule"], i["selector"]))
    review_path.write_text(json.dumps({"items": items}, indent=2) + chr(10), encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--update", action="store_true", help="rewrite the ratchet files from current results")
    ap.add_argument("--allow-increase", action="store_true",
                    help="permit --update to raise recorded counts or add new problems (default: refuse)")
    ap.add_argument("--static-only", action="store_true", help="skip the axe/browser half")
    args = ap.parse_args()

    from test_a11y_static import current_static

    static = current_static()
    old = json.loads(KNOWN.read_text(encoding="utf-8")) if KNOWN.exists() else {"static": {}, "axe": {}}
    if args.static_only:
        axe, review = old.get("axe", {}), None
    else:
        axe, review = current_axe()

    print(f"static: {sum(static.values())} problems across {len(static)} page/rule keys")
    print(f"axe:    {sum(axe.values())} nodes across {len(axe)} page/width/rule keys")
    if not args.static_only:
        print(f"axe needs-review: {len(review)} distinct page/rule/selector items")

    if not args.update:
        return 0

    write_ratchet(KNOWN, REVIEW, static, axe, review, args.allow_increase)
    print(f"wrote {KNOWN.relative_to(ROOT)} and {REVIEW.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
