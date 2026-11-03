import numpy as np
import pytest
from skimage.color import rgb2lab

from color_engine.models import Palette3, PaletteEntry, RegionMap4
from color_engine.pipeline.filter_4_regions.find_regions_4 import find_regions_4

WHITE, RED, BLUE = (255, 255, 255), (220, 30, 30), (40, 70, 200)


def _palette(*colors) -> Palette3:
    entries = []
    for position, rgb in enumerate(colors):
        lab = rgb2lab(np.array([[rgb]], dtype=np.uint8))[0, 0]
        entries.append(PaletteEntry(position + 1, rgb, tuple(float(v) for v in lab), 0.1))
    return Palette3(tuple(entries))


def _known_graphic() -> np.ndarray:
    image = np.full((100, 200, 3), WHITE, dtype=np.uint8)
    image[10:40, 20:60] = RED
    image[60:90, 20:80] = RED
    image[10:50, 120:180] = BLUE
    return image


def _by_color(result: RegionMap4, palette_id: int):
    return [region for region in result.regions if region.palette_id == palette_id]


def test_reports_the_correct_number_of_regions_for_each_color():
    result = find_regions_4(_known_graphic(), _palette(WHITE, RED, BLUE))
    assert isinstance(result, RegionMap4)
    assert len(_by_color(result, 1)) == 1
    assert len(_by_color(result, 2)) == 2
    assert len(_by_color(result, 3)) == 1


def test_locations_sizes_and_centers_match_known_values():
    result = find_regions_4(_known_graphic(), _palette(WHITE, RED, BLUE))
    first, second = _by_color(result, 2)
    assert (first.x, first.y, first.width, first.height) == (20, 10, 40, 30)
    assert first.area == 1200
    assert first.center_x == pytest.approx(39.5, abs=1)
    assert first.center_y == pytest.approx(24.5, abs=1)
    assert (second.x, second.y, second.width, second.height) == (20, 60, 60, 30)
    blue = _by_color(result, 3)[0]
    assert (blue.x, blue.y, blue.width, blue.height) == (120, 10, 60, 40)


def test_labels_hold_region_ids():
    result = find_regions_4(_known_graphic(), _palette(WHITE, RED, BLUE))
    blue = _by_color(result, 3)[0]
    assert result.labels.shape == (100, 200)
    assert result.labels[30, 150] == blue.id
    assert (result.labels == blue.id).sum() == blue.area
    assert [region.id for region in result.regions] == list(range(1, len(result.regions) + 1))


def test_regions_under_sixteen_pixels_are_dropped():
    image = np.full((50, 50, 3), WHITE, dtype=np.uint8)
    image[5:8, 5:8] = RED
    image[20:30, 20:30] = RED
    result = find_regions_4(image, _palette(WHITE, RED))
    assert len(_by_color(result, 2)) == 1


def test_thin_stray_lines_are_cleaned_away():
    image = np.full((50, 50, 3), WHITE, dtype=np.uint8)
    image[25, 5:45] = RED
    result = find_regions_4(image, _palette(WHITE, RED))
    assert _by_color(result, 2) == []


def test_nearby_shades_join_their_nearest_palette_color():
    image = np.full((40, 40, 3), WHITE, dtype=np.uint8)
    image[10:30, 10:30] = (216, 34, 28)
    result = find_regions_4(image, _palette(WHITE, RED))
    assert _by_color(result, 2)[0].area == 400


def test_palette_colors_in_one_lookup_bin_are_told_apart():
    first, second = (100, 100, 100), (103, 103, 103)
    image = np.hstack([np.full((20, 20, 3), c, dtype=np.uint8) for c in (first, second)])
    result = find_regions_4(image, _palette(first, second))
    assert len(result.regions) == 2
