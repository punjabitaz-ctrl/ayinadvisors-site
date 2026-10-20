"""The pixel contrast measurer must tell passing text from failing text (synthetic images, no browser)."""
from PIL import Image

from a11y_browser.pixel_contrast import ratio, required_ratio, worst_ratio


def _pair(text_rgb, bg_rgb):
    shown = Image.new("RGB", (40, 20), bg_rgb)
    hidden = Image.new("RGB", (40, 20), bg_rgb)
    for x in range(10, 30):
        for y in range(5, 15):
            shown.putpixel((x, y), text_rgb)
    return shown, hidden


def test_dark_text_on_white_passes_and_pale_grey_fails():
    rects = [(0, 0, 40, 20, 0, 0, 0, 1.0)]
    ok = worst_ratio(*_pair((0, 0, 0), (255, 255, 255)), rects)
    assert ok > 15
    pale = worst_ratio(*_pair((200, 200, 200), (255, 255, 255)), [(0, 0, 40, 20, 200, 200, 200, 1.0)])
    assert pale < required_ratio(16, 400)


def test_invisible_text_is_reported_as_unmeasurable_or_one_to_one():
    same = Image.new("RGB", (10, 10), (250, 250, 250))
    assert worst_ratio(same, same.copy(), [(0, 0, 10, 10, 0, 0, 0, 1.0)]) is None


def test_ratio_and_large_text_threshold():
    assert round(ratio((0, 0, 0), (255, 255, 255)), 1) == 21.0
    assert required_ratio(24, 400) == 3.0 and required_ratio(18.7, 700) == 3.0 and required_ratio(16, 700) == 4.5
