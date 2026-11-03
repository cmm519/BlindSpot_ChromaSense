import numpy as np
import pytest
from skimage.color import rgb2lab

from color_engine.models import Palette3
from color_engine.pipeline.filter_3_palette.extract_palette_3 import extract_palette_3
from color_engine.rules.distance import ciede2000

KNOWN = [(200, 30, 30), (30, 140, 40), (40, 70, 190)]


def _flat_graphic(colors=KNOWN, widths=(50, 30, 20)) -> np.ndarray:
    bars = [np.full((40, w, 3), c, dtype=np.uint8) for c, w in zip(colors, widths, strict=True)]
    return np.hstack(bars)


def _lab(rgb) -> np.ndarray:
    return rgb2lab(np.array([[rgb]], dtype=np.uint8))[0, 0]


def test_three_color_graphic_yields_three_entries():
    assert len(extract_palette_3(_flat_graphic(), 8).entries) == 3


def test_palette_contains_each_known_color():
    palette = extract_palette_3(_flat_graphic(), 8)
    for color in KNOWN:
        nearest = min(float(ciede2000(_lab(color), np.array(e.lab))) for e in palette.entries)
        assert nearest < 1.0


def test_ids_run_from_one_in_descending_share():
    palette = extract_palette_3(_flat_graphic(), 8)
    assert isinstance(palette, Palette3)
    assert [entry.id for entry in palette.entries] == [1, 2, 3]
    assert [entry.rgb for entry in palette.entries] == KNOWN
    assert [round(entry.share, 2) for entry in palette.entries] == [0.5, 0.3, 0.2]


def test_repeated_runs_give_the_same_palette():
    rng = np.random.default_rng(1)
    noisy = rng.integers(0, 256, (200, 200, 3), dtype=np.uint8)
    assert extract_palette_3(noisy, 6) == extract_palette_3(noisy, 6)


def test_large_image_is_sampled_and_still_finds_the_colors():
    large = np.repeat(np.repeat(_flat_graphic(), 10, axis=0), 10, axis=1)
    assert [entry.rgb for entry in extract_palette_3(large, 8).entries] == KNOWN


def test_near_duplicate_shades_merge_into_one_entry():
    image = _flat_graphic([(200, 30, 30), (201, 31, 30), (40, 70, 190)])
    assert len(extract_palette_3(image, 8).entries) == 2


def test_color_count_limits_the_palette():
    assert len(extract_palette_3(_flat_graphic(), 2).entries) <= 2


def test_single_color_image_has_one_entry():
    palette = extract_palette_3(np.full((4, 4, 3), 90, dtype=np.uint8), 8)
    assert len(palette.entries) == 1
    assert palette.entries[0].share == pytest.approx(1.0)


def test_invalid_color_count_is_rejected():
    with pytest.raises(ValueError):
        extract_palette_3(_flat_graphic(), 0)
