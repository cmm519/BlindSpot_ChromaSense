"""Run the upload pipeline. This use case sets the filter order for an upload."""

import hashlib
from dataclasses import dataclass
from datetime import timedelta
from uuid import uuid4

from chromasense.core.errors import InvalidImage
from chromasense.core.models import (
    ColorItem,
    ImageAnalysis,
    ImageRecord,
    ItemSource,
    LegendEntry,
    PatternGroup,
    ShapeItem,
    TextItem,
    Verification,
)
from chromasense.core.ports import Clock, ImageStore
from color_engine.models import (
    ConfusablePair,
    ConfusionGroup,
    CvdProfile,
    CvdType,
    ImageDecodeError,
    Shape,
    TextPiece,
    TextSet6,
)
from color_engine.pipeline.filter_1_decode.decode_1 import decode_1
from color_engine.pipeline.filter_2_downscale.downscale_2 import downscale_2
from color_engine.pipeline.filter_3_palette.extract_palette_3 import extract_palette_3
from color_engine.pipeline.filter_4_regions.find_regions_4 import find_regions_4
from color_engine.pipeline.filter_5_shapes.find_shapes_5 import find_shapes_5
from color_engine.pipeline.filter_6_text.read_text_6 import read_text_6
from color_engine.pipeline.filter_7_layout.analyze_layout_7 import analyze_layout_7
from color_engine.pipeline.filter_8_confusion.detect_confusion_8 import detect_confusion_8
from color_engine.pipeline.filter_9_enhance.enhance_9 import enhance_9
from color_engine.rules.naming import ColorNamer
from color_engine.rules.overlay import pattern_label

_TEXT_OVERLAP_SHARE = 0.5


@dataclass(frozen=True)
class ProcessUploadRequest:
    data: bytes
    profile: CvdProfile


@dataclass(frozen=True)
class ProcessUploadResponse:
    image_id: str
    analysis: ImageAnalysis
    pairs: tuple[ConfusablePair, ...]
    groups: tuple[PatternGroup, ...]
    remaining_pair_count: int | None
    enhancement_needed: bool


class ProcessUpload:
    def __init__(
        self,
        store: ImageStore,
        clock: Clock,
        threshold: float,
        retention: timedelta,
        max_megapixels: float = 12.0,
        color_count: int = 12,
    ) -> None:
        self._store = store
        self._clock = clock
        self._threshold = threshold
        self._retention = retention
        self._max_megapixels = max_megapixels
        self._color_count = color_count

    def execute(self, request: ProcessUploadRequest) -> ProcessUploadResponse:
        try:
            decoded = decode_1(request.data)
        except ImageDecodeError as error:
            raise InvalidImage(str(error)) from error

        working = downscale_2(decoded, self._max_megapixels)
        pixels = working.pixels
        palette = extract_palette_3(pixels, self._color_count)
        regions = find_regions_4(pixels, palette)
        shapes = find_shapes_5(regions)
        text = read_text_6(pixels)
        layout = analyze_layout_7(pixels, palette, regions, text)
        analysis = _build_analysis(
            palette, regions, shapes, text, layout, working.width, working.height
        )

        pairs: tuple[ConfusablePair, ...] = ()
        groups: tuple[PatternGroup, ...] = ()
        remaining: int | None = None
        if request.profile.type is not CvdType.NONE:
            confusion = detect_confusion_8(pixels, palette, request.profile, self._threshold)
            enhanced = enhance_9(pixels, confusion).pixels
            new_palette = extract_palette_3(enhanced, self._color_count)
            remaining_result = detect_confusion_8(
                enhanced, new_palette, request.profile, self._threshold
            )
            pairs = confusion.pairs
            groups = to_pattern_groups(confusion.groups)
            remaining = len(remaining_result.pairs)

        now = self._clock.now()
        record = ImageRecord(
            image_id=uuid4().hex,
            image_hash=hashlib.sha256(request.data).hexdigest(),
            width=decoded.width,
            height=decoded.height,
            created_at=now,
            expires_at=now + self._retention,
        )
        self._store.save(record, request.data, pixels)
        self._store.save_analysis(record.image_id, analysis)
        return ProcessUploadResponse(
            image_id=record.image_id,
            analysis=analysis,
            pairs=pairs,
            groups=groups,
            remaining_pair_count=remaining,
            enhancement_needed=bool(pairs),
        )


