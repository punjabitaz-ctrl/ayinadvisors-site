import subprocess

from conftest import ROOT


def _groups(text):
    groups, cur = [], None
    for line in text.splitlines():
        line = line.strip()
        if line.lower().startswith("user-agent:"):
            cur = [line]
            groups.append(cur)
        elif cur is not None and line and not line.startswith("#"):
            cur.append(line)
    return groups


def test_catch_all_group_blocks_source_dirs():
    text = (ROOT / "robots.txt").read_text(encoding="utf-8")
    star = next(g for g in _groups(text) if g[0] == "User-agent: *")
    for d in ("templates", "content", "tests", "docs"):
        assert f"Disallow: /{d}/" in star, d
    assert "Allow: /" in star
    assert "Sitemap: https://ayinadvisors.com/sitemap.xml" in text


def test_user_agent_group_count_unchanged():
    head = subprocess.run(
        ["git", "show", "HEAD:robots.txt"], cwd=ROOT, capture_output=True,
        text=True, encoding="utf-8", check=True,
    ).stdout
    now = (ROOT / "robots.txt").read_text(encoding="utf-8")
    assert len(_groups(now)) == len(_groups(head))
