"""Pattern overlays that tell confusable color groups apart without relying on color."""

from collections.abc import Sequence

import cv2
import numpy as np
from numpy.typing import NDArray

from color_engine.rules.color_spaces import srgb_to_linear

_PATTERNS = ("hatching", "dots", "crosshatch", "outline")
_REC709_LUMINANCE = np.array([0.2126, 0.7152, 0.0722])
_MIN_SPACING = 6
_SPACING_DIVISOR = 30


def pattern_label(position: int) -> str:
    """Return the text label of the pattern for a group, by its zero-based position."""
    name = _PATTERNS[position % len(_PATTERNS)]
    return f"{name}, wide" if position >= len(_PATTERNS) else name


def apply_overlay(
    pixels: NDArray, mask: NDArray[np.bool_], groups: Sequence[NDArray[np.bool_]]
) -> NDArray[np.uint8]:
    """Draw one pattern per group, inside the mask only, and return a new array.

    Each item in `groups` is a boolean array that marks the pixels of one group.
    """
    result = np.array(pixels, dtype=np.uint8)
    for position, group in enumerate(groups):
        area = np.logical_and(group, mask)
        if not area.any():
            continue
        drawn = _draw_pattern(area, position)
        result[drawn] = _ink_for(result[area])
    return result


def _draw_pattern(area: NDArray[np.bool_], position: int) -> NDArray[np.bool_]:
    height, width = area.shape
    wide = position >= len(_PATTERNS)
    spacing = max(_MIN_SPACING, min(height, width) // _SPACING_DIVISOR) * (2 if wide else 1)
    thickness = max(1, spacing // (16 if wide else 8))
    name = _PATTERNS[position % len(_PATTERNS)]
    if name == "outline":
        return _outline(area, thickness)

    canvas = np.zeros((height, width), dtype=np.uint8)
    if name == "dots":
        for y in range(spacing // 2, height, spacing):
            for x in range(spacing // 2, width, spacing):
                cv2.circle(canvas, (x, y), max(1, spacing // 5), 255, -1)
    else:
        _diagonals(canvas, spacing, thickness, rising=True)
        if name == "crosshatch":
            _diagonals(canvas, spacing, thickness, rising=False)
    area_mask = area.astype(np.uint8) * 255
    return cv2.bitwise_and(canvas, area_mask) > 0


def _diagonals(canvas: NDArray, spacing: int, thickness: int, rising: bool) -> None:
    height, width = canvas.shape
    for offset in range(-height, width + height, spacing):
        if rising:
            cv2.line(canvas, (offset, height), (offset + height, 0), 255, thickness)
        else:
            cv2.line(canvas, (offset, 0), (offset + height, height), 255, thickness)


def _outline(area: NDArray[np.bool_], thickness: int) -> NDArray[np.bool_]:
    inner = area.copy()
    for _ in range(thickness):
        shrunk = inner.copy()
        shrunk[1:, :] &= inner[:-1, :]
        shrunk[:-1, :] &= inner[1:, :]
        shrunk[:, 1:] &= inner[:, :-1]
        shrunk[:, :-1] &= inner[:, 1:]
        inner = shrunk
    return area & ~inner


def _ink_for(colors: NDArray) -> tuple[int, int, int]:
    """Return black or white, whichever has the higher contrast with the group's mean color."""
    mean = np.rint(colors.mean(axis=0)).astype(np.uint8)
    luminance = float(srgb_to_linear(mean) @ _REC709_LUMINANCE)
    white_contrast = 1.05 / (luminance + 0.05)
    black_contrast = (luminance + 0.05) / 0.05
    return (255, 255, 255) if white_contrast >= black_contrast else (0, 0, 0)
