# extract_bodies.py  -- one-shot; removed in Task 7
import json, re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PAGES = ["index", "About", "Services", "Projects", "BizCheck", "Contact", "404"]
OUT = ROOT / "templates" / "pages"
OUT.mkdir(parents=True, exist_ok=True)

for stem in PAGES:
    src = (ROOT / "tests" / "baseline" / f"{stem}.snap").read_text(encoding="utf-8")

    # head_extra is the whole head MINUS the five things base.html owns, verbatim and
    # in source order. Do not enumerate what to keep: six pages write their fonts link
    # as <link href=... rel="stylesheet"> and an allow-list regex silently drops it.
    head = src[src.index("<head>") + len("<head>"): src.index("</head>")]
    for pat in (
        r'<meta charset="[^"]*"\s*/?>',
        r'<meta name="viewport"[^>]*>',
        r'<title>.*?</title>',
        r'<meta name="description"[^>]*>',
        r'<link rel="canonical"[^>]*>',
    ):
        head = re.sub(pat, "", head, count=1, flags=re.S)
    head_extra = head.strip()

    drawer_end = src.index("</div>", src.index('<div class="mobile-drawer"')) + len("</div>")
    tail = src.index('<script src="assets/site.js">')
    foot = src.find('<footer class="footer">')
    body_end = foot if foot != -1 else tail
    body = src[drawer_end:body_end].strip()

    after = src[tail + len('<script src="assets/site.js"></script>'): src.rindex("</body>")].strip()

    (OUT / f"{stem}.body.html").write_text(body + "\n", encoding="utf-8")
    (OUT / f"{stem}.json").write_text(
        json.dumps({"head_extra": head_extra, "body_scripts": after}, indent=2, ensure_ascii=False),
        encoding="utf-8")
    print(f"  {stem}: body={len(body)}  head_extra={len(head_extra)}  scripts={len(after)}")
