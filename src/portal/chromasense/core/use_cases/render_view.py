"""Return a preview of an image: original, simulated, enhanced, or overlaid."""

from dataclasses import dataclass
from io import BytesIO

import numpy as np
from numpy.typing import NDArray
from PIL import Image

from chromasense.core.errors import ImageNotFound, NoEnhancementForProfile
from chromasense.core.ports import ImageStore
from color_engine.models import ConfusionResult8, CvdProfile, CvdType, DecodedImage1
from color_engine.pipeline.filter_2_downscale.downscale_2 import downscale_2
from color_engine.pipeline.filter_8_confusion.detect_confusion_8 import detect_confusion_8
from color_engine.pipeline.filter_9_enhance.enhance_9 import enhance_9
from color_engine.rules.overlay import apply_overlay
from color_engine.rules.simulation import simulate

VIEWS = ("original", "simulated", "enhanced", "overlay")
_PREVIEW_MEGAPIXELS = 2.0


@dataclass(frozen=True)
class RenderViewRequest:
    image_id: str
    view: str
    profile: CvdProfile
    strength: float = 1.0


@dataclass(frozen=True)
class RenderViewResponse:
    png: bytes


class RenderView:
    def __init__(self, store: ImageStore, threshold: float) -> None:
        self._store = store
        self._threshold = threshold

    def execute(self, request: RenderViewRequest) -> RenderViewResponse:
        if request.view not in VIEWS:
            raise ValueError(f"unknown view {request.view}")
        stored = self._store.load(request.image_id)
        if stored is None or stored.analysis is None:
            raise ImageNotFound(f"No image has the ID {request.image_id}")

        pixels = self._view_pixels(stored, request)
        height, width = pixels.shape[:2]
        preview = downscale_2(DecodedImage1(pixels, width, height), _PREVIEW_MEGAPIXELS)
        return RenderViewResponse(_to_png(preview.pixels))

    def _view_pixels(self, stored, request: RenderViewRequest) -> NDArray:
        if request.view == "original":
            return stored.working
        if request.view == "simulated":
            return simulate(stored.working, request.profile)
        if request.profile.type is CvdType.NONE:
            raise NoEnhancementForProfile("This view needs a CVD type")

        confusion = detect_confusion_8(
            stored.working, stored.analysis.palette, request.profile, self._threshold
        )
        enhanced = enhance_9(stored.working, confusion, request.strength).pixels
        if request.view == "enhanced":
            return enhanced
        return apply_overlay(enhanced, confusion.mask, _group_masks(confusion))


def _group_masks(confusion: ConfusionResult8) -> list[NDArray[np.bool_]]:
    return [np.isin(confusion.color_index, group.palette_ids) for group in confusion.groups]


def _to_png(pixels: NDArray) -> bytes:
    buffer = BytesIO()
    Image.fromarray(pixels).save(buffer, format="PNG", compress_level=1)
    return buffer.getvalue()
