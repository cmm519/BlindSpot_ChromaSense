import numpy as np
import pytest
from PIL import Image, ImageDraw
from skimage.color import rgb2lab

from color_engine.models import Palette3, PaletteEntry, RegionMap4, ShapeSet5
from color_engine.pipeline.filter_4_regions.find_regions_4 import find_regions_4
from color_engine.pipeline.filter_5_shapes.find_shapes_5 import find_shapes_5

WHITE, RED, GREEN, BLUE = (255, 255, 255), (220, 30, 30), (30, 150, 30), (40, 70, 200)
PALETTE_IDS = {WHITE: 1, RED: 2, GREEN: 3, BLUE: 4}


def _palette() -> Palette3:
    entries = []
    for rgb, palette_id in PALETTE_IDS.items():
        lab = rgb2lab(np.array([[rgb]], dtype=np.uint8))[0, 0]
        entries.append(PaletteEntry(palette_id, rgb, tuple(float(v) for v in lab), 0.25))
    return Palette3(tuple(entries))


def _regions(draw_shapes, size=(400, 200)) -> RegionMap4:
    image = Image.new("RGB", size, WHITE)
    draw_shapes(ImageDraw.Draw(image))
    return find_regions_4(np.array(image), _palette())


def _three_shapes(draw) -> None:
    draw.ellipse([20, 40, 120, 140], fill=RED)
    draw.rectangle([150, 50, 250, 130], fill=GREEN)
    draw.polygon([(280, 150), (380, 150), (330, 50)], fill=BLUE)


def test_known_circle_rectangle_and_triangle_have_kind_location_and_palette_id():
    result = find_shapes_5(_regions(_three_shapes))
    assert isinstance(result, ShapeSet5)
    by_kind = {shape.kind: shape for shape in result.shapes}
    assert set(by_kind) == {"circle", "rectangle", "triangle"}

    circle = by_kind["circle"]
    assert circle.palette_id == PALETTE_IDS[RED]
    assert (circle.x, circle.y) == pytest.approx((20, 40), abs=3)
    assert (circle.center_x, circle.center_y) == pytest.approx((70, 90), abs=3)

    rectangle = by_kind["rectangle"]
    assert rectangle.palette_id == PALETTE_IDS[GREEN]
    assert (rectangle.x, rectangle.y, rectangle.width, rectangle.height) == pytest.approx(
        (150, 50, 101, 81), abs=2
    )

    triangle = by_kind["triangle"]
    assert triangle.palette_id == PALETTE_IDS[BLUE]
    assert (triangle.center_x, triangle.center_y) == pytest.approx((330, 117), abs=4)


def test_background_is_not_a_shape():
    shapes = find_shapes_5(_regions(_three_shapes)).shapes
    assert PALETTE_IDS[WHITE] not in [shape.palette_id for shape in shapes]


def test_irregular_region_is_other():
    points = [(20, 20), (150, 30), (90, 60), (170, 150), (60, 110), (30, 170)]
    shapes = find_shapes_5(_regions(lambda draw: draw.polygon(points, fill=RED))).shapes
    assert [shape.kind for shape in shapes] == ["other"]


def test_ellipse_that_is_not_round_is_not_a_circle():
    shapes = find_shapes_5(_regions(lambda draw: draw.ellipse([20, 60, 220, 120], fill=RED))).shapes
    assert [shape.kind for shape in shapes] != ["circle"]


def test_small_circle_is_still_a_circle():
    shapes = find_shapes_5(_regions(lambda draw: draw.ellipse([50, 50, 74, 74], fill=RED))).shapes
    assert [shape.kind for shape in shapes] == ["circle"]


def test_each_shape_has_its_own_item_and_sequential_id():
    def two_rectangles(draw):
        draw.rectangle([10, 10, 60, 60], fill=RED)
        draw.rectangle([100, 10, 150, 60], fill=RED)

    shapes = find_shapes_5(_regions(two_rectangles)).shapes
    assert [shape.id for shape in shapes] == [1, 2]
    assert [shape.kind for shape in shapes] == ["rectangle", "rectangle"]


def test_image_with_only_background_has_no_shapes():
    assert find_shapes_5(_regions(lambda draw: None)).shapes == ()
