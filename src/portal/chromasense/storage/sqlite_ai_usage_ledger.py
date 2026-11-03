"""Keep AI request counts and estimated costs in SQLite."""

from datetime import UTC, datetime, timedelta
from pathlib import Path

from chromasense.core.models import AiUsage
from chromasense.storage.sqlite_interpretation_cache import connect, to_utc_text


class SqliteAiUsageLedger:
    def __init__(self, database: Path | str, window_seconds: float) -> None:
        self._database = database
        self._window = timedelta(seconds=window_seconds)
        connect(database).close()

    def record(
        self, session_id: str, ip_address: str, estimated_cost: float, now: datetime
    ) -> None:
        connection = connect(self._database)
        try:
            with connection:
                connection.execute(
                    "INSERT INTO ai_usage (session_id, ip_address, estimated_cost, created_at) "
                    "VALUES (?, ?, ?, ?)",
                    (session_id, ip_address, estimated_cost, to_utc_text(now)),
                )
        finally:
            connection.close()

    def usage(self, session_id: str, ip_address: str, now: datetime) -> AiUsage:
        since = to_utc_text(now - self._window)
        connection = connect(self._database)
        try:
            session_count = connection.execute(
                "SELECT COUNT(*) FROM ai_usage WHERE session_id = ? AND created_at > ?",
                (session_id, since),
            ).fetchone()[0]
            ip_count = connection.execute(
                "SELECT COUNT(*) FROM ai_usage WHERE ip_address = ? AND created_at > ?",
                (ip_address, since),
            ).fetchone()[0]
        finally:
            connection.close()
        return AiUsage(session_count, ip_count, self.total_cost(now))

    def total_cost(self, now: datetime) -> float:
        current = now.astimezone(UTC)
        month_start = current.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        connection = connect(self._database)
        try:
            total = connection.execute(
                "SELECT COALESCE(SUM(estimated_cost), 0) FROM ai_usage WHERE created_at >= ?",
                (to_utc_text(month_start),),
            ).fetchone()[0]
        finally:
            connection.close()
        return float(total)
