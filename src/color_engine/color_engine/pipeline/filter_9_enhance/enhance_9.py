"""Filter 9: separate confusable colors by lightness, changing only pixels in the mask.

docs/enhancement-evaluation.md records why this method was selected.
"""

import numpy as np
from numpy.typing import NDArray
from skimage.color import lab2rgb, rgb2lab

from color_engine.models import ConfusionResult8, EnhancedImage9

METHOD = "lightness separation"
_LIGHTNESS_MIN = 15.0
_LIGHTNESS_MAX = 90.0
_LIGHTNESS_GAP = 22.0


def enhance_9(
    pixels: NDArray, confusion: ConfusionResult8, strength: float = 1.0
) -> EnhancedImage9:
    if not 0.0 <= strength <= 1.0:
        raise ValueError("strength must be between 0 and 1")

    result = np.array(pixels, dtype=np.uint8)
    if strength == 0.0 or not confusion.mask.any():
        return EnhancedImage9(result, METHOD)

    shifts = _lightness_shifts(result, confusion)
    labs = rgb2lab(result[confusion.mask][np.newaxis, :, :])[0]
    labs[:, 0] += strength * shifts[confusion.color_index[confusion.mask]]
    recolored = lab2rgb(labs[np.newaxis, :, :])[0]
    result[confusion.mask] = np.rint(recolored * 255).astype(np.uint8)
    return EnhancedImage9(result, METHOD)


def _lightness_shifts(pixels: NDArray, confusion: ConfusionResult8) -> NDArray[np.float64]:
    """Return the lightness change for each palette ID, as an array indexed by that ID."""
    lightness = _mean_lightness(pixels, confusion.color_index)
    grouped = {palette_id for group in confusion.groups for palette_id in group.palette_ids}
    taken = [float(lightness[i]) for i in np.flatnonzero(~np.isnan(lightness)) if i not in grouped]

    shifts = np.zeros(lightness.shape, dtype=np.float64)
    for group in confusion.groups:
        members = sorted(group.palette_ids, key=lambda palette_id: lightness[palette_id])
        current = [float(lightness[palette_id]) for palette_id in members]
        targets = _choose_targets(current, taken)
        for palette_id, now, target in zip(members, current, targets, strict=True):
            shifts[palette_id] = target - now
        taken.extend(targets)
    return shifts


def _mean_lightness(pixels: NDArray, color_index: NDArray) -> NDArray[np.float64]:
    """Return the mean color's CIELAB lightness per palette ID, or NaN for an absent ID."""
    flat_index = color_index.ravel()
    counts = np.bincount(flat_index, minlength=256)
    lightness = np.full(counts.shape, np.nan)
    present = np.flatnonzero(counts)
    means = np.column_stack(
        [
            np.bincount(flat_index, weights=pixels[..., channel].ravel(), minlength=256)[present]
            / counts[present]
            for channel in range(3)
        ]
    )
    colors = np.rint(means).astype(np.uint8)[np.newaxis, :, :]
    lightness[present] = rgb2lab(colors)[0, :, 0]
    return lightness


def _choose_targets(current: list[float], taken: list[float]) -> list[float]:
    """Space a group evenly, avoiding other colors first, then moving as little as possible."""
    count = len(current)
    gap = min(_LIGHTNESS_GAP, (_LIGHTNESS_MAX - _LIGHTNESS_MIN) / max(count - 1, 1))
    best_key = None
    best_targets = current
    for start in np.arange(_LIGHTNESS_MIN, _LIGHTNESS_MAX + 1.0):
        targets = [float(start) + position * gap for position in range(count)]
        if targets[-1] > _LIGHTNESS_MAX:
            break
        conflicts = sum(abs(target - other) < gap for target in targets for other in taken)
        movement = sum(abs(target - now) for target, now in zip(targets, current, strict=True))
        if best_key is None or (conflicts, movement) < best_key:
            best_key = (conflicts, movement)
            best_targets = targets
    return best_targets
