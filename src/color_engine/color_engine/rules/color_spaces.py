"""sRGB transfer function, with values in the range 0 to 1."""

import numpy as np
from numpy.typing import NDArray


def srgb_to_linear(pixels: NDArray) -> NDArray[np.float64]:
    """Linearize sRGB values. A uint8 array is first scaled from 0-255 to 0-1."""
    values = np.asarray(pixels)
    encoded = values / 255.0 if values.dtype == np.uint8 else values.astype(np.float64)
    return np.where(encoded <= 0.04045, encoded / 12.92, ((encoded + 0.055) / 1.055) ** 2.4)


def linear_to_srgb(pixels: NDArray) -> NDArray[np.float64]:
    """Encode linear RGB values as sRGB, clipping them to the range 0 to 1."""
    linear = np.clip(np.asarray(pixels, dtype=np.float64), 0.0, 1.0)
    return np.where(linear <= 0.0031308, linear * 12.92, 1.055 * linear ** (1 / 2.4) - 0.055)
