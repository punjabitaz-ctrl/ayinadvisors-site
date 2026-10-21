"""Photography: registry, optimiser, <picture> rendering, build integration."""
import json
import re
from pathlib import Path

import pytest
from PIL import Image

import build
from conftest import ROOT, PAGES
from tools import images
from tools import optimize_images

WIDTHS = (480, 960, 1600)
BUDGET = 160_000


def _registry():
    return images.load_registry()


def _write_registry(path: Path, entries: list[dict]) -> Path:
    path.write_text(json.dumps({"images": entries}), encoding="utf-8")
    return path


def test_registry_requires_alt_or_decorative(tmp_path):
    for slug, e in _registry().items():
        assert (e.get("alt") or "").strip() or (e.get("decorative") is True and e.get("reason")), slug
    base = {"slug": "x", "source": "x.jpg", "focal": [0.5, 0.5], "pillar": "p", "crop": "3:2"}
    for bad in (base, {**base, "alt": "  "}, {**base, "decorative": True}):
        with pytest.raises(ValueError, match="x"):
            images.load_registry(_write_registry(tmp_path / "r.json", [bad]))
    ok = images.load_registry(_write_registry(tmp_path / "r.json", [{**base, "alt": "A thing"}]))
    assert ok["x"]["alt"] == "A thing"


def test_registry_sources_are_bare_file_names():
    for slug, e in _registry().items():
        assert Path(e["source"]).name == e["source"], slug
    assert set(_registry()) == {"us-night", "skyscrapers", "lightbulb"}


def test_every_registry_slug_has_all_three_files():
    for slug in _registry():
        for w in WIDTHS:
            assert (ROOT / "assets" / "img" / f"{slug}-{w}.webp").is_file(), (slug, w)


def test_no_1600_file_exceeds_160kb():
    for slug in _registry():
        assert (ROOT / "assets" / "img" / f"{slug}-1600.webp").stat().st_size <= BUDGET, slug


def test_generated_files_match_registry_dimensions():
    for slug in _registry():
        w, h = images.dimensions(slug, 1600)
        with Image.open(ROOT / "assets" / "img" / f"{slug}-1600.webp") as im:
            assert im.size == (w, h), slug
            assert not im.getexif(), f"{slug} still carries EXIF"


def test_render_picture_has_srcset_sizes_dimensions_and_alt():
    html = images.render_picture("us-night", "(min-width: 900px) 520px, 100vw")
    assert html.startswith("<picture>") and html.endswith("</picture>")
    for w in WIDTHS:
        assert f"assets/img/us-night-{w}.webp {w}w" in html
    assert 'sizes="(min-width: 900px) 520px, 100vw"' in html
    w, h = images.dimensions("us-night", 1600)
    assert f'width="{w}"' in html and f'height="{h}"' in html
    assert 'decoding="async"' in html and 'loading="lazy"' in html
    assert f'alt="{_registry()["us-night"]["alt"]}"' in html


def test_render_picture_class_and_decorative(tmp_path):
    assert 'class="photo-img"' in images.render_picture("lightbulb", "100vw", cls="photo-img")
    reg = _write_registry(tmp_path / "r.json", [{
        "slug": "d", "source": "d.jpg", "focal": [0.5, 0.5], "pillar": "p", "crop": "3:2",
        "decorative": True, "reason": "purely ornamental"}])
    html = images.render_picture("d", "100vw", registry=images.load_registry(reg))
    assert 'alt=""' in html


def test_above_the_fold_images_are_not_lazy():
    assert 'loading="eager"' in images.render_picture("lightbulb", "100vw", loading="eager")
    assert "lazy" not in images.render_picture("lightbulb", "100vw", loading="eager")
    html = build.expand_image_slots('<image-slot slug="lightbulb" sizes="100vw" loading="eager"></image-slot>')
    assert 'loading="eager"' in html


def test_unknown_image_slot_fails_the_build():
    with pytest.raises(KeyError, match="no-such-photo"):
        build.expand_image_slots('<p><image-slot slug="no-such-photo" sizes="100vw"></image-slot></p>')
    with pytest.raises(KeyError):
        images.render_picture("no-such-photo", "100vw")


