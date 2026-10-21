"""The reason on a needs-review entry must describe the page it is on (a ripples graphic only where one exists)."""
import json

import pytest
from bs4 import BeautifulSoup

import build
from conftest import ROOT

TEMPLATE_PAGES = ("Services", "partnerships", "ai-solutions", "digital-presence")
ENTRIES = json.loads((ROOT / "tests" / "a11y_review.json").read_text(encoding="utf-8"))["items"]


@pytest.fixture(scope="module")
def has_ripples():
    return {stem: bool(BeautifulSoup(html, "html.parser").select("svg.ripples")) for stem, html in build.render_all().items()}


def test_ripples_are_named_only_on_pages_that_carry_them(has_ripples):
    """Checked for the pages written in Sprint 2; Projects and 404 carry older boilerplate that is out of this sprint's scope."""
    bad = [(e["page"], e["selector"]) for e in ENTRIES
           if e["page"] in TEMPLATE_PAGES and "ripples" in e["reason"] and not has_ripples[e["page"]]]
    assert not bad, f"reasons that blame a ripples graphic on a page without one: {bad}"


PAGEHEAD_TEXT = ("h1", ".pagehead .lead", ".pagehead .eyebrow.on-navy")


@pytest.mark.parametrize("stem", TEMPLATE_PAGES)
def test_pagehead_entries_name_the_ring_motif_that_overlaps_the_text(stem):
    """The graphic behind the page-head text on these pages is the `.ph-motif` ring motif (an aria-hidden SVG)."""
    mine = [e for e in ENTRIES if e["page"] == stem and e["selector"] in PAGEHEAD_TEXT]
    assert {e["selector"] for e in mine} == set(PAGEHEAD_TEXT)
    for e in mine:
        assert ".ph-motif" in e["reason"], (stem, e["selector"])
        assert "decorative ripples" not in e["reason"]


@pytest.mark.parametrize("stem", ("Services", "ai-solutions", "digital-presence"))
def test_no_photograph_is_blamed_on_a_page_without_one(stem):
    assert "<img" not in build.render_all()[stem]
    for e in ENTRIES:
        if e["page"] == stem:
            assert "photograph" not in e["reason"] and "photography" not in e["reason"], (stem, e["selector"])
