"""Get one AI read of an image, and flag each item against the local analysis."""

from dataclasses import dataclass
from datetime import timedelta

from chromasense.core.errors import AiUnavailable, ImageNotFound
from chromasense.core.models import Interpretation
from chromasense.core.policy.ai_limits import AiLimits
from chromasense.core.policy.ai_verification import verify_items
from chromasense.core.ports import (
    AiUsageLedger,
    Clock,
    ImageStore,
    InterpretationCache,
    VisionReader,
)

INTERPRETATION_LIFETIME = timedelta(days=30)


@dataclass(frozen=True)
class InterpretImageRequest:
    image_id: str
    session_id: str
    ip_address: str


class InterpretImage:
    def __init__(
        self,
        store: ImageStore,
        reader: VisionReader,
        cache: InterpretationCache,
        ledger: AiUsageLedger,
        limits: AiLimits,
        clock: Clock,
    ) -> None:
        self._store = store
        self._reader = reader
        self._cache = cache
        self._ledger = ledger
        self._limits = limits
        self._clock = clock

    def execute(self, request: InterpretImageRequest) -> Interpretation:
        stored = self._store.load(request.image_id)
        if stored is None or stored.analysis is None:
            raise ImageNotFound(f"No image has the ID {request.image_id}")

        now = self._clock.now()
        cached = self._cache.get(stored.record.image_hash, now)
        if cached is not None:
            return cached

        self._limits.check(self._ledger.usage(request.session_id, request.ip_address, now))
        analysis = stored.analysis
        try:
            read = self._reader.read(stored.working, analysis.palette, analysis.image_type)
        except AiUnavailable:
            self._ledger.record(request.session_id, request.ip_address, 0.0, now)
            raise
        self._ledger.record(request.session_id, request.ip_address, read.estimated_cost, now)

        items = verify_items(read, analysis, analysis.palette)
        interpretation = Interpretation(
            image_hash=stored.record.image_hash,
            chart_type=read.chart_type,
            summary=read.summary,
            legend=items.legend,
            text_items=items.text_items,
            shape_items=items.shape_items,
            color_items=items.color_items,
            created_at=now,
            expires_at=now + INTERPRETATION_LIFETIME,
        )
        self._cache.put(interpretation)
        return interpretation
