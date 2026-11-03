"""Compare one AI read with the stored local analysis, and flag each item."""

from collections import Counter
from collections.abc import Callable, Iterable
from dataclasses import dataclass, replace

from chromasense.core.models import (
    AiAnswer,
    AiRead,
    ColorItem,
    ImageAnalysis,
    Interpretation,
    ItemSource,
    LegendEntry,
    ShapeItem,
    TextItem,
    Verification,
)
from color_engine.models import Palette3
from color_engine.rules.naming import ColorNamer

REASON_MISSING_ID = "The entry has no palette ID"
REASON_UNKNOWN_ID = "The entry's palette ID is not in the image's palette"
REASON_DUPLICATE_ID = "More than one legend entry uses this palette ID"
REASON_LOCAL_DIFFERS = "The local legend has different text for this palette ID"


@dataclass(frozen=True)
class VerifiedItems:
    legend: tuple[LegendEntry, ...]
    text_items: tuple[TextItem, ...]
    shape_items: tuple[ShapeItem, ...]
    color_items: tuple[ColorItem, ...]


def normalize_text(text: str) -> str:
    return " ".join(text.split()).casefold()


def validate_legend(entries: Iterable[LegendEntry], palette: Palette3) -> tuple[LegendEntry, ...]:
    """Flag each entry with a missing or unknown palette ID, or an ID used by more than one."""
    entries = tuple(entries)
    known_ids = {entry.id for entry in palette.entries}
    uses = Counter(entry.palette_id for entry in entries if entry.palette_id is not None)
    return tuple(_validated_entry(entry, known_ids, uses) for entry in entries)


def _validated_entry(entry: LegendEntry, known_ids: set[int], uses: Counter) -> LegendEntry:
    reason = None
    if entry.palette_id is None:
        reason = REASON_MISSING_ID
    elif entry.palette_id not in known_ids:
        reason = REASON_UNKNOWN_ID
    elif uses[entry.palette_id] > 1:
        reason = REASON_DUPLICATE_ID
    state = Verification.UNVERIFIED if reason else Verification.VERIFIED
    return replace(entry, verification=state, reason=reason)


def verify_items(read: AiRead, local: ImageAnalysis, palette: Palette3) -> VerifiedItems:
    return VerifiedItems(
        legend=_verify_legend(read.legend, local.legend, palette),
        text_items=_verify_one_to_one(
            read.text_items, local.text, lambda i: normalize_text(i.text)
        ),
        shape_items=_named_shapes(
            _verify_one_to_one(read.shape_items, local.shapes, lambda i: (i.kind, i.palette_id)),
            palette,
        ),
        color_items=_color_items(read, palette),
    )


def _verify_one_to_one(ai_items: tuple, local_items: tuple, key: Callable) -> tuple:
    """Pair each AI item with one unused local item that has the same key."""
    unused = list(local_items)
    results = []
    for item in ai_items:
        match = next((other for other in unused if key(other) == key(item)), None)
        if match is None:
            results.append(
                replace(item, source=ItemSource.AI, verification=Verification.UNVERIFIED)
            )
        else:
            unused.remove(match)
            results.append(
                replace(match, source=ItemSource.BOTH, verification=Verification.VERIFIED)
            )
    results.extend(
        replace(item, source=ItemSource.LOCAL, verification=Verification.UNVERIFIED)
        for item in unused
    )
    return tuple(results)


def _named_shapes(shapes: tuple[ShapeItem, ...], palette: Palette3) -> tuple[ShapeItem, ...]:
    rgb_by_id = {entry.id: entry.rgb for entry in palette.entries}
    namer = ColorNamer()
    return tuple(
        replace(
            shape,
            color_name=(
                namer.describe(rgb_by_id[shape.palette_id]).name
                if shape.palette_id in rgb_by_id
                else None
            ),
        )
        for shape in shapes
    )


def _verify_legend(
    ai_entries: tuple[LegendEntry, ...],
    local_entries: tuple[LegendEntry, ...],
    palette: Palette3,
) -> tuple[LegendEntry, ...]:
    local_by_id = {entry.palette_id: entry for entry in local_entries}
    matched: set[int] = set()
    results = []
    for entry in validate_legend(ai_entries, palette):
        local = local_by_id.get(entry.palette_id)
        if local is None:
            results.append(replace(entry, source=ItemSource.AI))
            continue
        matched.add(local.palette_id)
        if normalize_text(local.text) != normalize_text(entry.text):
            results.append(
                replace(
                    entry,
                    source=ItemSource.AI,
                    verification=Verification.UNVERIFIED,
                    reason=entry.reason or REASON_LOCAL_DIFFERS,
                )
            )
        else:
            results.append(replace(entry, source=ItemSource.BOTH))
    results.extend(
        replace(entry, source=ItemSource.LOCAL, verification=Verification.UNVERIFIED)
        for entry in local_entries
        if entry.palette_id not in matched
    )
    return tuple(results)


def _color_items(read: AiRead, palette: Palette3) -> tuple[ColorItem, ...]:
    entries = {entry.id: entry for entry in palette.entries}
    referenced = [item.palette_id for item in (*read.legend, *read.shape_items)]
    namer = ColorNamer()
    results = []
    for palette_id in dict.fromkeys(referenced):
        if palette_id is None:
            continue
        entry = entries.get(palette_id)
        if entry is None:
            results.append(
                ColorItem(
                    item_id=f"color-unknown-{palette_id}",
                    palette_id=palette_id,
                    name=None,
                    hex=None,
                    rgb=None,
                    hsl=None,
                    family=None,
                    source=ItemSource.AI,
                    verification=Verification.UNVERIFIED,
                )
            )
            continue
        info = namer.describe(entry.rgb)
        results.append(
            ColorItem(
                item_id=f"color-{palette_id}",
                palette_id=palette_id,
                name=info.name,
                hex=info.hex,
                rgb=info.rgb,
                hsl=info.hsl,
                family=info.family,
                source=ItemSource.BOTH,
                verification=Verification.VERIFIED,
                share=entry.share,
            )
        )
    return tuple(results)


def verify_answer(answer: AiAnswer, interpretation: Interpretation) -> Verification:
    """An answer is verified only when it cites items, and each cited item is verified."""
    states = {
        item.item_id: item.verification
        for item in (
            *interpretation.legend,
            *interpretation.text_items,
            *interpretation.shape_items,
            *interpretation.color_items,
        )
    }
    if not answer.cited_item_ids:
        return Verification.UNVERIFIED
    verified = all(
        states.get(item_id) is Verification.VERIFIED for item_id in answer.cited_item_ids
    )
    return Verification.VERIFIED if verified else Verification.UNVERIFIED
