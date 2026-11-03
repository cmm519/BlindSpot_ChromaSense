"""Plain data that crosses the Application Core boundary."""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from numpy.typing import NDArray

from color_engine.models import ImageType, Palette3, Region


class Verification(Enum):
    VERIFIED = "verified"
    UNVERIFIED = "unverified"


class ItemSource(Enum):
    LOCAL = "local"
    AI = "ai"
    BOTH = "both"


@dataclass(frozen=True)
class ImageRecord:
    image_id: str
    image_hash: str
    width: int
    height: int
    created_at: datetime
    expires_at: datetime


@dataclass(frozen=True)
class TextItem:
    item_id: str
    text: str
    source: ItemSource
    verification: Verification
    x: int | None = None
    y: int | None = None
    width: int | None = None
    height: int | None = None


@dataclass(frozen=True)
class ShapeItem:
    item_id: str
    kind: str
    palette_id: int | None
    color_name: str | None
    source: ItemSource
    verification: Verification
    x: int | None = None
    y: int | None = None
    width: int | None = None
    height: int | None = None


@dataclass(frozen=True)
class LegendEntry:
    item_id: str
    palette_id: int | None
    text: str
    source: ItemSource
    verification: Verification
    reason: str | None = None
    x: int | None = None
    y: int | None = None
    width: int | None = None
    height: int | None = None


@dataclass(frozen=True)
class ColorItem:
    item_id: str
    palette_id: int | None
    name: str | None
    hex: str | None
    rgb: tuple[int, int, int] | None
    hsl: tuple[int, int, int] | None
    family: str | None
    source: ItemSource
    verification: Verification
    share: float | None = None


@dataclass(frozen=True)
class ImageAnalysis:
    palette: Palette3
    regions: tuple[Region, ...]
    shapes: tuple[ShapeItem, ...]
    text: tuple[TextItem, ...]
    legend: tuple[LegendEntry, ...]
    image_type: ImageType
    color_items: tuple[ColorItem, ...]
    summary: str
    width: int
    height: int


@dataclass(frozen=True)
class PatternGroup:
    group_id: int
    palette_ids: tuple[int, ...]
    pattern: str


@dataclass(frozen=True, eq=False)
class StoredImage:
    record: ImageRecord
    original: bytes
    working: NDArray
    analysis: ImageAnalysis | None


@dataclass(frozen=True)
class AiRead:
    chart_type: str
    legend: tuple[LegendEntry, ...]
    text_items: tuple[TextItem, ...]
    shape_items: tuple[ShapeItem, ...]
    summary: str
    estimated_cost: float


@dataclass(frozen=True)
class AiAnswer:
    text: str
    cited_item_ids: tuple[str, ...]
    estimated_cost: float


@dataclass(frozen=True)
class AiUsage:
    session_count: int
    ip_count: int
    total_cost: float


@dataclass(frozen=True)
class Interpretation:
    image_hash: str
    chart_type: str
    summary: str
    legend: tuple[LegendEntry, ...]
    text_items: tuple[TextItem, ...]
    shape_items: tuple[ShapeItem, ...]
    color_items: tuple[ColorItem, ...]
    created_at: datetime
    expires_at: datetime
