import build
import pytest
from bs4 import BeautifulSoup
from parity import page_facts


def test_active_link_follows_the_page():
    html = build.render_page("About", "<main>x</main>")
    nav = {t: c for _, t, c in page_facts(html)["nav"]}
    assert "active" in nav["About"]
    assert "active" not in nav["Home"]


def test_bizcheck_keeps_its_gold_pill_and_own_cta():
    html = build.render_page("BizCheck", "<main>x</main>")
    facts = page_facts(html)
    nav = {t: c for _, t, c in facts["nav"]}
    assert "gold" in nav["BizCheck"] and "active" in nav["BizCheck"]
    assert facts["nav_cta"] == ("#submit", "Submit Your Idea", "btn")


def test_404_renders_without_a_footer():
    assert page_facts(build.render_page("404", "<main>x</main>"))["has_footer"] is False


def test_body_is_inserted_verbatim():
    body = "<main>{{ not_a_template }} {% nor_this %}</main>"
    assert body in build.render_page("About", body)


def test_generated_header_comment_is_present():
    assert build.render_page("About", "<main>x</main>").startswith("<!-- GENERATED")


def test_head_values_are_escaped_and_cannot_break_out(monkeypatch):
    site = build.load_site()
    site["pages"]["About"]["title"] = 'A & B "q" <x>'
    site["pages"]["About"]["description"] = 'Tom & "Jerry" onload="x"'
    site["pages"]["About"]["canonical"] = 'https://e.com/?a=1&b="2"'
    monkeypatch.setattr(build, "load_site", lambda: site)
    html = build.render_page("About", "<main>x</main>")
    assert "<title>A &amp; B &#34;q&#34; &lt;x&gt;</title>" in html
    soup = BeautifulSoup(html, "html.parser")
    desc = soup.find("meta", attrs={"name": "description"})
    assert desc["content"] == 'Tom & "Jerry" onload="x"'
    assert "onload" not in desc.attrs
    canon = soup.find("link", rel="canonical")
    assert canon["href"] == 'https://e.com/?a=1&b="2"' and set(canon.attrs) == {"rel", "href"}


def test_ampersand_titles_render_as_entities():
    html = build.render_page("index", "<main>x</main>")
    assert "US Market Entry &amp; Channel Strategy</title>" in html
    html = build.render_page("Services", "<main>x</main>")
    assert "channel strategy &amp; enablement" in html


def test_pages_derive_from_site_json_in_order():
    assert build.PAGES == list(build.load_site()["pages"])


def test_unknown_stem_names_it_and_lists_known_ones():
    with pytest.raises(KeyError) as exc:
        build.render_page("Nope", "<main>x</main>")
    msg = str(exc.value)
    assert "Nope" in msg
    for stem in build.PAGES:
        assert stem in msg
