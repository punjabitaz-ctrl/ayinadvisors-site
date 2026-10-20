"""The parity net must catch single-attribute chrome edits (mutation tests, in memory only)."""
import re
import pytest
import build
from parity import page_facts

_RENDERED = build.render_all()

SCRIPT_SITE = '<script src="assets/site.js"></script>'


def _sub(old, new, count=1):
    return lambda h: h.replace(old, new, count)


def _regex(pattern, repl, flags=0):
    return lambda h: re.sub(pattern, repl, h, count=1, flags=flags)


def _move_script_ahead(h):
    m = re.search(re.escape(SCRIPT_SITE) + r"\s*(<script>.*?</script>)", h, re.S)
    assert m, "no inline script follows site.js"
    return h[: m.start()] + m.group(1) + "\n" + SCRIPT_SITE + h[m.end():]


# (name, page, mutator)
MUTATIONS = [
    ("html lang", "About", _sub('<html lang="en">', '<html lang="fr">')),
    ("remove doctype", "About", _sub("<!DOCTYPE html>", "")),
    ("body class+style", "About", _sub("<body>", '<body class="x" style="display:none">')),
    ("remove viewport meta", "About", _regex(r'<meta name="viewport"[^>]*>', "")),
    ("change charset", "About", _sub('charset="UTF-8"', 'charset="ISO-8859-1"')),
    ("remove logo aria-label", "About", _sub(' aria-label="AYiN Advisors home"', "")),
    ("remove data-magnetic from nav CTA", "About",
     _regex(r'(<span class="nav-cta"><a [^>]*?) data-magnetic', r"\1")),
    ("remove btn-label wrapper in nav CTA", "About",
     _regex(r'(<span class="nav-cta"><a [^>]*>)<span class="btn-label">(.*?)</span></a>', r"\1\2</a>")),
    ("remove nav-toggle aria-label", "About", _sub(' aria-label="Menu"', "")),
    ("remove nav-toggle aria-controls", "About", _sub(' aria-controls="mobile-menu"', "")),
    ("remove primary nav label", "About", _sub(' aria-label="Primary"', "")),
    ("drawer back to a div", "About", _sub('<nav class="mobile-drawer surface-inverse"', '<div class="mobile-drawer surface-inverse"')),
    ("drop md-cta class from drawer", "About", _sub(' class="md-cta"', "")),
    ("drop gold class from drawer", "About",
     _regex(r'(<nav class="mobile-drawer surface-inverse"[^>]*>.*?<a href="BizCheck.html") class="gold"', r"\1", re.S)),
    ("hidden on nav.nav", "About", _sub('<nav class="nav surface-inverse" aria-label="Primary">', '<nav class="nav surface-inverse" aria-label="Primary" hidden>')),
    ("style on .nav-links", "About", _sub('<div class="nav-links">', '<div class="nav-links" style="display:none">')),
    ("footer class", "About", _sub('<footer class="footer surface-inverse">', '<footer class="footer surface-inverse dark">')),
    ("remove footer logo style", "About", _sub(' style="margin-bottom:0"', "")),
    ("defer on site.js", "About", _sub(SCRIPT_SITE, '<script src="assets/site.js" defer></script>')),
    ("move inline script ahead of site.js", "BizCheck", _move_script_ahead),
    # Same mutations on BizCheck, whose CTA/active state differs.
    ("BizCheck: remove data-magnetic from nav CTA", "BizCheck",
     _regex(r'(<span class="nav-cta"><a [^>]*?) data-magnetic', r"\1")),
    ("BizCheck: html lang", "BizCheck", _sub('<html lang="en">', '<html lang="fr">')),
    ("BizCheck: defer on site.js", "BizCheck", _sub(SCRIPT_SITE, '<script src="assets/site.js" defer></script>')),
]


@pytest.mark.parametrize("name,stem,mutate", MUTATIONS, ids=[m[0] for m in MUTATIONS])
def test_net_catches_mutation(name, stem, mutate):
    original = _RENDERED[stem]
    mutated = mutate(original)
    assert mutated != original, f"mutation {name!r} did not change the page (no-op)"
    assert page_facts(mutated) != page_facts(original), f"parity net missed: {name}"
