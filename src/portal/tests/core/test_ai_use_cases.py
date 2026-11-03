from dataclasses import replace
from datetime import timedelta

import numpy as np
import pytest
from fakes import (
    START,
    FakeAiUsageLedger,
    FakeClock,
    FakeImageStore,
    FakeInterpretationCache,
    FakeVisionReader,
)

from chromasense.core.errors import (
    AiRateLimited,
    AiSpendCapReached,
    AiUnavailable,
    ImageNotFound,
    NotInterpreted,
)
from chromasense.core.models import (
    AiAnswer,
    AiRead,
    ImageAnalysis,
    ImageRecord,
    ItemSource,
    LegendEntry,
    ShapeItem,
    TextItem,
    Verification,
)
from chromasense.core.policy.ai_limits import AiLimits
from chromasense.core.policy.ai_verification import (
    REASON_DUPLICATE_ID,
    REASON_LOCAL_DIFFERS,
    REASON_MISSING_ID,
    REASON_UNKNOWN_ID,
    validate_legend,
    verify_answer,
)
from chromasense.core.use_cases.answer_question import AnswerQuestion, AnswerQuestionRequest
from chromasense.core.use_cases.interpret_image import InterpretImage, InterpretImageRequest
from color_engine.models import ImageType, Palette3, PaletteEntry
from color_engine.rules.naming import ColorNamer

IMAGE_ID = "a" * 32
LOCAL = ItemSource.LOCAL
AI = ItemSource.AI
UNVERIFIED = Verification.UNVERIFIED
VERIFIED = Verification.VERIFIED
PALETTE = Palette3(
    (
        PaletteEntry(1, (220, 30, 30), (46.0, 70.0, 50.0), 0.5),
        PaletteEntry(2, (30, 150, 30), (54.0, -55.0, 50.0), 0.5),
    )
)


def _local_text(item_id, text):
    return TextItem(item_id, text, LOCAL, UNVERIFIED, 1, 2, 3, 4)


def _local_shape(item_id, kind, palette_id):
    return ShapeItem(item_id, kind, palette_id, "red", LOCAL, UNVERIFIED, 1, 2, 3, 4)


def _local_legend(item_id, palette_id, text):
    return LegendEntry(item_id, palette_id, text, LOCAL, UNVERIFIED)


ANALYSIS = ImageAnalysis(
    palette=PALETTE,
    regions=(),
    shapes=(_local_shape("shape-1", "circle", 1), _local_shape("shape-2", "triangle", 2)),
    text=(_local_text("text-1", "Quarterly   Sales"), _local_text("text-2", "Only Local")),
    legend=(_local_legend("legend-1", 1, "North"), _local_legend("legend-2", 2, "South")),
    image_type=ImageType.CHART,
    color_items=(),
    summary="Chart.",
    width=4,
    height=4,
)


def _ai_text(position, text):
    return TextItem(f"ai-text-{position}", text, AI, UNVERIFIED)


def _ai_shape(position, kind, palette_id):
    return ShapeItem(f"ai-shape-{position}", kind, palette_id, None, AI, UNVERIFIED)


def _ai_legend(position, palette_id, text):
    return LegendEntry(f"ai-legend-{position}", palette_id, text, AI, UNVERIFIED)


READ = AiRead(
    chart_type="bar",
    legend=(_ai_legend(1, 1, "north"), _ai_legend(2, 2, "Southern")),
    text_items=(_ai_text(1, "quarterly sales"), _ai_text(2, "Only AI")),
    shape_items=(_ai_shape(1, "circle", 1), _ai_shape(2, "rectangle", 2)),
    summary="Sales by quarter.",
    estimated_cost=0.25,
)


def _store(image_hash="hash-1") -> FakeImageStore:
    store = FakeImageStore()
    record = ImageRecord(IMAGE_ID, image_hash, 4, 4, START, START + timedelta(hours=24))
    store.save(record, b"original", np.zeros((4, 4, 3), dtype=np.uint8))
    store.save_analysis(IMAGE_ID, ANALYSIS)
    return store


class Harness:
    def __init__(self, read=READ, answer=None, error=None, limits=None) -> None:
        self.store = _store()
        self.reader = FakeVisionReader(read, answer, error)
        self.cache = FakeInterpretationCache()
        self.ledger = FakeAiUsageLedger()
        self.clock = FakeClock()
        self.limits = limits or AiLimits(100, 100, 1000.0)

    def _parts(self):
        return (self.store, self.reader, self.cache, self.ledger, self.limits, self.clock)

    def interpret(self, session="s1", ip="1.1.1.1"):
        request = InterpretImageRequest(IMAGE_ID, session, ip)
        return InterpretImage(*self._parts()).execute(request)

    def ask(self, question="What is it?", session="s1", ip="1.1.1.1"):
        request = AnswerQuestionRequest(IMAGE_ID, question, session, ip)
        return AnswerQuestion(*self._parts()).execute(request)


def _by_id(items):
    return {item.item_id: item for item in items}


