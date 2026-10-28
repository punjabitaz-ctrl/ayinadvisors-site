"""The blog (2026-10-28): an index and question-led posts, linked from the footer only, never the main navigation.

Only posts Taz has approved are in the repo: Cloudflare serves the whole repo, so a draft here would be reachable.
Every post answers its question in the first section, carries a byline and dates, links the services of its practice,
and is described to search engines as a BlogPosting by the founder. The post tests render a sample post in a sandbox,
so they hold before the first real post is approved.
"""
import json

import pytest
from bs4 import BeautifulSoup

import build
from conftest import ROOT

SAMPLE = {
    "slug": "sample-question",
    "question": "What is a sample question a buyer might ask?",
    "summary": "A sample answer in a sentence or two, used only by the tests.",
    "published": "2026-11-02",
    "updated": "2026-11-09",
    "practice": "partnerships",
    "related": ["partnerships/channel-strategy", "partnerships/market-entry-research"],
}
SAMPLE_BODY = '<h2 id="short-answer">The short answer</h2>\n<p>A sample answer.</p>\n<h2 id="more">More detail</h2>\n<p>Detail.</p>\n'


def _soup(html):
    return BeautifulSoup(html, "html.parser")


def _ld(html):
    return [json.loads(s.string) for s in _soup(html).find_all("script", type="application/ld+json")]


def _render(stem):
    body, head, scripts = build.page_parts(stem)
    return build.render_page(stem, build.expand_image_slots(body, build.page_root(stem)), head, scripts)


@pytest.fixture
def with_sample_post(sandbox):
    """The sandbox with one approved post added the way docs/blog/content-strategy.md describes."""
    blog = json.loads((sandbox / "content" / "blog.json").read_text(encoding="utf-8"))
    blog["posts"] = [SAMPLE] + blog["posts"]
    (sandbox / "content" / "blog.json").write_text(json.dumps(blog), encoding="utf-8")
    (sandbox / "content" / "blog").mkdir(exist_ok=True)
    (sandbox / "content" / "blog" / "sample-question.frag").write_text(SAMPLE_BODY, encoding="utf-8")
    site = json.loads((sandbox / "content" / "site.json").read_text(encoding="utf-8"))
    site["pages"]["blog/sample-question"] = {
        "title": "A Sample Question - AYiN Advisors", "description": "A sample description.",
        "canonical": "https://ayinadvisors.com/blog/sample-question", "active": "",
        "cta": site["pages"]["blog"]["cta"], "footer": True, "template": "post",
        "sitemap": {"priority": "0.6", "lastmod": "2026-11-09"}}
    (sandbox / "content" / "site.json").write_text(json.dumps(site), encoding="utf-8")
    return sandbox


def test_blog_is_in_the_footer_and_not_in_the_main_navigation():
    for stem, html in build.render_all().items():
        soup = _soup(html)
        assert not [a for a in soup.select("nav a") if "blog" in a["href"].lower()], stem
        footer = [a["href"] for a in soup.select("footer.footer a")]
        assert build.clean_href(build.page_root(stem) + "blog.html") in footer, stem


def test_only_approved_posts_are_in_the_repo():
    """Each post body in content/blog belongs to a post in blog.json, and each post has a site.json page."""
    posts = {p["slug"] for p in build.load_blog()["posts"]}
    bodies = {p.stem for p in (ROOT / "content" / "blog").glob("*")} if (ROOT / "content" / "blog").exists() else set()
    assert bodies == posts
    assert {s for s, p in build.load_site()["pages"].items() if p.get("template") == "post"} == {f"blog/{s}" for s in posts}


def test_blog_with_no_posts_says_so_instead_of_an_empty_list():
    if build.load_blog()["posts"]:
        pytest.skip("posts are published")
    soup = _soup(build.render_all()["blog"])
    assert not soup.select(".post-list") and soup.select_one(".post-empty").get_text(strip=True)


def test_blog_index_is_a_blog():
    crumbs, blog = _ld(build.render_all()["blog"])
    assert blog["@type"] == "Blog" and blog["url"] == f"{build.SITE_URL}/blog"
    assert crumbs["@type"] == "BreadcrumbList"


def test_index_lists_an_approved_post(with_sample_post):
    soup = _soup(_render("blog"))
    hrefs = [a["href"] for a in soup.select(".post-list h2 a")]
    assert hrefs[0] == "blog/sample-question", "the newest post comes first"
    assert hrefs[1:] == [f"blog/{p['slug']}" for p in build.load_blog()["posts"] if p["slug"] != SAMPLE["slug"]]
    assert not soup.select(".post-empty")


def test_post_page_answers_its_question(with_sample_post):
    soup = _soup(_render("blog/sample-question"))
    assert soup.h1.get_text(strip=True) == SAMPLE["question"]
    first = soup.select(".prose h2")[0]
    assert first.get_text(strip=True) == "The short answer" and first.find_next_sibling("p").get_text(strip=True)
    byline = soup.select_one(".post-byline")
    assert "Taz Abbas" in byline.get_text()
    assert byline.select_one("time[datetime='2026-11-02']").get_text() == "November 2, 2026"
    assert byline.select_one("time[datetime='2026-11-09']")  # updated date shown when it differs


def test_post_links_its_practice_services_and_contact_with_the_practice(with_sample_post):
    soup = _soup(_render("blog/sample-question"))
    assert [a["href"] for a in soup.select("#related h3 a")] == ["../partnerships/channel-strategy", "../partnerships/market-entry-research"]
    assert soup.select_one("section.cta a.btn")["href"] == "../Contact?practice=partnerships"


def test_post_is_a_blog_posting_by_the_founder(with_sample_post):
    html = _render("blog/sample-question")
    crumbs, posting = _ld(html)
    url = f"{build.SITE_URL}/blog/sample-question"
    assert posting["@type"] == "BlogPosting" and posting["headline"] == SAMPLE["question"] and posting["url"] == url
    assert posting["datePublished"] == "2026-11-02" and posting["dateModified"] == "2026-11-09"
    assert posting["author"]["@id"] == build.FOUNDER_ID and posting["publisher"]["@id"] == build.ORG_ID
    assert [i["item"] for i in crumbs["itemListElement"]] == [f"{build.SITE_URL}/", f"{build.SITE_URL}/blog", url]
    assert 'property="og:type" content="article"' in html


def test_a_post_without_a_page_cannot_build(with_sample_post):
    site = json.loads((with_sample_post / "content" / "site.json").read_text(encoding="utf-8"))
    del site["pages"]["blog/sample-question"]
    (with_sample_post / "content" / "site.json").write_text(json.dumps(site), encoding="utf-8")
    with pytest.raises(KeyError, match="sample-question"):
        build.blog_posts()


def test_a_related_service_must_have_a_page(with_sample_post):
    blog = json.loads((with_sample_post / "content" / "blog.json").read_text(encoding="utf-8"))
    blog["posts"][0]["related"] = ["partnerships/no-such-service"]
    (with_sample_post / "content" / "blog.json").write_text(json.dumps(blog), encoding="utf-8")
    with pytest.raises(KeyError, match="no-such-service"):
        build.page_parts("blog/sample-question")


def test_date_label_is_the_us_form():
    assert build.date_label("2026-10-28") == "October 28, 2026"
    assert build.date_label("2027-01-05") == "January 5, 2027"
