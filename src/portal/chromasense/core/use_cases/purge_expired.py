"""Delete the data whose time has passed."""

from dataclasses import dataclass

from chromasense.core.ports import Clock, ImageStore, InterpretationCache


@dataclass(frozen=True)
class PurgeExpiredRequest:
    pass


@dataclass(frozen=True)
class PurgeExpiredResponse:
    images_deleted: int
    interpretations_deleted: int


class PurgeExpired:
    def __init__(self, store: ImageStore, cache: InterpretationCache, clock: Clock) -> None:
        self._store = store
        self._cache = cache
        self._clock = clock

    def execute(self, request: PurgeExpiredRequest) -> PurgeExpiredResponse:
        now = self._clock.now()
        return PurgeExpiredResponse(
            images_deleted=self._store.delete_expired(now),
            interpretations_deleted=self._cache.delete_expired(now),
        )
