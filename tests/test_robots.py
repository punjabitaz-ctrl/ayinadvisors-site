from conftest import ROOT, PAGES


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
    for d in ("templates", "content", "tests", "docs", "tools"):
        assert f"Disallow: /{d}/" in star, d
    assert "Allow: /" in star
    assert "Sitemap: https://ayinadvisors.com/sitemap.xml" in text


def test_user_agent_group_count_pinned():
    text = (ROOT / "robots.txt").read_text(encoding="utf-8")
    groups = _groups(text)
    assert len(groups) == 19
    names = {g[0].split(":", 1)[1].strip().lower() for g in groups}
    # AI search and answer crawlers cite the site to people searching; only training crawlers are blocked.
    for answer_bot in ("oai-searchbot", "chatgpt-user", "perplexitybot", "perplexity-user", "claude-searchbot", "claude-user"):
        assert answer_bot not in names, answer_bot
    for trainer in ("gptbot", "claudebot", "ccbot", "google-extended", "applebot-extended"):
        assert trainer in names, trainer
    # Search engines must stay allowed: never given their own (blocking) group.
    assert "googlebot" not in names
    assert "bingbot" not in names


def test_catch_all_group_does_not_block_public_urls():
    text = (ROOT / "robots.txt").read_text(encoding="utf-8")
    star = next(g for g in _groups(text) if g[0] == "User-agent: *")
    public = ["/assets/", "/robots.txt", "/sitemap.xml", "/"]
    public += [f"/{s}.html" for s in PAGES] + [f"/{s}" for s in PAGES if s != "index"]
    for line in star:
        if not line.startswith("Disallow:"):
            continue
        rule = line.split(":", 1)[1].strip()
        if not rule:
            continue
        for url in public:
            assert not url.startswith(rule), f"{line} blocks {url}"
