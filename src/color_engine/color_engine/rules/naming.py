"""Nearest color names from the dataset bundled with the package."""

import colorsys
import csv
from functools import cache
from importlib import resources

import numpy as np
from skimage.color import rgb2lab

from color_engine.models import ColorInfo
from color_engine.rules.distance import ciede2000


@cache
def _load_dataset() -> tuple[tuple[str, ...], tuple[str, ...], np.ndarray]:
    source = resources.files("color_engine").joinpath("data/named_colors.csv")
    with source.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    names = tuple(row["name"] for row in rows)
    families = tuple(row["family"] for row in rows)
    labs = np.array([[float(row["l"]), float(row["a"]), float(row["b"])] for row in rows])
    return names, families, labs


class ColorNamer:
    """Describes an RGB color by its values and the nearest color in the dataset."""

    def describe(self, rgb: tuple[int, int, int]) -> ColorInfo:
        red, green, blue = (int(channel) for channel in rgb)
        if not all(0 <= channel <= 255 for channel in (red, green, blue)):
            raise ValueError("RGB channels must be between 0 and 255")

        names, families, labs = _load_dataset()
        pixel = np.array([[[red, green, blue]]], dtype=np.uint8)
        lab = rgb2lab(pixel)[0, 0]
        nearest = int(np.argmin(ciede2000(labs, lab)))

        return ColorInfo(
            name=names[nearest],
            hex=f"#{red:02X}{green:02X}{blue:02X}",
            rgb=(red, green, blue),
            hsl=_to_hsl(red, green, blue),
            family=families[nearest],
        )


def _to_hsl(red: int, green: int, blue: int) -> tuple[int, int, int]:
    hue, lightness, saturation = colorsys.rgb_to_hls(red / 255, green / 255, blue / 255)
    return round(hue * 360) % 360, round(saturation * 100), round(lightness * 100)
