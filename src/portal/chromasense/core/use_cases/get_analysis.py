"""Return the stored local analysis of an image."""

from dataclasses import dataclass

from chromasense.core.errors import ImageNotFound
from chromasense.core.models import ImageAnalysis
from chromasense.core.ports import ImageStore


@dataclass(frozen=True)
class GetAnalysisRequest:
    image_id: str


@dataclass(frozen=True)
class GetAnalysisResponse:
    image_id: str
    analysis: ImageAnalysis


class GetAnalysis:
    def __init__(self, store: ImageStore) -> None:
        self._store = store

    def execute(self, request: GetAnalysisRequest) -> GetAnalysisResponse:
        stored = self._store.load(request.image_id)
        if stored is None or stored.analysis is None:
            raise ImageNotFound(f"No image has the ID {request.image_id}")
        return GetAnalysisResponse(request.image_id, stored.analysis)
