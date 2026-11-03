"""Pydantic request and response shapes, and their mapping from core models."""

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

from chromasense.core.models import (
    ColorItem,
    ImageAnalysis,
    ItemSource,
    LegendEntry,
    PatternGroup,
    ShapeItem,
    TextItem,
    Verification,
)
from color_engine.models import ColorInfo, ConfusablePair, CvdProfile, CvdType, ImageType

ImageId = Annotated[str, Field(pattern=r"^[0-9a-f]{32}$")]
CvdTypeName = Literal["protan", "deutan", "tritan", "achromatopsia", "none"]
ViewName = Literal["original", "simulated", "enhanced", "overlay"]
UnitInterval = Annotated[float, Field(ge=0.0, le=1.0, allow_inf_nan=False)]


class InvalidProfile(ValueError):
    """The CVD type and severity do not fit together."""


class UploadTooLarge(ValueError):
    """The uploaded file is over the size limit."""


def to_profile(cvd_type: str, severity: float | None) -> CvdProfile:
    if cvd_type == "none":
        if severity is not None:
            raise InvalidProfile("Severity is not used when no CVD is selected")
        return CvdProfile(CvdType.NONE)
    if severity is None:
        raise InvalidProfile("Severity is required with a CVD type")
    return CvdProfile(CvdType(cvd_type), severity)


class ProfileBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    cvd_type: CvdTypeName
    severity: UnitInterval | None = None


class _FromCore(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class PaletteEntrySchema(_FromCore):
    id: int
    rgb: tuple[int, int, int]
    lab: tuple[float, float, float]
    share: float


class RegionSchema(_FromCore):
    id: int
    palette_id: int
    x: int
    y: int
    width: int
    height: int
    area: int
    center_x: float
    center_y: float


class _ItemSchema(_FromCore):
    item_id: str
    source: ItemSource
    verification: Verification


class ShapeSchema(_ItemSchema):
    kind: str
    palette_id: int | None
    color_name: str | None
    x: int | None
    y: int | None
    width: int | None
    height: int | None


class TextSchema(_ItemSchema):
    text: str
    x: int | None
    y: int | None
    width: int | None
    height: int | None


class LegendSchema(_ItemSchema):
    palette_id: int | None
    text: str
    reason: str | None
    x: int | None
    y: int | None
    width: int | None
    height: int | None


class ColorItemSchema(_ItemSchema):
    palette_id: int | None
    name: str | None
    hex: str | None
    rgb: tuple[int, int, int] | None
    hsl: tuple[int, int, int] | None
    family: str | None
    share: float | None


class AnalysisSchema(BaseModel):
    palette: list[PaletteEntrySchema]
    regions: list[RegionSchema]
    shapes: list[ShapeSchema]
    text: list[TextSchema]
    legend: list[LegendSchema]
    image_type: ImageType
    color_items: list[ColorItemSchema]
    summary: str
    width: int
    height: int


def analysis_schema(analysis: ImageAnalysis) -> AnalysisSchema:
    return AnalysisSchema(
        palette=[PaletteEntrySchema.model_validate(entry) for entry in analysis.palette.entries],
        regions=[RegionSchema.model_validate(region) for region in analysis.regions],
        shapes=[_validate(ShapeSchema, item, ShapeItem) for item in analysis.shapes],
        text=[_validate(TextSchema, item, TextItem) for item in analysis.text],
        legend=[_validate(LegendSchema, item, LegendEntry) for item in analysis.legend],
        image_type=analysis.image_type,
        color_items=[_validate(ColorItemSchema, item, ColorItem) for item in analysis.color_items],
        summary=analysis.summary,
        width=analysis.width,
        height=analysis.height,
    )


def _validate(schema: type[BaseModel], item: object, core_type: type) -> BaseModel:
    if not isinstance(item, core_type):
        raise TypeError(f"expected {core_type.__name__}")
    return schema.model_validate(item)


class PairSchema(_FromCore):
    a_id: int
    b_id: int
    original_distance: float
    simulated_distance: float


class GroupSchema(_FromCore):
    group_id: int
    palette_ids: list[int]
    pattern: str


class UploadResponseSchema(BaseModel):
    image_id: str
    analysis: AnalysisSchema
    pairs: list[PairSchema]
    groups: list[GroupSchema]
    remaining_pair_count: int | None
    enhancement_needed: bool


class ReanalyzeResponseSchema(BaseModel):
    image_id: str
    pairs: list[PairSchema]
    groups: list[GroupSchema]
    remaining_pair_count: int | None
    enhancement_needed: bool


class AnalysisResponseSchema(BaseModel):
    image_id: str
    analysis: AnalysisSchema


class ColorInfoSchema(_FromCore):
    name: str
    hex: str
    rgb: tuple[int, int, int]
    hsl: tuple[int, int, int]
    family: str


class ColorResponseSchema(BaseModel):
    color: ColorInfoSchema
    simulated_rgb: tuple[int, int, int] | None
    simulated_hex: str | None


class InterpretBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    image_id: ImageId


class AskBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    image_id: ImageId
    question: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=1000)
    ]


class InterpretationSchema(_FromCore):
    chart_type: str
    summary: str
    legend: list[LegendSchema]
    text_items: list[TextSchema]
    shape_items: list[ShapeSchema]
    color_items: list[ColorItemSchema]


class AnswerResponseSchema(_FromCore):
    text: str
    cited_item_ids: list[str]
    verification: Verification


def group_schemas(groups: tuple[PatternGroup, ...]) -> list[GroupSchema]:
    return [GroupSchema.model_validate(group) for group in groups]


def pair_schemas(pairs: tuple[ConfusablePair, ...]) -> list[PairSchema]:
    return [PairSchema.model_validate(pair) for pair in pairs]


def color_schema(color: ColorInfo) -> ColorInfoSchema:
    return ColorInfoSchema.model_validate(color)
