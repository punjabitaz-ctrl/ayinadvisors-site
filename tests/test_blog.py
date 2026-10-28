"""The blog (2026-10-28): an index and question-led posts, linked from the footer only, never the main navigation.

Every post answers its question in the first section, carries a byline and dates, links the services of its practice,
and is described to search engines as a BlogPosting by the founder. Nothing on a post may claim a client result.
"""
import json

import pytest
from bs4 import BeautifulSoup

import build

POSTS = build.blog_posts()


@pytest.fixture(scope="module")
def pages():
    return build.render_all()


def _soup(html):
    return BeautifulSoup(html, "html.parser")


def _ld(html):
    return [json.loads(s.string) for s in _soup(html).find_all("script", type="application/ld+json")]


def test_blog_is_in_the_footer_and_not_in_the_main_navigation(pages):
    for stem, html in pages.items():
        soup = _soup(html)
        assert not [a for a in soup.select("nav a") if "blog" in a["href"].lower()], stem
        footer = [a["href"] for a in soup.select("footer.footer a")]
        assert build.clean_href(build.page_root(stem) + "blog.html") in footer, stem


def test_index_lists_every_post_newest_first(pages):
    links = [a["href"] for a in _soup(pages["blog"]).select(".post-list h2 a")]
    assert links == [build.clean_href(p["href"]) for p in POSTS]
    assert [p["published"] for p in POSTS] == sorted((p["published"] for p in POSTS), reverse=True)


@pytest.mark.parametrize("post", POSTS, ids=[p["slug"] for p in POSTS])
def test_post_page_answers_its_question(pages, post):
    soup = _soup(pages[post["stem"]])
    assert soup.h1.get_text(strip=True) == post["question"]
    first = soup.select(".prose h2")[0]
    assert first.get_text(strip=True) == "The short answer" and first.find_next_sibling("p").get_text(strip=True)
    byline = soup.select_one(".post-byline")
    assert "Taz Abbas" in byline.get_text() and byline.select_one(f"time[datetime='{post['published']}']")


@pytest.mark.parametrize("post", POSTS, ids=[p["slug"] for p in POSTS])
def test_post_links_its_practice_services_and_contact_with_the_practice(pages, post):
    soup = _soup(pages[post["stem"]])
    related = [a["href"] for a in soup.select("#related h3 a")]
    assert related == ["../" + r for r in post["related"]]
    assert all(r.startswith(post["practice"] + "/") for r in post["related"])
    assert soup.select_one("section.cta a.btn")["href"] == f"../Contact?practice={post['practice']}"


@pytest.mark.parametrize("post", POSTS, ids=[p["slug"] for p in POSTS])
def test_post_is_a_blog_posting_by_the_founder(pages, post):
    crumbs, posting = _ld(pages[post["stem"]])
    page = build.load_site()["pages"][post["stem"]]
    assert posting["@type"] == "BlogPosting" and posting["headline"] == post["question"]
    assert posting["url"] == page["canonical"] == f"{build.SITE_URL}/{post['stem']}"
    assert posting["datePublished"] == post["published"] and posting["dateModified"] == post["updated"]
    assert posting["author"]["@id"] == build.FOUNDER_ID and posting["publisher"]["@id"] == build.ORG_ID
    assert [i["item"] for i in crumbs["itemListElement"]] == [f"{build.SITE_URL}/", f"{build.SITE_URL}/blog", page["canonical"]]
    assert 'property="og:type" content="article"' in pages[post["stem"]]


def test_blog_index_is_a_blog(pages):
    crumbs, blog = _ld(pages["blog"])
    assert blog["@type"] == "Blog" and blog["url"] == f"{build.SITE_URL}/blog"
    assert crumbs["@type"] == "BreadcrumbList"


def test_a_post_without_a_page_cannot_build(monkeypatch):
    blog = build.load_blog()
    blog["posts"].append({**blog["posts"][0], "slug": "no-page"})
    monkeypatch.setattr(build, "load_blog", lambda: blog)
    with pytest.raises(KeyError, match="no-page"):
        build.blog_posts()


def test_date_label_is_the_us_form():
    assert build.date_label("2026-10-28") == "October 28, 2026"
    assert build.date_label("2027-01-05") == "January 5, 2027"
