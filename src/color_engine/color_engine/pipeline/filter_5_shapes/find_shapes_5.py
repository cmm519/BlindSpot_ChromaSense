"""Filter 5: describe the regions that form a distinct shape."""

from math import pi

import cv2
import numpy as np
from numpy.typing import NDArray

from color_engine.models import Region, RegionMap4, Shape, ShapeSet5

_MIN_SHAPE_PIXELS = 64
_POLYGON_TOLERANCE = 0.03
_RECTANGLE_FILL = 0.85
_CIRCLE_CIRCULARITY = 0.80
_CIRCLE_ASPECT_LIMIT = 1.2
_PADDING = 2


def find_shapes_5(regions: RegionMap4) -> ShapeSet5:
    height, width = regions.labels.shape
    shapes: list[Shape] = []
    for region in regions.regions:
        if region.area < _MIN_SHAPE_PIXELS or _touches_all_edges(region, width, height):
            continue
        mask = _region_mask(regions.labels, region)
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        if not contours:
            continue
        contour = max(contours, key=cv2.contourArea)
        center_x, center_y = _center(contour, region)
        shapes.append(
            Shape(
                id=len(shapes) + 1,
                kind=_classify(contour, mask, region),
                palette_id=region.palette_id,
                x=region.x,
                y=region.y,
                width=region.width,
                height=region.height,
                center_x=center_x,
                center_y=center_y,
            )
        )
    return ShapeSet5(tuple(shapes))


def _touches_all_edges(region: Region, width: int, height: int) -> bool:
    return (
        region.x == 0
        and region.y == 0
        and region.x + region.width == width
        and region.y + region.height == height
    )


def _region_mask(labels: NDArray, region: Region) -> NDArray[np.uint8]:
    """Return the region as a padded mask, so its contour never touches the mask's border."""
    window = labels[region.y : region.y + region.height, region.x : region.x + region.width]
    mask = (window == region.id).astype(np.uint8) * 255
    return cv2.copyMakeBorder(mask, _PADDING, _PADDING, _PADDING, _PADDING, cv2.BORDER_CONSTANT)


def _center(contour: NDArray, region: Region) -> tuple[float, float]:
    moments = cv2.moments(contour)
    if moments["m00"] == 0:
        return float(region.center_x), float(region.center_y)
    return (
        moments["m10"] / moments["m00"] + region.x - _PADDING,
        moments["m01"] / moments["m00"] + region.y - _PADDING,
    )


def _classify(contour: NDArray, mask: NDArray, region: Region) -> str:
    perimeter = cv2.arcLength(contour, closed=True)
    area = cv2.contourArea(contour)
    if perimeter == 0 or area == 0:
        return "other"

    corners = len(cv2.approxPolyDP(contour, _POLYGON_TOLERANCE * perimeter, closed=True))
    if corners == 3:
        return "triangle"
    if corners == 4 and area / (region.width * region.height) >= _RECTANGLE_FILL:
        return "rectangle"
    if _is_circle(area, perimeter, mask, region):
        return "circle"
    return "other"


def _is_circle(area: float, perimeter: float, mask: NDArray, region: Region) -> bool:
    aspect = max(region.width, region.height) / min(region.width, region.height)
    if aspect > _CIRCLE_ASPECT_LIMIT or 4 * pi * area / perimeter**2 < _CIRCLE_CIRCULARITY:
        return False
    radius = (region.width + region.height) / 4
    circles = cv2.HoughCircles(
        cv2.GaussianBlur(mask, (5, 5), 0),
        cv2.HOUGH_GRADIENT,
        dp=1,
        minDist=max(1.0, radius),
        param1=100,
        param2=max(5.0, radius * 0.4),
        minRadius=max(1, int(radius * 0.8)),
        maxRadius=int(radius * 1.2) + 1,
    )
    return circles is not None
