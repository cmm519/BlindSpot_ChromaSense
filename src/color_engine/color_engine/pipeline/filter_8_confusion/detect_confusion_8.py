"""Filter 8: flag the palette colors that a CVD profile makes confusable."""

from functools import cache
from itertools import combinations

import numpy as np
from numpy.typing import NDArray
from skimage.color import rgb2lab

from color_engine.models import (
    ConfusablePair,
    ConfusionGroup,
    ConfusionResult8,
    CvdProfile,
    Palette3,
)
from color_engine.rules.distance import ciede2000
from color_engine.rules.simulation import simulate

_BIN_SHIFT = 2  # 256 levels / 4 = 64 bins per channel
_BINS = 64


def detect_confusion_8(
    pixels: NDArray, palette: Palette3, profile: CvdProfile, threshold: float
) -> ConfusionResult8:
    pairs = _flag_pairs(palette, profile, threshold)
    color_index = _assign_pixels(np.asarray(pixels), palette)
    flagged_ids = sorted({palette_id for pair in pairs for palette_id in (pair.a_id, pair.b_id)})
    return ConfusionResult8(
        pairs=pairs,
        groups=_connected_groups(pairs),
        mask=np.isin(color_index, flagged_ids),
        color_index=color_index,
    )


def _flag_pairs(
    palette: Palette3, profile: CvdProfile, threshold: float
) -> tuple[ConfusablePair, ...]:
    entries = palette.entries
    if len(entries) < 2:
        return ()
    rgb = np.array([[entry.rgb for entry in entries]], dtype=np.uint8)
    simulated_labs = rgb2lab(simulate(rgb, profile))[0]
    original_labs = np.array([entry.lab for entry in entries])

    flagged = []
    for a, b in combinations(range(len(entries)), 2):
        original = float(ciede2000(original_labs[a], original_labs[b]))
        simulated = float(ciede2000(simulated_labs[a], simulated_labs[b]))
        if simulated < threshold and original > threshold:
            flagged.append(ConfusablePair(entries[a].id, entries[b].id, original, simulated))
    return tuple(flagged)


def _connected_groups(pairs: tuple[ConfusablePair, ...]) -> tuple[ConfusionGroup, ...]:
    parent: dict[int, int] = {}

    def find(palette_id: int) -> int:
        parent.setdefault(palette_id, palette_id)
        while parent[palette_id] != palette_id:
            parent[palette_id] = parent[parent[palette_id]]
            palette_id = parent[palette_id]
        return palette_id

    for pair in pairs:
        parent[find(pair.a_id)] = find(pair.b_id)

    members: dict[int, list[int]] = {}
    for palette_id in sorted(parent):
        members.setdefault(find(palette_id), []).append(palette_id)
    ordered = sorted(members.values(), key=lambda ids: ids[0])
    return tuple(
        ConfusionGroup(group_id=position + 1, palette_ids=tuple(ids))
        for position, ids in enumerate(ordered)
    )


@cache
def _bin_center_labs() -> NDArray:
    centers = np.arange(_BINS, dtype=np.uint8) * (1 << _BIN_SHIFT) + (1 << (_BIN_SHIFT - 1))
    red, green, blue = np.meshgrid(centers, centers, centers, indexing="ij")
    return rgb2lab(np.stack([red, green, blue], axis=-1).reshape(1, -1, 3))[0]


def _assign_pixels(pixels: NDArray, palette: Palette3) -> NDArray[np.uint8]:
    """Label each pixel with the palette ID of its nearest color, through a lookup table."""
    ids = np.array([entry.id for entry in palette.entries], dtype=np.uint8)
    labs = np.array([entry.lab for entry in palette.entries])
    distances = ((_bin_center_labs()[:, np.newaxis, :] - labs[np.newaxis, :, :]) ** 2).sum(axis=-1)
    table = ids[np.argmin(distances, axis=1)]

    palette_bins = _bin_keys(np.array([entry.rgb for entry in palette.entries], dtype=np.uint8))
    table[palette_bins] = ids
    index = table[_bin_keys(pixels)]

    unique_bins, counts = np.unique(palette_bins, return_counts=True)
    shared_bins = unique_bins[counts > 1]
    if shared_bins.size:
        needs_exact = np.isin(_bin_keys(pixels), shared_bins)
        exact_labs = rgb2lab(pixels[needs_exact][np.newaxis, :, :])[0]
        nearest = ((exact_labs[:, np.newaxis, :] - labs[np.newaxis, :, :]) ** 2).sum(axis=-1)
        index[needs_exact] = ids[np.argmin(nearest, axis=1)]
    return index


def _bin_keys(rgb: NDArray) -> NDArray[np.int32]:
    binned = rgb.astype(np.int32) >> _BIN_SHIFT
    return (binned[..., 0] * _BINS + binned[..., 1]) * _BINS + binned[..., 2]
