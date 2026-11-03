"""Plain data shared by the color rules and the pipeline filters."""

from dataclasses import dataclass
from enum import Enum

import numpy as np
from numpy.typing import NDArray


class CvdType(Enum):
    PROTAN = "protan"
    DEUTAN = "deutan"
    TRITAN = "tritan"
    ACHROMATOPSIA = "achromatopsia"
    NONE = "none"


@dataclass(frozen=True)
class CvdProfile:
    type: CvdType
    severity: float = 0.0

    def __post_init__(self) -> None:
        if not 0.0 <= self.severity <= 1.0:
            raise ValueError("severity must be between 0 and 1")


@dataclass(frozen=True)
class ColorInfo:
    name: str
    hex: str
    rgb: tuple[int, int, int]
    hsl: tuple[int, int, int]
    family: str


class ImageDecodeError(ValueError):
    """The uploaded bytes are not a supported, readable image."""


@dataclass(frozen=True, eq=False)
class DecodedImage1:
    pixels: NDArray[np.uint8]
    width: int
    height: int


@dataclass(frozen=True, eq=False)
class AnalysisImage2:
    pixels: NDArray[np.uint8]
    width: int
    height: int
    scale: float


@dataclass(frozen=True)
class PaletteEntry:
    id: int
    rgb: tuple[int, int, int]
    lab: tuple[float, float, float]
    share: float


@dataclass(frozen=True)
class Palette3:
    entries: tuple[PaletteEntry, ...]


@dataclass(frozen=True)
class ConfusablePair:
    a_id: int
    b_id: int
    original_distance: float
    simulated_distance: float


@dataclass(frozen=True)
class ConfusionGroup:
    group_id: int
    palette_ids: tuple[int, ...]


@dataclass(frozen=True, eq=False)
class ConfusionResult8:
    pairs: tuple[ConfusablePair, ...]
    groups: tuple[ConfusionGroup, ...]
    mask: NDArray[np.bool_]
    color_index: NDArray[np.uint8]


@dataclass(frozen=True, eq=False)
class EnhancedImage9:
    pixels: NDArray[np.uint8]
    method: str


@dataclass(frozen=True)
class Region:
    id: int
    palette_id: int
    x: int
    y: int
    width: int
    height: int
    area: int
    center_x: float
    center_y: float


@dataclass(frozen=True, eq=False)
class RegionMap4:
    regions: tuple[Region, ...]
    labels: NDArray[np.int32]


@dataclass(frozen=True)
class Shape:
    id: int
    kind: str
    palette_id: int
    x: int
    y: int
    width: int
    height: int
    center_x: float
    center_y: float


@dataclass(frozen=True)
class ShapeSet5:
    shapes: tuple[Shape, ...]


@dataclass(frozen=True)
class TextPiece:
    text: str
    x: int
    y: int
    width: int
    height: int
    confidence: float


@dataclass(frozen=True)
class TextSet6:
    items: tuple[TextPiece, ...]


class ImageType(Enum):
    CHART = "chart"
    MAP = "map"
    FLAT_GRAPHIC = "flat_graphic"
    PHOTOGRAPH = "photograph"


@dataclass(frozen=True)
class LegendEntry7:
    palette_id: int
    text: str
    x: int
    y: int
    width: int
    height: int


@dataclass(frozen=True)
class LayoutResult7:
    image_type: ImageType
    legend: tuple[LegendEntry7, ...]
