"""Filter 7: classify the image type and find a legend, with measured features and written rules."""

from math import pi

import cv2
import numpy as np
from numpy.typing import NDArray
from skimage.color import rgb2lab

from color_engine.models import (
    ImageType,
    LayoutResult7,
    LegendEntry7,
    Palette3,
    Region,
    RegionMap4,
    TextPiece,
    TextSet6,
)

# Image features are measured on a copy no longer than this, to keep analysis fast.
_FEATURE_MAX_SIDE = 800
_HISTOGRAM_BINS = 16
_HISTOGRAM_MIN_SHARE = 0.0005
_COVERAGE_LAB_DISTANCE = 6.0

# Image type rules. The values come from the measurements on tests/data/labeled/.
_PHOTO_MAX_COVERAGE = 0.80
_PHOTO_MIN_OCCUPIED_BINS = 0.02
_PHOTO_MIN_REGIONS = 100
_AXIS_MIN_LENGTH_SHARE = 0.5
_AXIS_ANGLE_TOLERANCE = pi / 90
_CHART_MIN_TEXT_PIECES = 1
_MAP_MIN_IRREGULAR_REGIONS = 2
_MAP_MIN_REGION_SHARE = 0.05
_MAP_MAX_REGION_SHARE = 0.5
# Share of its box that a regular shape fills: a rectangle, a circle, and a triangle.
_REGULAR_FILLS = ((1.0, 0.03), (pi / 4, 0.012), (0.5, 0.03))

# Legend rules.
_SWATCH_MAX_IMAGE_SHARE = 0.015
_SWATCH_MAX_ASPECT = 2.5
_SWATCH_SIZE_TOLERANCE = 0.3
_ALIGN_TOLERANCE_IN_SWATCHES = 0.5
_TEXT_MAX_GAP_IN_SWATCHES = 3.0
_MIN_LEGEND_ENTRIES = 2


def analyze_layout_7(
    pixels: NDArray, palette: Palette3, regions: RegionMap4, text: TextSet6
) -> LayoutResult7:
    image = np.asarray(pixels)
    legend = _find_legend(regions, text, image.shape[0] * image.shape[1])
    return LayoutResult7(_classify(image, palette, regions, text), legend)


def _classify(image: NDArray, palette: Palette3, regions: RegionMap4, text: TextSet6) -> ImageType:
    small = _feature_copy(image)
    if _looks_photographic(small, palette, regions):
        return ImageType.PHOTOGRAPH
    if len(text.items) >= _CHART_MIN_TEXT_PIECES and _has_axes(small):
        return ImageType.CHART
    image_area = image.shape[0] * image.shape[1]
    if _irregular_region_count(regions, image_area) >= _MAP_MIN_IRREGULAR_REGIONS:
        return ImageType.MAP
    return ImageType.FLAT_GRAPHIC


def _feature_copy(image: NDArray) -> NDArray:
    longest = max(image.shape[:2])
    if longest <= _FEATURE_MAX_SIDE:
        return image
    scale = _FEATURE_MAX_SIDE / longest
    return cv2.resize(image, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)


def _looks_photographic(small: NDArray, palette: Palette3, regions: RegionMap4) -> bool:
    labs = rgb2lab(small)
    centers = np.array([entry.lab for entry in palette.entries])
    distances = np.linalg.norm(labs[:, :, np.newaxis, :] - centers, axis=-1).min(axis=-1)
    coverage = float((distances <= _COVERAGE_LAB_DISTANCE).mean())

    histogram = cv2.calcHist(
        [small], [0, 1, 2], None, [_HISTOGRAM_BINS] * 3, [0, 256, 0, 256, 0, 256]
    )
    minimum = _HISTOGRAM_MIN_SHARE * small.shape[0] * small.shape[1]
    occupied = float((histogram > minimum).sum()) / histogram.size
    return (
        coverage < _PHOTO_MAX_COVERAGE
        and occupied >= _PHOTO_MIN_OCCUPIED_BINS
        and len(regions.regions) >= _PHOTO_MIN_REGIONS
    )


