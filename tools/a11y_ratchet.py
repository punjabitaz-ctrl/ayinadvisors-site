#!/usr/bin/env python3
"""Record today's accessibility problems so the gate can only get stricter.

    python tools/a11y_ratchet.py            # print current static + axe totals
    python tools/a11y_ratchet.py --update   # rewrite tests/a11y_known_issues.json
                                            # (and add unjustified needs-review items
                                            # to tests/a11y_review.json for triage)

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
PLACEHOLDER = ("Recorded at the Task 2 baseline: axe cannot resolve the effective background "
               "(gradient, translucent layer or overlap). Re-check by hand once the page is re-themed.")


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


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--update", action="store_true", help="rewrite the ratchet files from current results")
    ap.add_argument("--static-only", action="store_true", help="skip the axe/browser half")
    args = ap.parse_args()

    from test_a11y_static import current_static

    static = current_static()
    old = json.loads(KNOWN.read_text(encoding="utf-8")) if KNOWN.exists() else {"static": {}, "axe": {}}
    if args.static_only:
        axe, review = old.get("axe", {}), []
    else:
        axe, review = current_axe()

    print(f"static: {sum(static.values())} problems across {len(static)} page/rule keys")
    print(f"axe:    {sum(axe.values())} nodes across {len(axe)} page/width/rule keys")
    if not args.static_only:
        print(f"axe needs-review: {len(review)} distinct page/rule/selector items")

    if not args.update:
        return 0

    KNOWN.write_text(json.dumps({"static": static, "axe": axe}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    items = json.loads(REVIEW.read_text(encoding="utf-8"))["items"] if REVIEW.exists() else []
    have = {(i["page"], i["rule"], i["selector"]) for i in items}
    for page, rule, sel in review:
        if (page, rule, sel) not in have and (page, rule, "*") not in have:
            items.append({"page": page, "rule": rule, "selector": sel, "reason": PLACEHOLDER})
    items.sort(key=lambda i: (i["page"], i["rule"], i["selector"]))
    REVIEW.write_text(json.dumps({"items": items}, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {KNOWN.relative_to(ROOT)} and {REVIEW.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
