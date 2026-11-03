import numpy as np
import pytest
from skimage.color import rgb2lab

from color_engine.models import (
    ConfusionResult8,
    CvdProfile,
    CvdType,
    Palette3,
    PaletteEntry,
)
from color_engine.pipeline.filter_3_palette.extract_palette_3 import extract_palette_3
from color_engine.pipeline.filter_8_confusion.detect_confusion_8 import detect_confusion_8
from color_engine.rules.distance import ciede2000

RED = (220, 30, 30)
GREEN = (30, 150, 30)
BLUE = (40, 70, 200)
WHITE = (255, 255, 255)
FULL_DEUTAN = CvdProfile(CvdType.DEUTAN, 1.0)
THRESHOLD = 10.0


def _palette(*colors) -> Palette3:
    entries = []
    for position, rgb in enumerate(colors):
        lab = rgb2lab(np.array([[rgb]], dtype=np.uint8))[0, 0]
        entries.append(
            PaletteEntry(position + 1, rgb, tuple(float(v) for v in lab), 1 / len(colors))
        )
    return Palette3(tuple(entries))


def _bars(*colors) -> np.ndarray:
    return np.hstack([np.full((10, 10, 3), color, dtype=np.uint8) for color in colors])


def test_red_and_green_are_flagged_under_full_deutan():
    result = detect_confusion_8(_bars(RED, GREEN), _palette(RED, GREEN), FULL_DEUTAN, THRESHOLD)
    assert isinstance(result, ConfusionResult8)
    assert [(p.a_id, p.b_id) for p in result.pairs] == [(1, 2)]


def test_each_pair_reports_both_distances():
    palette = _palette(RED, GREEN)
    pair = detect_confusion_8(_bars(RED, GREEN), palette, FULL_DEUTAN, THRESHOLD).pairs[0]
    expected = float(ciede2000(np.array(palette.entries[0].lab), np.array(palette.entries[1].lab)))
    assert pair.original_distance == pytest.approx(expected)
    assert pair.original_distance > THRESHOLD
    assert 0 < pair.simulated_distance < THRESHOLD


def test_pair_distinct_under_both_views_is_not_flagged():
    result = detect_confusion_8(_bars(BLUE, WHITE), _palette(BLUE, WHITE), FULL_DEUTAN, THRESHOLD)
    assert result.pairs == ()
    assert result.groups == ()
    assert not result.mask.any()


def test_changing_the_threshold_changes_the_result():
    palette = _palette(RED, GREEN)
    image = _bars(RED, GREEN)
    simulated = detect_confusion_8(image, palette, FULL_DEUTAN, THRESHOLD).pairs[0]
    below = simulated.simulated_distance - 0.1
    assert detect_confusion_8(image, palette, FULL_DEUTAN, below).pairs == ()


def test_pair_is_not_flagged_when_the_original_distance_is_below_the_threshold():
    palette = _palette(RED, GREEN)
    assert detect_confusion_8(_bars(RED, GREEN), palette, FULL_DEUTAN, 100.0).pairs == ()


def test_no_cvd_flags_nothing():
    profile = CvdProfile(CvdType.NONE)
    result = detect_confusion_8(_bars(RED, GREEN), _palette(RED, GREEN), profile, THRESHOLD)
    assert result.pairs == ()


def test_mask_covers_flagged_colors_and_no_others():
    image = _bars(RED, GREEN, BLUE, WHITE)
    result = detect_confusion_8(image, _palette(RED, GREEN, BLUE, WHITE), FULL_DEUTAN, THRESHOLD)
    flagged = np.all(image == RED, axis=-1) | np.all(image == GREEN, axis=-1)
    assert result.mask.shape == image.shape[:2]
    assert np.array_equal(result.mask, flagged)


def test_color_index_labels_every_pixel_with_its_palette_id():
    image = _bars(RED, GREEN, BLUE)
    result = detect_confusion_8(image, _palette(RED, GREEN, BLUE), FULL_DEUTAN, THRESHOLD)
    assert result.color_index[0, 5] == 1
    assert result.color_index[0, 15] == 2
    assert result.color_index[0, 25] == 3


def test_palette_colors_in_one_lookup_bin_are_told_apart():
    first, second = (100, 100, 100), (103, 103, 103)
    image = _bars(first, second)
    result = detect_confusion_8(image, _palette(first, second), FULL_DEUTAN, THRESHOLD)
    assert result.color_index[0, 5] == 1
    assert result.color_index[0, 15] == 2


def test_linked_pairs_form_one_group_and_separate_pairs_form_two():
    linked = (150, 110, 30)
    result = detect_confusion_8(
        _bars(RED, GREEN, linked), _palette(RED, GREEN, linked), FULL_DEUTAN, 25.0
    )
    assert len(result.groups) == 1
    assert set(result.groups[0].palette_ids) == {1, 2, 3}

    others = ((230, 120, 170), (120, 170, 230))
    profile = CvdProfile(CvdType.ACHROMATOPSIA, 1.0)
    colors = (RED, GREEN, *others)
    groups = detect_confusion_8(_bars(*colors), _palette(*colors), profile, 5.0).groups
    assert [group.group_id for group in groups] == list(range(1, len(groups) + 1))
    assert sum(len(group.palette_ids) for group in groups) == len(
        {palette_id for group in groups for palette_id in group.palette_ids}
    )


def test_single_color_palette_has_no_pairs():
    result = detect_confusion_8(_bars(RED), _palette(RED), FULL_DEUTAN, THRESHOLD)
    assert result.pairs == ()


def test_filters_3_and_8_work_together():
    image = _bars(RED, GREEN, BLUE, WHITE)
    palette = extract_palette_3(image, 8)
    assert len(palette.entries) == 4
    result = detect_confusion_8(image, palette, FULL_DEUTAN, THRESHOLD)
    assert len(result.pairs) == 1
    flagged = np.all(image == RED, axis=-1) | np.all(image == GREEN, axis=-1)
    assert np.array_equal(result.mask, flagged)