def test_one_explain_makes_exactly_one_read_with_only_image_palette_and_type():
    harness = Harness()
    harness.interpret()
    assert len(harness.reader.read_calls) == 1
    image, palette, image_type = harness.reader.read_calls[0]
    assert palette is ANALYSIS.palette or palette == PALETTE
    assert image_type is ImageType.CHART
    assert image.shape == (4, 4, 3)


def test_text_matching_after_normalizing_is_verified_and_others_are_not():
    items = _by_id(Harness().interpret().text_items)
    assert items["text-1"].verification is VERIFIED
    assert items["text-1"].source is ItemSource.BOTH
    assert items["text-1"].text == "Quarterly   Sales"
    assert (items["ai-text-2"].verification, items["ai-text-2"].source) == (UNVERIFIED, AI)
    assert (items["text-2"].verification, items["text-2"].source) == (UNVERIFIED, LOCAL)


def test_duplicate_text_matches_one_to_one():
    read = replace(READ, text_items=(_ai_text(1, "Only Local"), _ai_text(2, "only local")))
    items = Harness(read=read).interpret().text_items
    assert [item.verification for item in items if item.text.casefold() == "only local"] == [
        VERIFIED,
        UNVERIFIED,
    ]


def test_shape_agrees_only_when_kind_and_palette_id_match():
    items = _by_id(Harness().interpret().shape_items)
    assert (items["shape-1"].verification, items["shape-1"].source) == (VERIFIED, ItemSource.BOTH)
    assert (items["ai-shape-2"].verification, items["ai-shape-2"].source) == (UNVERIFIED, AI)
    assert (items["shape-2"].verification, items["shape-2"].source) == (UNVERIFIED, LOCAL)


def test_same_kind_with_a_different_palette_id_does_not_agree():
    read = replace(READ, shape_items=(_ai_shape(1, "circle", 2),))
    items = _by_id(Harness(read=read).interpret().shape_items)
    assert items["ai-shape-1"].verification is UNVERIFIED
    assert items["shape-1"].verification is UNVERIFIED


def test_color_names_come_from_the_dataset_for_ai_shapes():
    items = _by_id(Harness().interpret().shape_items)
    assert items["ai-shape-2"].color_name == ColorNamer().describe((30, 150, 30)).name


def test_valid_legend_has_none_flagged():
    entries = (_ai_legend(1, 1, "a"), _ai_legend(2, 2, "b"))
    results = validate_legend(entries, PALETTE)
    assert {entry.verification for entry in results} == {VERIFIED}
    assert {entry.reason for entry in results} == {None}


@pytest.mark.parametrize(
    ("entries", "reasons"),
    [
        ((_ai_legend(1, None, "a"), _ai_legend(2, 2, "b")), [REASON_MISSING_ID, None]),
        ((_ai_legend(1, 99, "a"), _ai_legend(2, 2, "b")), [REASON_UNKNOWN_ID, None]),
        (
            (_ai_legend(1, 1, "a"), _ai_legend(2, 1, "b")),
            [REASON_DUPLICATE_ID, REASON_DUPLICATE_ID],
        ),
    ],
    ids=["missing", "unknown", "duplicated"],
)
def test_missing_unknown_and_duplicated_ids_are_flagged(entries, reasons):
    results = validate_legend(entries, PALETTE)
    assert [entry.reason for entry in results] == reasons
    assert [entry.verification for entry in results] == [
        UNVERIFIED if reason else VERIFIED for reason in reasons
    ]


def test_ai_legend_entry_with_different_text_from_the_local_entry_is_unverified():
    items = _by_id(Harness().interpret().legend)
    assert (items["ai-legend-1"].verification, items["ai-legend-1"].source) == (
        VERIFIED,
        ItemSource.BOTH,
    )
    assert items["ai-legend-2"].verification is UNVERIFIED
    assert items["ai-legend-2"].reason == REASON_LOCAL_DIFFERS


def test_local_legend_entry_the_read_did_not_report_stays_unverified():
    read = replace(READ, legend=(_ai_legend(1, 1, "North"),))
    items = _by_id(Harness(read=read).interpret().legend)
    assert (items["legend-2"].verification, items["legend-2"].source) == (UNVERIFIED, LOCAL)


def test_color_items_are_named_by_the_engine_and_an_invalid_id_is_unverified():
    read = replace(READ, legend=(_ai_legend(1, 1, "a"),), shape_items=(_ai_shape(1, "other", 99),))
    items = _by_id(Harness(read=read).interpret().color_items)
    expected = ColorNamer().describe((220, 30, 30))
    assert items["color-1"].verification is VERIFIED
    assert (items["color-1"].name, items["color-1"].hex) == (expected.name, expected.hex)
    assert items["color-1"].family == expected.family
    assert items["color-unknown-99"].verification is UNVERIFIED
    assert items["color-unknown-99"].name is None


def test_final_flags_are_cached_and_a_second_explain_makes_no_read():
    harness = Harness()
    first = harness.interpret()
    second = harness.interpret()
    assert second == first
    assert len(harness.reader.read_calls) == 1
    assert harness.cache.entries["hash-1"].text_items == first.text_items
    assert len(harness.ledger.records) == 1


