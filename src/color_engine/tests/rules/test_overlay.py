import numpy as np
import pytest

from color_engine.rules.overlay import apply_overlay, pattern_label

SIZE = 120


def _two_groups():
    pixels = np.full((SIZE, SIZE, 3), 240, dtype=np.uint8)
    first = np.zeros((SIZE, SIZE), dtype=bool)
    second = np.zeros((SIZE, SIZE), dtype=bool)
    first[10:60, 10:60] = True
    second[10:60, 70:110] = True
    pixels[first] = (220, 30, 30)
    pixels[second] = (30, 150, 30)
    return pixels, first, second


def _changed(before, after):
    return np.any(before != after, axis=-1)


def test_each_group_has_a_different_pattern_and_nothing_changes_outside_the_mask():
    pixels, first, second = _two_groups()
    mask = first | second
    result = apply_overlay(pixels, mask, [first, second])
    changed = _changed(pixels, result)

    assert not changed[~mask].any()
    assert changed[first].any() and changed[second].any()
    first_pattern = changed[10:60, 10:50]
    second_pattern = changed[10:60, 70:110]
    assert not np.array_equal(first_pattern, second_pattern)
    assert pattern_label(0) != pattern_label(1)


def test_input_is_not_modified_and_a_new_array_returns():
    pixels, first, second = _two_groups()
    before = pixels.copy()
    result = apply_overlay(pixels, first | second, [first, second])
    assert result is not pixels
    assert np.array_equal(pixels, before)


def test_group_area_outside_the_mask_is_not_drawn():
    pixels, first, second = _two_groups()
    result = apply_overlay(pixels, first, [first, second])
    assert not _changed(pixels, result)[second].any()


def test_labels_follow_group_order_and_become_wide_after_four():
    labels = [pattern_label(position) for position in range(6)]
    assert labels == [
        "hatching",
        "dots",
        "crosshatch",
        "outline",
        "hatching, wide",
        "dots, wide",
    ]


@pytest.mark.parametrize("position", range(6))
def test_every_pattern_changes_pixels_only_inside_its_group(position):
    pixels, first, _ = _two_groups()
    groups = [np.zeros_like(first)] * position + [first]
    result = apply_overlay(pixels, first, groups)
    changed = _changed(pixels, result)
    assert changed[first].any()
    assert not changed[~first].any()


def test_wide_pattern_differs_from_the_narrow_one():
    pixels, first, _ = _two_groups()
    empty = np.zeros_like(first)
    narrow = _changed(pixels, apply_overlay(pixels, first, [first]))
    wide = _changed(pixels, apply_overlay(pixels, first, [empty] * 4 + [first]))
    assert not np.array_equal(narrow, wide)
    assert wide.sum() < narrow.sum()


def test_outline_leaves_the_center_of_the_group_unchanged():
    pixels, first, _ = _two_groups()
    empty = np.zeros_like(first)
    changed = _changed(pixels, apply_overlay(pixels, first, [empty] * 3 + [first]))
    assert changed[10, 30]
    assert not changed[35, 35]


@pytest.mark.parametrize(
    ("color", "ink"),
    [((250, 240, 60), (0, 0, 0)), ((20, 20, 90), (255, 255, 255))],
)
def test_ink_is_whichever_of_black_or_white_has_higher_contrast(color, ink):
    pixels = np.full((SIZE, SIZE, 3), color, dtype=np.uint8)
    area = np.ones((SIZE, SIZE), dtype=bool)
    result = apply_overlay(pixels, area, [area])
    drawn = result[_changed(pixels, result)]
    assert (drawn == ink).all()
