"""Keep cached interpretations in SQLite."""

import json
import sqlite3
from datetime import UTC, datetime
from importlib import resources
from pathlib import Path

from chromasense.core.models import Interpretation, LegendEntry, ShapeItem, TextItem
from chromasense.storage.filesystem_image_store import (
    _color_from_dict,
    _item_from_dict,
    _item_to_dict,
)


def connect(database: Path | str) -> sqlite3.Connection:
    """Open the database, and create its tables if they are missing."""
    connection = sqlite3.connect(database, timeout=10.0)
    schema = resources.files("chromasense.storage").joinpath("schema.sql").read_text()
    connection.executescript(schema)
    return connection


def to_utc_text(moment: datetime) -> str:
    """Store times in one zone and format, so that they compare correctly as text."""
    return moment.astimezone(UTC).isoformat()


class SqliteInterpretationCache:
    def __init__(self, database: Path | str) -> None:
        self._database = database
        connect(database).close()

    def get(self, image_hash: str, now: datetime) -> Interpretation | None:
        connection = connect(self._database)
        try:
            row = connection.execute(
                "SELECT payload FROM interpretations WHERE image_hash = ? AND expires_at > ?",
                (image_hash, to_utc_text(now)),
            ).fetchone()
        finally:
            connection.close()
        return None if row is None else _from_payload(json.loads(row[0]))

    def put(self, interpretation: Interpretation) -> None:
        connection = connect(self._database)
        try:
            with connection:
                connection.execute(
                    "INSERT OR REPLACE INTO interpretations "
                    "(image_hash, payload, created_at, expires_at) VALUES (?, ?, ?, ?)",
                    (
                        interpretation.image_hash,
                        json.dumps(_to_payload(interpretation)),
                        to_utc_text(interpretation.created_at),
                        to_utc_text(interpretation.expires_at),
                    ),
                )
        finally:
            connection.close()

    def delete_expired(self, now: datetime) -> int:
        connection = connect(self._database)
        try:
            with connection:
                cursor = connection.execute(
                    "DELETE FROM interpretations WHERE expires_at <= ?", (to_utc_text(now),)
                )
            return cursor.rowcount
        finally:
            connection.close()


def _to_payload(interpretation: Interpretation) -> dict:
    return {
        "image_hash": interpretation.image_hash,
        "chart_type": interpretation.chart_type,
        "summary": interpretation.summary,
        "legend": [_item_to_dict(item) for item in interpretation.legend],
        "text_items": [_item_to_dict(item) for item in interpretation.text_items],
        "shape_items": [_item_to_dict(item) for item in interpretation.shape_items],
        "color_items": [_item_to_dict(item) for item in interpretation.color_items],
        "created_at": interpretation.created_at.isoformat(),
        "expires_at": interpretation.expires_at.isoformat(),
    }


def _from_payload(values: dict) -> Interpretation:
    return Interpretation(
        image_hash=values["image_hash"],
        chart_type=values["chart_type"],
        summary=values["summary"],
        legend=tuple(_item_from_dict(LegendEntry, item) for item in values["legend"]),
        text_items=tuple(_item_from_dict(TextItem, item) for item in values["text_items"]),
        shape_items=tuple(_item_from_dict(ShapeItem, item) for item in values["shape_items"]),
        color_items=tuple(_color_from_dict(item) for item in values["color_items"]),
        created_at=datetime.fromisoformat(values["created_at"]),
        expires_at=datetime.fromisoformat(values["expires_at"]),
    )