def _has_axes(small: NDArray) -> bool:
    """A chart has a long horizontal line and a long vertical line."""
    edges = cv2.Canny(cv2.cvtColor(small, cv2.COLOR_RGB2GRAY), 50, 150)
    height, width = edges.shape
    return _line_at_angle(edges, int(width * _AXIS_MIN_LENGTH_SHARE), pi / 2) and _line_at_angle(
        edges, int(height * _AXIS_MIN_LENGTH_SHARE), 0.0
    )


def _line_at_angle(edges: NDArray, votes: int, angle: float) -> bool:
    lines = cv2.HoughLines(edges, 1, pi / 180, max(votes, 1))
    if lines is None:
        return False
    return bool((np.abs(lines[:, 0, 1] - angle) <= _AXIS_ANGLE_TOLERANCE).any())


def _irregular_region_count(regions: RegionMap4, image_area: int) -> int:
    """Count large regions that are not a rectangle, circle, or triangle, as in a map."""
    return sum(
        _MAP_MIN_REGION_SHARE * image_area <= region.area < _MAP_MAX_REGION_SHARE * image_area
        and not _has_regular_fill(region.area / (region.width * region.height))
        for region in regions.regions
    )


def _has_regular_fill(fill: float) -> bool:
    return any(abs(fill - regular) <= tolerance for regular, tolerance in _REGULAR_FILLS)


def _find_legend(regions: RegionMap4, text: TextSet6, image_area: int) -> tuple[LegendEntry7, ...]:
    swatches = [
        region
        for region in regions.regions
        if _could_be_swatch(region, image_area) and not _overlaps_text(region, text)
    ]
    best: tuple[LegendEntry7, ...] = ()
    for side in ("right", "left"):
        labeled = [
            (region, piece)
            for region in swatches
            if (piece := _text_beside(region, text, side)) is not None
        ]
        for line in _aligned_lines(labeled):
            if len(line) >= _MIN_LEGEND_ENTRIES and len(line) > len(best):
                best = tuple(
                    LegendEntry7(
                        region.palette_id,
                        piece.text,
                        region.x,
                        region.y,
                        region.width,
                        region.height,
                    )
                    for region, piece in line
                )
    return best


def _could_be_swatch(region: Region, image_area: int) -> bool:
    aspect = max(region.width, region.height) / min(region.width, region.height)
    return region.area <= _SWATCH_MAX_IMAGE_SHARE * image_area and aspect <= _SWATCH_MAX_ASPECT


def _overlaps_text(region: Region, text: TextSet6) -> bool:
    return any(
        region.x < piece.x + piece.width
        and piece.x < region.x + region.width
        and region.y < piece.y + piece.height
        and piece.y < region.y + region.height
        for piece in text.items
    )


def _text_beside(region: Region, text: TextSet6, side: str) -> TextPiece | None:
    """Return the nearest text on the given side of a swatch, at the same height."""
    best = None
    best_gap = _TEXT_MAX_GAP_IN_SWATCHES * region.width
    for piece in text.items:
        center = piece.y + piece.height / 2
        if not region.y - region.height / 2 <= center <= region.y + 1.5 * region.height:
            continue
        if side == "right":
            gap = piece.x - (region.x + region.width)
        else:
            gap = region.x - (piece.x + piece.width)
        if 0 <= gap <= best_gap:
            best, best_gap = piece, gap
    return best


def _aligned_lines(
    labeled: list[tuple[Region, TextPiece]],
) -> list[list[tuple[Region, TextPiece]]]:
    """Group swatches of similar size into columns and rows."""
    lines = []
    for key, order in (("x", "y"), ("y", "x")):
        for anchor, _ in labeled:
            line = [
                item
                for item in labeled
                if _similar_size(anchor, item[0]) and _aligned(anchor, item[0], key)
            ]
            line.sort(key=lambda item: getattr(item[0], order))
            lines.append(line)
    return lines


def _similar_size(first: Region, second: Region) -> bool:
    limit = 1 + _SWATCH_SIZE_TOLERANCE
    return max(first.width, second.width) <= limit * min(first.width, second.width) and max(
        first.height, second.height
    ) <= limit * min(first.height, second.height)


def _aligned(first: Region, second: Region, key: str) -> bool:
    size = first.width if key == "x" else first.height
    return abs(getattr(first, key) - getattr(second, key)) <= _ALIGN_TOLERANCE_IN_SWATCHES * size
