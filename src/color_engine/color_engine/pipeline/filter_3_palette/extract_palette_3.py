"""Filter 3: find the dominant colors of an image with k-means in CIELAB."""

import numpy as np
from numpy.typing import NDArray
from skimage.color import lab2rgb, rgb2lab
from sklearn.cluster import KMeans

from color_engine.models import Palette3, PaletteEntry
from color_engine.rules.distance import ciede2000

_MAX_SAMPLE = 50_000
_MERGE_DISTANCE = 2.3
_RANDOM_STATE = 0


def extract_palette_3(pixels: NDArray, color_count: int) -> Palette3:
    if color_count < 1:
        raise ValueError("color_count must be at least 1")

    colors, weights = np.unique(_sample(pixels), axis=0, return_counts=True)
    labs = rgb2lab(colors[np.newaxis, :, :].astype(np.uint8))[0]
    clusters = min(color_count, len(colors))
    model = KMeans(n_clusters=clusters, n_init=4, random_state=_RANDOM_STATE)
    assignment = model.fit_predict(labs, sample_weight=weights)

    used = np.unique(assignment)
    cluster_weights = np.array([weights[assignment == label].sum() for label in used], dtype=float)
    centers = np.array(
        [
            np.average(labs[assignment == label], axis=0, weights=weights[assignment == label])
            for label in used
        ]
    )
    return _build_palette(*_merge_close_clusters(centers, cluster_weights))


def _sample(pixels: NDArray) -> NDArray:
    flat = np.asarray(pixels).reshape(-1, 3)
    if len(flat) <= _MAX_SAMPLE:
        return flat
    chosen = np.random.default_rng(_RANDOM_STATE).choice(len(flat), _MAX_SAMPLE, replace=False)
    return flat[chosen]


def _merge_close_clusters(centers: NDArray, weights: NDArray) -> tuple[NDArray, NDArray]:
    centers, weights = centers.copy(), weights.copy()
    while len(centers) > 1:
        first, second = np.triu_indices(len(centers), k=1)
        distances = ciede2000(centers[first], centers[second])
        closest = int(np.argmin(distances))
        if distances[closest] >= _MERGE_DISTANCE:
            break
        keep, drop = int(first[closest]), int(second[closest])
        total = weights[keep] + weights[drop]
        centers[keep] = (centers[keep] * weights[keep] + centers[drop] * weights[drop]) / total
        weights[keep] = total
        centers = np.delete(centers, drop, axis=0)
        weights = np.delete(weights, drop)
    return centers, weights


def _build_palette(centers: NDArray, weights: NDArray) -> Palette3:
    order = sorted(
        range(len(centers)), key=lambda i: (-weights[i], *np.round(centers[i], 6).tolist())
    )
    rgb = np.rint(lab2rgb(centers[np.newaxis, :, :])[0] * 255).astype(np.uint8)
    total = weights.sum()
    return Palette3(
        tuple(
            PaletteEntry(
                id=position + 1,
                rgb=tuple(int(channel) for channel in rgb[index]),
                lab=tuple(float(value) for value in centers[index]),
                share=float(weights[index] / total),
            )
            for position, index in enumerate(order)
        )
    )
