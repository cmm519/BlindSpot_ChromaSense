"""Run confusion detection and enhancement again for a changed profile."""

from dataclasses import dataclass

from chromasense.core.errors import ImageNotFound
from chromasense.core.models import PatternGroup
from chromasense.core.ports import ImageStore
from chromasense.core.use_cases.process_upload import to_pattern_groups
from color_engine.models import ConfusablePair, CvdProfile, CvdType
from color_engine.pipeline.filter_3_palette.extract_palette_3 import extract_palette_3
from color_engine.pipeline.filter_8_confusion.detect_confusion_8 import detect_confusion_8
from color_engine.pipeline.filter_9_enhance.enhance_9 import enhance_9


@dataclass(frozen=True)
class ReanalyzeRequest:
    image_id: str
    profile: CvdProfile


@dataclass(frozen=True)
class ReanalyzeResponse:
    image_id: str
    pairs: tuple[ConfusablePair, ...]
    groups: tuple[PatternGroup, ...]
    remaining_pair_count: int | None
    enhancement_needed: bool


class ReanalyzeForProfile:
    def __init__(self, store: ImageStore, threshold: float, color_count: int = 12) -> None:
        self._store = store
        self._threshold = threshold
        self._color_count = color_count

    def execute(self, request: ReanalyzeRequest) -> ReanalyzeResponse:
        stored = self._store.load(request.image_id)
        if stored is None or stored.analysis is None:
            raise ImageNotFound(f"No image has the ID {request.image_id}")
        if request.profile.type is CvdType.NONE:
            return ReanalyzeResponse(request.image_id, (), (), None, False)

        confusion = detect_confusion_8(
            stored.working, stored.analysis.palette, request.profile, self._threshold
        )
        enhanced = enhance_9(stored.working, confusion).pixels
        new_palette = extract_palette_3(enhanced, self._color_count)
        remaining = detect_confusion_8(enhanced, new_palette, request.profile, self._threshold)
        return ReanalyzeResponse(
            image_id=request.image_id,
            pairs=confusion.pairs,
            groups=to_pattern_groups(confusion.groups),
            remaining_pair_count=len(remaining.pairs),
            enhancement_needed=bool(confusion.pairs),
        )
