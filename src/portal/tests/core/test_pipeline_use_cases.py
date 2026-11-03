import inspect
from datetime import timedelta
from io import BytesIO

import numpy as np
import pytest
from fakes import START, FakeClock, FakeImageStore
from PIL import Image, ImageDraw, ImageFont

from chromasense.core.errors import ImageNotFound, InvalidImage
from chromasense.core.models import ItemSource, Verification
from chromasense.core.use_cases import process_upload, reanalyze_for_profile
from chromasense.core.use_cases.get_analysis import GetAnalysis, GetAnalysisRequest
from chromasense.core.use_cases.process_upload import ProcessUpload, ProcessUploadRequest
from chromasense.core.use_cases.reanalyze_for_profile import ReanalyzeForProfile, ReanalyzeRequest
from color_engine.models import CvdProfile, CvdType, ImageType

RED, GREEN, BLUE = (220, 30, 30), (30, 150, 30), (40, 70, 200)
TEAL, LEAF = (90, 150, 210), (90, 170, 150)
THRESHOLD = 10.0
DEUTAN = CvdProfile(CvdType.DEUTAN, 1.0)
TRITAN = CvdProfile(CvdType.TRITAN, 1.0)
NONE = CvdProfile(CvdType.NONE)
UPLOAD_ORDER = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "3", "8"]
NO_CVD_ORDER = ["1", "2", "3", "4", "5", "6", "7"]
REANALYZE_ORDER = ["8", "9", "3", "8"]
FILTERS = {
    "decode_1": "1",
    "downscale_2": "2",
    "extract_palette_3": "3",
    "find_regions_4": "4",
    "find_shapes_5": "5",
    "read_text_6": "6",
    "analyze_layout_7": "7",
    "detect_confusion_8": "8",
    "enhance_9": "9",
}


def _png() -> bytes:
    image = Image.new("RGB", (640, 360), (255, 255, 255))
    draw = ImageDraw.Draw(image)
    draw.rectangle([40, 90, 200, 300], fill=RED)
    draw.ellipse([240, 110, 400, 270], fill=GREEN)
    draw.polygon([(440, 280), (600, 280), (520, 110)], fill=BLUE)
    draw.text((40, 20), "Sample Graphic", font=ImageFont.load_default(size=32), fill=(0, 0, 0))
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def _tritan_png() -> bytes:
    image = Image.new("RGB", (200, 100), (255, 255, 255))
    draw = ImageDraw.Draw(image)
    draw.rectangle([10, 10, 90, 90], fill=TEAL)
    draw.rectangle([110, 10, 190, 90], fill=LEAF)
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def _use_case(store=None) -> ProcessUpload:
    return ProcessUpload(store or FakeImageStore(), FakeClock(), THRESHOLD, timedelta(hours=24))


class FilterSpy:
    """Wrap the real filters, recording the order, and the arguments of each call."""

    def __init__(self, monkeypatch, module, names=FILTERS) -> None:
        self.order = []
        self.calls = []
        for name, number in names.items():
            if hasattr(module, name):
                monkeypatch.setattr(module, name, self._wrap(number, getattr(module, name)))

    def _wrap(self, number, real):
        def wrapped(*args, **kwargs):
            self.order.append(number)
            self.calls.append((number, args))
            return real(*args, **kwargs)

        return wrapped


def test_upload_with_a_cvd_type_returns_results_and_runs_the_filters_in_order(monkeypatch):
    spy = FilterSpy(monkeypatch, process_upload)
    response = _use_case().execute(ProcessUploadRequest(_png(), DEUTAN))

    assert spy.order == UPLOAD_ORDER
    assert [(pair.a_id, pair.b_id) for pair in response.pairs]
    assert response.enhancement_needed is True
    assert isinstance(response.remaining_pair_count, int)
    assert response.analysis.image_type in ImageType
    assert response.analysis.text and response.analysis.shapes


def test_second_palette_and_detection_use_the_enhanced_pixels(monkeypatch):
    spy = FilterSpy(monkeypatch, process_upload)
    enhance_outputs = []
    real_enhance = process_upload.enhance_9

    def capture(*args, **kwargs):
        result = real_enhance(*args, **kwargs)
        enhance_outputs.append(result)
        return result

    monkeypatch.setattr(process_upload, "enhance_9", capture)
    _use_case().execute(ProcessUploadRequest(_png(), DEUTAN))

    palettes = [call for call in spy.calls if call[0] == "3"]
    detections = [call for call in spy.calls if call[0] == "8"]
    enhanced = enhance_outputs[0].pixels
    assert palettes[1][1][0] is enhanced
    assert detections[1][1][0] is enhanced
    assert detections[1][1][1] is not detections[0][1][1]


