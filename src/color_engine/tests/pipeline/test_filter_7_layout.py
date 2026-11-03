import json
from pathlib import Path

import numpy as np
import pytest
from PIL import Image
from skimage.color import rgb2lab

from color_engine.models import (
    ImageType,
    LayoutResult7,
    Palette3,
    PaletteEntry,
    Region,
    RegionMap4,
    TextPiece,
    TextSet6,
)
from color_engine.pipeline.filter_3_palette.extract_palette_3 import extract_palette_3
from color_engine.pipeline.filter_4_regions.find_regions_4 import find_regions_4
from color_engine.pipeline.filter_6_text.read_text_6 import read_text_6
from color_engine.pipeline.filter_7_layout.analyze_layout_7 import analyze_layout_7
from color_engine.rules.distance import ciede2000

LABELED = Path(__file__).parent.parent / "data" / "labeled"
LABELS = json.loads((LABELED / "labels.json").read_text())["images"]
TYPES = {
    "chart": ImageType.CHART,
    "map": ImageType.MAP,
    "flat_graphic": ImageType.FLAT_GRAPHIC,
    "photograph": ImageType.PHOTOGRAPH,
}
_cache = {}


def _analyze(label) -> tuple[LayoutResult7, Palette3]:
    if label["file"] not in _cache:
        pixels = np.array(Image.open(LABELED / label["file"]).convert("RGB"))
        palette = extract_palette_3(pixels, 12)
        regions = find_regions_4(pixels, palette)
        _cache[label["file"]] = (
            analyze_layout_7(pixels, palette, regions, read_text_6(pixels)),
            palette,
        )
    return _cache[label["file"]]


def _nearest_palette_id(palette: Palette3, rgb) -> int:
    lab = rgb2lab(np.array([[rgb]], dtype=np.uint8))[0, 0]
    return min(palette.entries, key=lambda e: float(ciede2000(lab, np.array(e.lab)))).id


def test_sample_set_covers_every_type():
    assert {label["image_type"] for label in LABELS} == set(TYPES)


@pytest.mark.parametrize("label", LABELS, ids=lambda label: label["file"])
def test_each_sample_receives_its_type(label):
    result, _ = _analyze(label)
    assert isinstance(result.image_type, ImageType)
    assert result.image_type is TYPES[label["image_type"]]


@pytest.mark.parametrize(
    "label",
    [label for label in LABELS if label["image_type"] == "chart"],
    ids=lambda label: label["file"],
)
def test_chart_legend_matches_the_known_entries(label):
    result, palette = _analyze(label)
    expected = [(_nearest_palette_id(palette, rgb), text) for rgb, text in label["legend"]]
    assert [(entry.palette_id, entry.text) for entry in result.legend] == expected


@pytest.mark.parametrize(
    "label",
    [label for label in LABELS if label["image_type"] == "flat_graphic"],
    ids=lambda label: label["file"],
)
def test_graphic_with_no_legend_returns_an_empty_list(label):
    assert _analyze(label)[0].legend == ()


def _swatch(region_id, x, y, palette_id=1, size=20):
    area = size * size
    return Region(region_id, palette_id, x, y, size, size, area, x + size / 2, y + size / 2)


def _result(regions, pieces, width=600, height=400):
    pixels = np.full((height, width, 3), 255, dtype=np.uint8)
    lab = tuple(float(v) for v in rgb2lab(np.array([[[255, 255, 255]]], dtype=np.uint8))[0, 0])
    palette = Palette3((PaletteEntry(1, (255, 255, 255), lab, 1.0),))
    labels = np.zeros((height, width), dtype=np.int32)
    return analyze_layout_7(pixels, palette, RegionMap4(tuple(regions), labels), TextSet6(pieces))


def test_legend_column_with_text_on_the_right():
    regions = [_swatch(1, 500, 50, 2), _swatch(2, 500, 90, 3)]
    pieces = (TextPiece("Alpha", 530, 50, 50, 20, 0.9), TextPiece("Beta", 530, 90, 50, 20, 0.9))
    legend = _result(regions, pieces).legend
    assert [(e.palette_id, e.text) for e in legend] == [(2, "Alpha"), (3, "Beta")]
    assert (legend[0].x, legend[0].y, legend[0].width, legend[0].height) == (500, 50, 20, 20)


def test_legend_row_is_found():
    regions = [_swatch(1, 100, 350, 2), _swatch(2, 300, 350, 3)]
    pieces = (TextPiece("Alpha", 130, 350, 50, 20, 0.9), TextPiece("Beta", 330, 350, 50, 20, 0.9))
    assert [e.text for e in _result(regions, pieces).legend] == ["Alpha", "Beta"]


def test_text_on_the_left_is_found():
    regions = [_swatch(1, 500, 50, 2), _swatch(2, 500, 90, 3)]
    pieces = (TextPiece("Alpha", 430, 50, 60, 20, 0.9), TextPiece("Beta", 430, 90, 60, 20, 0.9))
    assert [e.text for e in _result(regions, pieces).legend] == ["Alpha", "Beta"]


def test_a_single_swatch_is_not_a_legend():
    pieces = (TextPiece("Alpha", 530, 50, 50, 20, 0.9),)
    assert _result([_swatch(1, 500, 50, 2)], pieces).legend == ()


def test_swatches_of_different_sizes_are_not_a_legend():
    regions = [_swatch(1, 500, 50, 2, size=20), _swatch(2, 500, 90, 3, size=60)]
    pieces = (TextPiece("Alpha", 530, 50, 50, 20, 0.9), TextPiece("Beta", 570, 110, 50, 20, 0.9))
    assert _result(regions, pieces).legend == ()


def test_swatches_with_no_nearby_text_are_not_a_legend():
    regions = [_swatch(1, 100, 50, 2), _swatch(2, 100, 90, 3)]
    pieces = (TextPiece("Far away", 400, 50, 50, 20, 0.9),)
    assert _result(regions, pieces).legend == ()