def test_expiry_is_thirty_days_and_an_expired_entry_makes_a_new_read():
    harness = Harness()
    assert harness.interpret().expires_at == START + timedelta(days=30)
    harness.clock.current = START + timedelta(days=31)
    harness.interpret()
    assert len(harness.reader.read_calls) == 2


def test_read_counts_toward_usage_with_its_cost():
    harness = Harness()
    harness.interpret("session-a", "9.9.9.9")
    assert harness.ledger.records == [("session-a", "9.9.9.9", 0.25, START)]


def test_failed_read_is_recorded_at_no_cost_and_caches_nothing():
    harness = Harness(error=AiUnavailable("down"))
    with pytest.raises(AiUnavailable):
        harness.interpret()
    assert [record[2] for record in harness.ledger.records] == [0.0]
    assert harness.cache.entries == {}


def test_session_limit_refuses_with_no_provider_call():
    harness = Harness(limits=AiLimits(1, 100, 1000.0))
    harness.interpret("s1", "1.1.1.1")
    harness.cache.entries.clear()
    with pytest.raises(AiRateLimited):
        harness.interpret("s1", "2.2.2.2")
    assert len(harness.reader.read_calls) == 1


def test_ip_limit_refuses_with_no_provider_call():
    harness = Harness(limits=AiLimits(100, 1, 1000.0))
    harness.interpret("s1", "1.1.1.1")
    harness.cache.entries.clear()
    with pytest.raises(AiRateLimited):
        harness.interpret("s2", "1.1.1.1")
    assert len(harness.reader.read_calls) == 1


def test_spend_cap_refuses_at_the_cap_with_no_provider_call():
    harness = Harness(limits=AiLimits(100, 100, 0.25))
    harness.interpret()
    harness.cache.entries.clear()
    with pytest.raises(AiSpendCapReached):
        harness.interpret()
    assert len(harness.reader.read_calls) == 1


def test_cache_hit_is_served_past_the_limit():
    harness = Harness(limits=AiLimits(1, 1, 1000.0))
    first = harness.interpret()
    assert harness.interpret() == first


def test_unknown_image_is_refused():
    harness = Harness()
    harness.store.images.clear()
    with pytest.raises(ImageNotFound):
        harness.interpret()


def _answer(*cited):
    return AiAnswer("It shows sales.", cited, 0.1)


def test_question_before_any_interpretation_is_refused():
    with pytest.raises(NotInterpreted):
        Harness(answer=_answer()).ask()


def test_question_sends_the_same_image_palette_and_items_with_flags():
    harness = Harness(answer=_answer("text-1"))
    interpretation = harness.interpret()
    harness.ask("Which quarter is best?")
    image, palette, items, question = harness.reader.ask_calls[0]
    read_image, read_palette, _ = harness.reader.read_calls[0]
    assert image is read_image
    assert palette == read_palette
    assert question == "Which quarter is best?"
    assert {item.item_id for item in items} >= {item.item_id for item in interpretation.text_items}
    assert {item.verification for item in items} == {VERIFIED, UNVERIFIED}


@pytest.mark.parametrize(
    ("cited", "expected"),
    [
        (("text-1",), VERIFIED),
        (("text-1", "shape-1", "ai-legend-1", "color-1"), VERIFIED),
        (("text-2",), UNVERIFIED),
        (("text-1", "text-2"), UNVERIFIED),
        (("no-such-item",), UNVERIFIED),
        ((), UNVERIFIED),
    ],
    ids=["one-verified", "all-verified", "unverified", "mixed", "unknown", "none"],
)
def test_answer_flag_follows_its_citations(cited, expected):
    harness = Harness(answer=_answer(*cited))
    harness.interpret()
    result = harness.ask()
    assert result.verification is expected
    assert result.cited_item_ids == cited
    assert result.text == "It shows sales."
    assert verify_answer(_answer(*cited), harness.cache.entries["hash-1"]) is expected


def test_question_counts_toward_limits_and_is_refused_past_them():
    harness = Harness(answer=_answer(), limits=AiLimits(2, 100, 1000.0))
    harness.interpret()
    harness.ask()
    assert len(harness.ledger.records) == 2
    with pytest.raises(AiRateLimited):
        harness.ask()
    assert len(harness.reader.ask_calls) == 1


def test_failed_question_is_recorded_at_no_cost():
    harness = Harness()
    harness.interpret()
    harness.reader.error = AiUnavailable("down")
    with pytest.raises(AiUnavailable):
        harness.ask()
    assert harness.ledger.records[-1][2] == 0.0


def test_each_question_stands_alone():
    harness = Harness(answer=_answer())
    harness.interpret()
    harness.ask("first")
    harness.ask("second")
    assert [call[3] for call in harness.reader.ask_calls] == ["first", "second"]
    assert all(len(call) == 4 for call in harness.reader.ask_calls)
