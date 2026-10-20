from conftest import PAGES, baseline_html


def test_every_page_has_a_baseline():
    for stem in PAGES:
        assert "<nav class=\"nav surface-inverse\"" in baseline_html(stem), stem
