"""Return the enhanced image at the original resolution."""

from dataclasses import dataclass
from io import BytesIO

from PIL import Image

from chromasense.core.errors import ImageNotFound, NoEnhancementForProfile
from chromasense.core.ports import ImageStore
from color_engine.models import CvdProfile, CvdType
from color_engine.pipeline.filter_1_decode.decode_1 import decode_1
from color_engine.pipeline.filter_8_confusion.detect_confusion_8 import detect_confusion_8
from color_engine.pipeline.filter_9_enhance.enhance_9 import enhance_9


@dataclass(frozen=True)
class ExportImageRequest:
    image_id: str
    profile: CvdProfile
    strength: float = 1.0


@dataclass(frozen=True)
class ExportImageResponse:
    png: bytes


class ExportImage:
    def __init__(self, store: ImageStore, threshold: float) -> None:
        self._store = store
        self._threshold = threshold

    def execute(self, request: ExportImageRequest) -> ExportImageResponse:
        stored = self._store.load(request.image_id)
        if stored is None or stored.analysis is None:
            raise ImageNotFound(f"No image has the ID {request.image_id}")
        if request.profile.type is CvdType.NONE:
            raise NoEnhancementForProfile("Exporting an enhanced image needs a CVD type")

        pixels = decode_1(stored.original).pixels
        confusion = detect_confusion_8(
            pixels, stored.analysis.palette, request.profile, self._threshold
        )
        enhanced = enhance_9(pixels, confusion, request.strength).pixels
        buffer = BytesIO()
        Image.fromarray(enhanced).save(buffer, format="PNG", compress_level=1)
        return ExportImageResponse(buffer.getvalue())
