import sqlite3
from datetime import UTC, datetime, timedelta, timezone

from chromasense.core.models import (
    ColorItem,
    Interpretation,
    ItemSource,
    LegendEntry,
    ShapeItem,
    TextItem,
    Verification,
)
from chromasense.storage.sqlite_ai_usage_ledger import SqliteAiUsageLedger
from chromasense.storage.sqlite_interpretation_cache import SqliteInterpretationCache

NOW = datetime(2026, 3, 15, 12, 0, tzinfo=UTC)
HOUR = 3600.0


def _interpretation(image_hash="hash-1", created_at=NOW, lifetime=timedelta(days=30)):
    return Interpretation(
        image_hash=image_hash,
        chart_type="bar",
        summary="A chart.",
        legend=(LegendEntry("ai-legend-1", 1, "North", ItemSource.BOTH, Verification.VERIFIED),),
        text_items=(
            TextItem("text-1", "Title", ItemSource.BOTH, Verification.VERIFIED, 1, 2, 3, 4),
        ),
        shape_items=(
            ShapeItem("ai-shape-1", "circle", 1, "red", ItemSource.AI, Verification.UNVERIFIED),
        ),
        color_items=(
            ColorItem(
                "color-1",
                1,
                "red",
                "#FF0000",
                (255, 0, 0),
                (0, 100, 50),
                "red",
                ItemSource.BOTH,
                Verification.VERIFIED,
                0.5,
            ),
            ColorItem(
                "color-unknown-9",
                9,
                None,
                None,
                None,
                None,
                None,
                ItemSource.AI,
                Verification.UNVERIFIED,
            ),
        ),
        created_at=created_at,
        expires_at=created_at + lifetime,
    )


def test_cache_round_trip_keeps_the_final_flags(tmp_path):
    cache = SqliteInterpretationCache(tmp_path / "db.sqlite3")
    stored = _interpretation()
    cache.put(stored)
    assert cache.get("hash-1", NOW) == stored
    assert cache.get("other-hash", NOW) is None


def test_entry_dated_31_days_ago_is_not_returned_and_29_days_is(tmp_path):
    cache = SqliteInterpretationCache(tmp_path / "db.sqlite3")
    cache.put(_interpretation("old", created_at=NOW - timedelta(days=31)))
    cache.put(_interpretation("recent", created_at=NOW - timedelta(days=29)))
    assert cache.get("old", NOW) is None
    assert cache.get("recent", NOW) is not None


def test_expiry_compares_correctly_across_time_zones(tmp_path):
    cache = SqliteInterpretationCache(tmp_path / "db.sqlite3")
    cache.put(_interpretation(lifetime=timedelta(hours=1)))
    plus_nine = timezone(timedelta(hours=9))
    assert cache.get("hash-1", (NOW + timedelta(minutes=30)).astimezone(plus_nine)) is not None
    assert cache.get("hash-1", (NOW + timedelta(hours=2)).astimezone(plus_nine)) is None


def test_delete_expired_removes_only_expired_entries(tmp_path):
    database = tmp_path / "db.sqlite3"
    cache = SqliteInterpretationCache(database)
    cache.put(_interpretation("old", created_at=NOW - timedelta(days=31)))
    cache.put(_interpretation("recent"))
    assert cache.delete_expired(NOW) == 1
    with sqlite3.connect(database) as connection:
        rows = connection.execute("SELECT image_hash FROM interpretations").fetchall()
    assert rows == [("recent",)]


def test_put_replaces_an_entry_for_the_same_hash(tmp_path):
    cache = SqliteInterpretationCache(tmp_path / "db.sqlite3")
    cache.put(_interpretation())
    cache.put(_interpretation(created_at=NOW + timedelta(days=1)))
    assert cache.get("hash-1", NOW).created_at == NOW + timedelta(days=1)


def test_data_survives_a_new_adapter_instance(tmp_path):
    database = tmp_path / "db.sqlite3"
    SqliteInterpretationCache(database).put(_interpretation())
    ledger = SqliteAiUsageLedger(database, HOUR)
    ledger.record("s1", "1.1.1.1", 1.0, NOW)
    assert SqliteInterpretationCache(database).get("hash-1", NOW) is not None
    assert SqliteAiUsageLedger(database, HOUR).usage("s1", "1.1.1.1", NOW).session_count == 1


def test_usage_counts_session_and_ip_separately(tmp_path):
    ledger = SqliteAiUsageLedger(tmp_path / "db.sqlite3", HOUR)
    ledger.record("s1", "1.1.1.1", 0.5, NOW)
    ledger.record("s1", "2.2.2.2", 0.5, NOW)
    ledger.record("s2", "1.1.1.1", 0.5, NOW)
    usage = ledger.usage("s1", "1.1.1.1", NOW)
    assert (usage.session_count, usage.ip_count) == (2, 2)
    assert usage.total_cost == 1.5


def test_usage_counts_only_the_window(tmp_path):
    ledger = SqliteAiUsageLedger(tmp_path / "db.sqlite3", HOUR)
    ledger.record("s1", "1.1.1.1", 0.0, NOW - timedelta(minutes=61))
    ledger.record("s1", "1.1.1.1", 0.0, NOW - timedelta(minutes=59))
    assert ledger.usage("s1", "1.1.1.1", NOW).session_count == 1


def test_total_cost_sums_the_current_utc_calendar_month(tmp_path):
    ledger = SqliteAiUsageLedger(tmp_path / "db.sqlite3", HOUR)
    ledger.record("s1", "1.1.1.1", 9.0, datetime(2026, 2, 28, 23, 59, tzinfo=UTC))
    ledger.record("s1", "1.1.1.1", 1.0, datetime(2026, 3, 1, 0, 0, tzinfo=UTC))
    ledger.record("s1", "1.1.1.1", 2.0, NOW)
    assert ledger.total_cost(NOW) == 3.0