def test_slot_without_sizes_is_rejected():
    with pytest.raises(ValueError, match="sizes"):
        build.expand_image_slots('<image-slot slug="lightbulb"></image-slot>')


def test_expand_leaves_other_html_untouched():
    src = "<p>hello</p>\n<!-- c -->"
    assert build.expand_image_slots(src) == src


PLACEMENTS = {"index": "us-night", "About": "skyscrapers", "BizCheck": "lightbulb"}


@pytest.mark.parametrize("stem,slug", PLACEMENTS.items())
def test_each_placement_renders_one_picture(stem, slug):
    frag = (ROOT / "templates" / "pages" / f"{stem}.body.frag").read_text(encoding="utf-8")
    assert f'slug="{slug}"' in frag
    html = (ROOT / f"{stem}.html").read_text(encoding="utf-8")
    assert html.count("<picture>") == 1 and f"assets/img/{slug}-1600.webp" in html
    assert "image-slot" not in html


@pytest.mark.parametrize("stem", [s for s in PAGES if s not in PLACEMENTS])
def test_other_pages_have_no_photos(stem):
    assert "<picture" not in (ROOT / f"{stem}.html").read_text(encoding="utf-8")


def test_render_all_expands_slots():
    for stem, html in build.render_all().items():
        assert "<image-slot" not in html, stem


def test_no_background_image_under_text():
    """Photos are <img> elements beside text; CSS never paints one behind it.

    The only allowed `url(` in a background is the inline SVG chevron on <select>.
    """
    texts = {n: (ROOT / "assets" / n).read_text(encoding="utf-8") for n in ("styles.css", "theme.css")}
    for s in PAGES:
        body, head_extra, body_scripts = build.page_parts(s)
        texts[s] = head_extra + body + body_scripts
    for name, text in texts.items():
        for m in re.finditer(r"""url\(\s*\\?["']?([^)"'\\]{0,40})""", text):
            assert m.group(1).startswith("data:image/svg+xml"), f"{name}: url({m.group(1)}"


# ---- optimiser ---------------------------------------------------------

def _src(tmp_path, name="a.jpg", size=(2400, 1800), exif=True):
    d = tmp_path / "src"
    d.mkdir(exist_ok=True)
    im = Image.merge("RGB", [Image.radial_gradient("L").resize(size)] * 3)
    if exif:
        e = Image.Exif()
        e[0x010F] = "SecretCam"
        im.save(d / name, exif=e)
    else:
        im.save(d / name)
    return d


def _reg(tmp_path, source="a.jpg", crop="3:2"):
    return images.load_registry(_write_registry(tmp_path / "r.json", [{
        "slug": "t", "source": source, "alt": "test", "focal": [0.5, 0.5], "pillar": "p", "crop": crop}]))


def test_optimizer_writes_three_widths_strips_exif_and_never_upscales(tmp_path):
    out = tmp_path / "out"
    reg = _reg(tmp_path)
    optimize_images.optimize(_src(tmp_path, size=(1200, 900)), out, reg)
    sizes = {}
    for w in WIDTHS:
        with Image.open(out / f"t-{w}.webp") as im:
            sizes[w] = im.size
            assert not im.getexif()
    assert sizes[480] == (480, 320) and sizes[960] == (960, 640)
    assert sizes[1600] == (1200, 800)  # source is only 1200 wide: capped, not upscaled


def test_optimizer_fails_on_missing_source(tmp_path):
    with pytest.raises(optimize_images.OptimizeError, match="a.jpg"):
        optimize_images.optimize(tmp_path / "empty", tmp_path / "out", _reg(tmp_path))
    assert optimize_images.main([str(tmp_path / "empty")]) != 0


def test_optimizer_fails_when_file_cannot_fit_budget(tmp_path):
    with pytest.raises(optimize_images.OptimizeError, match="budget"):
        optimize_images.optimize(_src(tmp_path), tmp_path / "out", _reg(tmp_path), budget=1000)


def test_optimizer_cli_requires_source_dir(capsys):
    assert optimize_images.main([]) == 2