def test_pipeline_output_counts_remaining_pairs_from_the_enhanced_image():
    response = _use_case().execute(ProcessUploadRequest(_png(), DEUTAN))
    assert len(response.pairs) >= 1
    assert response.remaining_pair_count < len(response.pairs)


def test_upload_with_no_cvd_stops_after_filter_7(monkeypatch):
    spy = FilterSpy(monkeypatch, process_upload)
    response = _use_case().execute(ProcessUploadRequest(_png(), NONE))

    assert spy.order == NO_CVD_ORDER
    assert response.pairs == ()
    assert response.remaining_pair_count is None
    assert response.enhancement_needed is False
    assert response.analysis.color_items


def test_upload_makes_no_provider_call_and_local_items_start_unverified():
    parameters = inspect.signature(ProcessUpload.__init__).parameters
    assert not any(isinstance(name, str) and "reader" in name for name in parameters)
    assert not hasattr(process_upload, "VisionReader")

    response = _use_case().execute(ProcessUploadRequest(_png(), DEUTAN))
    items = [*response.analysis.text, *response.analysis.shapes]
    assert items
    assert {item.source for item in items} == {ItemSource.LOCAL}
    assert {item.verification for item in items} == {Verification.UNVERIFIED}


def test_local_color_items_are_verified_and_named_by_the_engine():
    response = _use_case().execute(ProcessUploadRequest(_png(), NONE))
    names = {item.name for item in response.analysis.color_items}
    assert {"white", "black"} & names
    assert {item.verification for item in response.analysis.color_items} == {Verification.VERIFIED}
    shape_names = {item.color_name for item in response.analysis.shapes}
    assert shape_names <= names


def test_summary_states_the_type_and_each_count():
    analysis = _use_case().execute(ProcessUploadRequest(_png(), NONE)).analysis
    assert analysis.image_type.value.replace("_", " ") in analysis.summary.casefold()
    for count, noun in (
        (len(analysis.color_items), "color"),
        (len(analysis.regions), "region"),
        (len(analysis.shapes), "shape"),
        (len(analysis.text), "text item"),
    ):
        assert f"{count} {noun}" in analysis.summary


def test_record_holds_hash_expiry_and_a_uuid_hex_id():
    store = FakeImageStore()
    data = _png()
    response = _use_case(store).execute(ProcessUploadRequest(data, NONE))
    stored = store.load(response.image_id)
    assert len(response.image_id) == 32
    assert int(response.image_id, 16) >= 0
    assert stored.record.expires_at == START + timedelta(hours=24)
    assert stored.record.created_at == START
    assert stored.original == data
    assert stored.analysis == response.analysis


def test_same_bytes_have_the_same_hash_and_different_ids():
    store = FakeImageStore()
    use_case = _use_case(store)
    data = _png()
    first = use_case.execute(ProcessUploadRequest(data, NONE)).image_id
    second = use_case.execute(ProcessUploadRequest(data, NONE)).image_id
    assert first != second
    assert store.load(first).record.image_hash == store.load(second).record.image_hash


@pytest.mark.parametrize("data", [b"not an image", b""])
def test_bad_file_raises_invalid_image_and_stores_nothing(data, monkeypatch):
    spy = FilterSpy(monkeypatch, process_upload)
    store = FakeImageStore()
    with pytest.raises(InvalidImage):
        _use_case(store).execute(ProcessUploadRequest(data, DEUTAN))
    assert spy.order == ["1"]
    assert store.images == {}


def test_get_analysis_returns_stored_results_and_refuses_unknown_ids():
    store = FakeImageStore()
    response = _use_case(store).execute(ProcessUploadRequest(_png(), NONE))
    result = GetAnalysis(store).execute(GetAnalysisRequest(response.image_id))
    assert result.analysis == response.analysis
    assert result.analysis.regions
    assert result.analysis.shapes
    assert result.analysis.text
    assert result.analysis.legend == response.analysis.legend
    assert result.analysis.image_type is response.analysis.image_type
    with pytest.raises(ImageNotFound):
        GetAnalysis(store).execute(GetAnalysisRequest("0" * 32))


