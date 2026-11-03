"""Fakes for every port, so core tests need no framework, database, network, or provider."""

from datetime import UTC, datetime

from chromasense.core.models import AiUsage, StoredImage

START = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)


class FakeClock:
    def __init__(self, now: datetime = START) -> None:
        self.current = now

    def now(self) -> datetime:
        return self.current


class FakeImageStore:
    def __init__(self) -> None:
        self.images: dict[str, StoredImage] = {}

    def save(self, record, original, working) -> None:
        self.images[record.image_id] = StoredImage(record, original, working, None)

    def load(self, image_id):
        return self.images.get(image_id)

    def save_analysis(self, image_id, analysis) -> None:
        stored = self.images[image_id]
        self.images[image_id] = StoredImage(
            stored.record, stored.original, stored.working, analysis
        )

    def delete_expired(self, now) -> int:
        expired = [key for key, value in self.images.items() if value.record.expires_at <= now]
        for key in expired:
            del self.images[key]
        return len(expired)


class FakeInterpretationCache:
    def __init__(self) -> None:
        self.entries = {}
        self.deleted_at = []

    def get(self, image_hash, now):
        entry = self.entries.get(image_hash)
        return entry if entry is not None and entry.expires_at > now else None

    def put(self, interpretation) -> None:
        self.entries[interpretation.image_hash] = interpretation

    def delete_expired(self, now) -> int:
        self.deleted_at.append(now)
        expired = [key for key, value in self.entries.items() if value.expires_at <= now]
        for key in expired:
            del self.entries[key]
        return len(expired)


class FakeAiUsageLedger:
    def __init__(self) -> None:
        self.records = []

    def record(self, session_id, ip_address, estimated_cost, now) -> None:
        self.records.append((session_id, ip_address, estimated_cost, now))

    def usage(self, session_id, ip_address, now) -> AiUsage:
        return AiUsage(
            session_count=sum(record[0] == session_id for record in self.records),
            ip_count=sum(record[1] == ip_address for record in self.records),
            total_cost=self.total_cost(now),
        )

    def total_cost(self, now) -> float:
        return sum(record[2] for record in self.records)


class FakeVisionReader:
    def __init__(self, read_result=None, answer=None, error=None) -> None:
        self.read_result = read_result
        self.answer = answer
        self.error = error
        self.read_calls = []
        self.ask_calls = []

    def read(self, image, palette, image_type):
        self.read_calls.append((image, palette, image_type))
        if self.error is not None:
            raise self.error
        return self.read_result

    def ask(self, image, palette, items, question):
        self.ask_calls.append((image, palette, items, question))
        if self.error is not None:
            raise self.error
        return self.answer
