"""Filter 2: make the copy of an image that analysis uses."""

from math import sqrt

import numpy as np
from PIL import Image

from color_engine.models import AnalysisImage2, DecodedImage1


def downscale_2(image: DecodedImage1, max_megapixels: float) -> AnalysisImage2:
    if max_megapixels <= 0:
        raise ValueError("max_megapixels must be positive")

    limit = max_megapixels * 1_000_000
    area = image.width * image.height
    if area <= limit:
        return AnalysisImage2(image.pixels.copy(), image.width, image.height, scale=1.0)

    ratio = sqrt(limit / area)
    width = max(1, int(image.width * ratio))
    height = max(1, int(image.height * ratio))
    resized = Image.fromarray(image.pixels).resize((width, height), Image.Resampling.LANCZOS)
    pixels = np.asarray(resized, dtype=np.uint8).copy()
    return AnalysisImage2(pixels, width, height, scale=width / image.width)
