"""Answer a typed question about an interpreted image."""

from dataclasses import dataclass

from chromasense.core.errors import AiUnavailable, ImageNotFound, NotInterpreted
from chromasense.core.models import Verification
from chromasense.core.policy.ai_limits import AiLimits
from chromasense.core.policy.ai_verification import verify_answer
from chromasense.core.ports import (
    AiUsageLedger,
    Clock,
    ImageStore,
    InterpretationCache,
    VisionReader,
)


@dataclass(frozen=True)
class AnswerQuestionRequest:
    image_id: str
    question: str
    session_id: str
    ip_address: str


@dataclass(frozen=True)
class AnswerQuestionResponse:
    text: str
    cited_item_ids: tuple[str, ...]
    verification: Verification


class AnswerQuestion:
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

    def execute(self, request: AnswerQuestionRequest) -> AnswerQuestionResponse:
        stored = self._store.load(request.image_id)
        if stored is None or stored.analysis is None:
            raise ImageNotFound(f"No image has the ID {request.image_id}")

        now = self._clock.now()
        interpretation = self._cache.get(stored.record.image_hash, now)
        if interpretation is None:
            raise NotInterpreted("Click Explain before you ask a question about this image")

        self._limits.check(self._ledger.usage(request.session_id, request.ip_address, now))
        items = (
            *interpretation.legend,
            *interpretation.text_items,
            *interpretation.shape_items,
            *interpretation.color_items,
        )
        try:
            answer = self._reader.ask(
                stored.working, stored.analysis.palette, items, request.question
            )
        except AiUnavailable:
            self._ledger.record(request.session_id, request.ip_address, 0.0, now)
            raise
        self._ledger.record(request.session_id, request.ip_address, answer.estimated_cost, now)
        return AnswerQuestionResponse(
            answer.text, answer.cited_item_ids, verify_answer(answer, interpretation)
        )
