import pytest

from tools.contrast import composite, ratio, solve_min_darken


def test_known_ratios():
    assert ratio("#c6a15c", "#ffffff") == pytest.approx(2.43, abs=0.01)
    assert ratio("#061325", "#c6a15c") == pytest.approx(7.67, abs=0.01)
    assert ratio("#72787e", "#061325") == pytest.approx(4.17, abs=0.01)


def test_ratio_is_symmetric_and_bounded():
    assert ratio("#000000", "#ffffff") == pytest.approx(21.0)
    assert ratio("#123456", "#ffffff") == ratio("#ffffff", "#123456")
    assert ratio("#abcdef", "#abcdef") == pytest.approx(1.0)


def test_composite_matches_direct_computation():
    navy, cream = "#061325", "#faf7f0"
    mixed = composite(cream, 0.5, navy)
    # channel-wise blend, rounded
    expect = "#" + "".join(
        f"{round(int(cream[i:i + 2], 16) * 0.5 + int(navy[i:i + 2], 16) * 0.5):02x}" for i in (1, 3, 5)
    )
    assert mixed == expect
    assert ratio(mixed, navy) < ratio(cream, navy)
    assert composite(cream, 1.0, navy) == cream
    assert composite(cream, 0.0, navy) == navy


def test_solve_min_darken_is_minimal():
    bg = "#efdecd"
    out = solve_min_darken("#c6a15c", [bg], 4.5)
    assert ratio(out, bg) >= 4.5
    # one 1% lighter step must fail (i.e. the answer is the lightest passing one)
    lighter = composite(out, 0.99, "#ffffff")
    assert ratio(lighter, bg) < 4.5 or lighter == out


def test_solve_min_darken_returns_input_when_already_passing():
    assert solve_min_darken("#061325", ["#ffffff"], 4.5) == "#061325"


def test_solve_must_pass_every_background():
    bgs = ["#ffffff", "#e8dcc8"]
    out = solve_min_darken("#5d6c7b", bgs, 4.5)
    assert all(ratio(out, b) >= 4.5 for b in bgs)
