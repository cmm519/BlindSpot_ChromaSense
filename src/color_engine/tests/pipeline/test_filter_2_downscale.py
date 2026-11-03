import numpy as np
import pytest

from color_engine.models import AnalysisImage2, DecodedImage1
from color_engine.pipeline.filter_2_downscale.downscale_2 import downscale_2


def _decoded(width: int, height: int) -> DecodedImage1:
    return DecodedImage1(np.full((height, width, 3), 90, dtype=np.uint8), width, height)


def test_twenty_megapixels_becomes_at_most_twelve_and_keeps_the_input():
    image = _decoded(5000, 4000)
    before = image.pixels.copy()

    result = downscale_2(image, 12)

    assert isinstance(result, AnalysisImage2)
    assert result.width * result.height <= 12_000_000
    assert result.width * result.height > 11_900_000
    assert result.pixels.shape == (result.height, result.width, 3)
    assert result.width / result.height == pytest.approx(5000 / 4000, abs=1e-3)
    assert result.scale == pytest.approx(result.width / 5000)
    assert image.pixels.shape == (4000, 5000, 3)
    assert np.array_equal(image.pixels, before)


def test_image_within_the_limit_is_not_enlarged():
    image = _decoded(100, 50)
    result = downscale_2(image, 12)
    assert (result.width, result.height, result.scale) == (100, 50, 1.0)
    assert np.array_equal(result.pixels, image.pixels)


def test_result_does_not_share_memory_with_the_input():
    image = _decoded(10, 10)
    assert not np.shares_memory(downscale_2(image, 12).pixels, image.pixels)


def test_extreme_aspect_ratio_keeps_at_least_one_pixel():
    result = downscale_2(_decoded(4000, 1), 0.001)
    assert result.width >= 1 and result.height == 1


@pytest.mark.parametrize("limit", [0, -1])
def test_non_positive_limit_is_rejected(limit):
    with pytest.raises(ValueError):
        downscale_2(_decoded(2, 2), limit)