def to_pattern_groups(groups: tuple[ConfusionGroup, ...]) -> tuple[PatternGroup, ...]:
    """Name each group's pattern, in the group order that the overlay view draws."""
    return tuple(
        PatternGroup(group.group_id, group.palette_ids, pattern_label(position))
        for position, group in enumerate(groups)
    )


def _build_analysis(palette, regions, shapes, text, layout, width, height) -> ImageAnalysis:
    namer = ColorNamer()
    names = {entry.id: namer.describe(entry.rgb) for entry in palette.entries}
    color_items = tuple(
        ColorItem(
            item_id=f"color-{entry.id}",
            palette_id=entry.id,
            name=names[entry.id].name,
            hex=names[entry.id].hex,
            rgb=names[entry.id].rgb,
            hsl=names[entry.id].hsl,
            family=names[entry.id].family,
            source=ItemSource.LOCAL,
            verification=Verification.VERIFIED,
            share=entry.share,
        )
        for entry in palette.entries
    )
    shape_items = tuple(
        ShapeItem(
            item_id=f"shape-{shape.id}",
            kind=shape.kind,
            palette_id=shape.palette_id,
            color_name=names[shape.palette_id].name,
            source=ItemSource.LOCAL,
            verification=Verification.UNVERIFIED,
            x=shape.x,
            y=shape.y,
            width=shape.width,
            height=shape.height,
        )
        for shape in shapes.shapes
        if not _is_part_of_text(shape, text)
    )
    text_items = tuple(
        TextItem(
            item_id=f"text-{position}",
            text=piece.text,
            source=ItemSource.LOCAL,
            verification=Verification.UNVERIFIED,
            x=piece.x,
            y=piece.y,
            width=piece.width,
            height=piece.height,
        )
        for position, piece in enumerate(text.items, start=1)
    )
    legend = tuple(
        LegendEntry(
            item_id=f"legend-{position}",
            palette_id=entry.palette_id,
            text=entry.text,
            source=ItemSource.LOCAL,
            verification=Verification.UNVERIFIED,
            x=entry.x,
            y=entry.y,
            width=entry.width,
            height=entry.height,
        )
        for position, entry in enumerate(layout.legend, start=1)
    )
    summary = (
        f"{layout.image_type.value.replace('_', ' ').capitalize()} with "
        f"{_count(len(color_items), 'color')}, {_count(len(regions.regions), 'region')}, "
        f"{_count(len(shape_items), 'shape')}, and {_count(len(text_items), 'text item')}."
    )
    return ImageAnalysis(
        palette=palette,
        regions=regions.regions,
        shapes=shape_items,
        text=text_items,
        legend=legend,
        image_type=layout.image_type,
        color_items=color_items,
        summary=summary,
        width=width,
        height=height,
    )


def _is_part_of_text(shape: Shape, text: TextSet6) -> bool:
    """A letter such as "o" can look like a circle, but it is text, not a shape."""
    shape_area = shape.width * shape.height
    return any(_overlap(shape, piece) >= _TEXT_OVERLAP_SHARE * shape_area for piece in text.items)


def _overlap(shape: Shape, piece: TextPiece) -> int:
    width = min(shape.x + shape.width, piece.x + piece.width) - max(shape.x, piece.x)
    height = min(shape.y + shape.height, piece.y + piece.height) - max(shape.y, piece.y)
    return max(width, 0) * max(height, 0)


def _count(count: int, noun: str) -> str:
    return f"{count} {noun}" if count == 1 else f"{count} {noun}s"
