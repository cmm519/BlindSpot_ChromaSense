"""Filter 4: find the connected regions of each palette color."""

from functools import cache

import cv2
import numpy as np
from numpy.typing import NDArray
from skimage.color import rgb2lab

from color_engine.models import Palette3, Region, RegionMap4

_MIN_REGION_PIXELS = 16
_CLEANING_KERNEL = np.ones((3, 3), dtype=np.uint8)
_BIN_SHIFT = 2  # 256 levels / 4 = 64 bins per channel
_BINS = 64


def find_regions_4(pixels: NDArray, palette: Palette3) -> RegionMap4:
    image = np.asarray(pixels)
    color_index = _nearest_palette_ids(image, palette)
    found: list[tuple[int, int, int, int, int, int, float, float, int]] = []
    per_color_labels: dict[int, NDArray] = {}

    for entry in palette.entries:
        mask = (color_index == entry.id).astype(np.uint8)
        cleaned = cv2.morphologyEx(mask, cv2.MORPH_OPEN, _CLEANING_KERNEL)
        count, labels, stats, centroids = cv2.connectedComponentsWithStats(cleaned, connectivity=8)
        per_color_labels[entry.id] = labels
        for label in range(1, count):
            x, y, width, height, area = (int(value) for value in stats[label])
            if area >= _MIN_REGION_PIXELS:
                center_x, center_y = (float(value) for value in centroids[label])
                found.append((y, x, entry.id, width, height, area, center_x, center_y, label))

    found.sort()
    region_labels = np.zeros(image.shape[:2], dtype=np.int32)
    regions = []
    for position, item in enumerate(found):
        y, x, palette_id, width, height, area, center_x, center_y, label = item
        region_id = position + 1
        window = (slice(y, y + height), slice(x, x + width))
        region_labels[window][per_color_labels[palette_id][window] == label] = region_id
        regions.append(Region(region_id, palette_id, x, y, width, height, area, center_x, center_y))
    return RegionMap4(tuple(regions), region_labels)


@cache
def _bin_center_labs() -> NDArray:
    centers = np.arange(_BINS, dtype=np.uint8) * (1 << _BIN_SHIFT) + (1 << (_BIN_SHIFT - 1))
    red, green, blue = np.meshgrid(centers, centers, centers, indexing="ij")
    return rgb2lab(np.stack([red, green, blue], axis=-1).reshape(1, -1, 3))[0]


def _nearest_palette_ids(pixels: NDArray, palette: Palette3) -> NDArray[np.uint8]:
    ids = np.array([entry.id for entry in palette.entries], dtype=np.uint8)
    labs = np.array([entry.lab for entry in palette.entries])
    distances = ((_bin_center_labs()[:, np.newaxis, :] - labs[np.newaxis, :, :]) ** 2).sum(axis=-1)
    table = ids[np.argmin(distances, axis=1)]

    palette_bins = _bin_keys(np.array([entry.rgb for entry in palette.entries], dtype=np.uint8))
    table[palette_bins] = ids
    pixel_bins = _bin_keys(pixels)
    index = table[pixel_bins]

    unique_bins, counts = np.unique(palette_bins, return_counts=True)
    shared_bins = unique_bins[counts > 1]
    if shared_bins.size:
        needs_exact = np.isin(pixel_bins, shared_bins)
        exact_labs = rgb2lab(pixels[needs_exact][np.newaxis, :, :])[0]
        nearest = ((exact_labs[:, np.newaxis, :] - labs[np.newaxis, :, :]) ** 2).sum(axis=-1)
        index[needs_exact] = ids[np.argmin(nearest, axis=1)]
    return index


def _bin_keys(rgb: NDArray) -> NDArray[np.int32]:
    binned = rgb.astype(np.int32) >> _BIN_SHIFT
    return (binned[..., 0] * _BINS + binned[..., 1]) * _BINS + binned[..., 2]
