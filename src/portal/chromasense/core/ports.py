"""Interfaces that Application Core needs, and that outer parts implement."""

from collections.abc import Sequence
from datetime import datetime
from typing import Protocol

from numpy.typing import NDArray

from chromasense.core.models import (
    AiAnswer,
    AiRead,
    AiUsage,
    ImageAnalysis,
    ImageRecord,
    Interpretation,
    StoredImage,
)
from color_engine.models import ImageType, Palette3


class ImageStore(Protocol):
    def save(self, record: ImageRecord, original: bytes, working: NDArray) -> None: ...

    def load(self, image_id: str) -> StoredImage | None: ...

    def save_analysis(self, image_id: str, analysis: ImageAnalysis) -> None: ...

    def delete_expired(self, now: datetime) -> int: ...


class InterpretationCache(Protocol):
    def get(self, image_hash: str, now: datetime) -> Interpretation | None: ...

    def put(self, interpretation: Interpretation) -> None: ...

    def delete_expired(self, now: datetime) -> int: ...


class AiUsageLedger(Protocol):
    def record(
        self, session_id: str, ip_address: str, estimated_cost: float, now: datetime
    ) -> None: ...

    def usage(self, session_id: str, ip_address: str, now: datetime) -> AiUsage: ...

    def total_cost(self, now: datetime) -> float: ...


class VisionReader(Protocol):
    def read(self, image: NDArray, palette: Palette3, image_type: ImageType) -> AiRead: ...

    def ask(
        self, image: NDArray, palette: Palette3, items: Sequence[object], question: str
    ) -> AiAnswer: ...


class Clock(Protocol):
    def now(self) -> datetime: ...