def test_profile_change_runs_only_filters_8_9_3_8_starting_from_the_stored_palette(monkeypatch):
    store = FakeImageStore()
    upload = _use_case(store).execute(ProcessUploadRequest(_png(), DEUTAN))
    stored_palette = store.load(upload.image_id).analysis.palette

    spy = FilterSpy(monkeypatch, reanalyze_for_profile)
    ReanalyzeForProfile(store, THRESHOLD).execute(ReanalyzeRequest(upload.image_id, TRITAN))

    assert spy.order == REANALYZE_ORDER
    first_detection = next(call for call in spy.calls if call[0] == "8")
    assert first_detection[1][1] is stored_palette
    for name in ("find_regions_4", "find_shapes_5", "read_text_6", "analyze_layout_7"):
        assert not hasattr(reanalyze_for_profile, name)


def test_profile_change_from_deutan_to_tritan_updates_pairs_and_enhanced_image():
    store = FakeImageStore()
    use_case = _use_case(store)
    red_green = use_case.execute(ProcessUploadRequest(_png(), DEUTAN))
    reanalyze = ReanalyzeForProfile(store, THRESHOLD)

    same = reanalyze.execute(ReanalyzeRequest(red_green.image_id, DEUTAN))
    changed = reanalyze.execute(ReanalyzeRequest(red_green.image_id, TRITAN))
    assert same.pairs == red_green.pairs
    assert changed.pairs != same.pairs

    teal = use_case.execute(ProcessUploadRequest(_tritan_png(), DEUTAN))
    assert teal.pairs == ()
    assert reanalyze.execute(ReanalyzeRequest(teal.image_id, TRITAN)).pairs != ()


def test_reanalyze_with_no_cvd_returns_no_pairs(monkeypatch):
    store = FakeImageStore()
    upload = _use_case(store).execute(ProcessUploadRequest(_png(), DEUTAN))
    spy = FilterSpy(monkeypatch, reanalyze_for_profile)
    result = ReanalyzeForProfile(store, THRESHOLD).execute(ReanalyzeRequest(upload.image_id, NONE))
    assert spy.order == []
    assert (result.pairs, result.remaining_pair_count) == ((), None)
    assert result.enhancement_needed is False


def test_reanalyze_unknown_id_raises():
    with pytest.raises(ImageNotFound):
        ReanalyzeForProfile(FakeImageStore(), THRESHOLD).execute(ReanalyzeRequest("0" * 32, DEUTAN))


def test_pixels_are_downscaled_for_analysis_and_the_upload_bytes_are_kept():
    image = Image.fromarray(np.full((4000, 5000, 3), (200, 40, 40), dtype=np.uint8))
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    store = FakeImageStore()
    response = _use_case(store).execute(ProcessUploadRequest(buffer.getvalue(), NONE))
    stored = store.load(response.image_id)
    assert stored.working.shape[0] * stored.working.shape[1] <= 12_000_000
    assert (stored.record.width, stored.record.height) == (5000, 4000)
    assert stored.original == buffer.getvalue()


def test_letters_in_a_title_are_not_listed_as_shapes():
    image = Image.new("RGB", (800, 500), (255, 255, 255))
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default(size=60)
    draw.text((40, 20), "Good Food Zone", font=font, fill=(0, 0, 0))
    draw.ellipse([100, 200, 300, 400], fill=RED)
    draw.rectangle([450, 200, 650, 400], fill=GREEN)
    buffer = BytesIO()
    image.save(buffer, format="PNG")

    analysis = _use_case().execute(ProcessUploadRequest(buffer.getvalue(), NONE)).analysis

    assert analysis.text
    assert sorted(shape.kind for shape in analysis.shapes) == ["circle", "rectangle"]
    assert all(shape.y >= 190 for shape in analysis.shapes)


def test_a_label_inside_a_large_shape_does_not_remove_the_shape():
    image = Image.new("RGB", (800, 500), (255, 255, 255))
    draw = ImageDraw.Draw(image)
    draw.rectangle([100, 100, 700, 400], fill=(200, 220, 250))
    draw.text((300, 230), "Label", font=ImageFont.load_default(size=40), fill=(0, 0, 0))
    buffer = BytesIO()
    image.save(buffer, format="PNG")

    analysis = _use_case().execute(ProcessUploadRequest(buffer.getvalue(), NONE)).analysis

    assert analysis.text
    assert any(shape.width > 500 for shape in analysis.shapes)
