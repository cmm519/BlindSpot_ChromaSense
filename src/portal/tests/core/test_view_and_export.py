from datetime import timedelta
from io import BytesIO

import numpy as np
import pytest
from fakes import FakeClock, FakeImageStore
from PIL import Image

from chromasense.core.errors import ImageNotFound, InvalidCoordinates, NoEnhancementForProfile
from chromasense.core.use_cases.export_image import ExportImage, ExportImageRequest
from chromasense.core.use_cases.identify_color import IdentifyColor, IdentifyColorRequest
from chromasense.core.use_cases.process_upload import ProcessUpload, ProcessUploadRequest
from chromasense.core.use_cases.render_view import RenderView, RenderViewRequest
from color_engine.models import CvdProfile, CvdType
from color_engine.pipeline.filter_1_decode.decode_1 import decode_1
from color_engine.pipeline.filter_3_palette.extract_palette_3 import extract_palette_3
from color_engine.pipeline.filter_8_confusion.detect_confusion_8 import detect_confusion_8
from color_engine.pipeline.filter_9_enhance.enhance_9 import enhance_9
from color_engine.rules.naming import ColorNamer

RED, GREEN, WHITE = (220, 30, 30), (30, 150, 30), (255, 255, 255)
THRESHOLD = 10.0
DEUTAN = CvdProfile(CvdType.DEUTAN, 1.0)
TRITAN = CvdProfile(CvdType.TRITAN, 1.0)
NONE = CvdProfile(CvdType.NONE)


def _png(width=300, height=200) -> bytes:
    pixels = np.full((height, width, 3), WHITE, dtype=np.uint8)
    pixels[height // 10 : height // 2, width // 10 : width // 2] = RED
    pixels[height // 2 : 9 * height // 10, width // 2 : 9 * width // 10] = GREEN
    buffer = BytesIO()
    Image.fromarray(pixels).save(buffer, format="PNG")
    return buffer.getvalue()


def _uploaded(data=None):
    store = FakeImageStore()
    upload = ProcessUpload(store, FakeClock(), THRESHOLD, timedelta(hours=24))
    response = upload.execute(ProcessUploadRequest(data or _png(), NONE))
    return store, response.image_id


def _decode(png: bytes) -> np.ndarray:
    with Image.open(BytesIO(png)) as image:
        assert image.format == "PNG"
        return np.array(image.convert("RGB"))


def _render(store, image_id, view, profile=DEUTAN, strength=1.0) -> np.ndarray:
    use_case = RenderView(store, THRESHOLD)
    request = RenderViewRequest(image_id, view, profile, strength)
    return _decode(use_case.execute(request).png)


def test_original_view_returns_the_working_copy():
    store, image_id = _uploaded()
    assert np.array_equal(_render(store, image_id, "original"), store.load(image_id).working)


def test_simulated_view_changes_with_the_profile():
    store, image_id = _uploaded()
    deutan = _render(store, image_id, "simulated", DEUTAN)
    tritan = _render(store, image_id, "simulated", TRITAN)
    assert not np.array_equal(deutan, tritan)
    assert not np.array_equal(deutan, store.load(image_id).working)


def test_simulated_view_with_no_cvd_returns_the_original():
    store, image_id = _uploaded()
    assert np.array_equal(_render(store, image_id, "simulated", NONE), store.load(image_id).working)


def test_enhanced_view_changes_only_flagged_colors_and_follows_strength():
    store, image_id = _uploaded()
    original = store.load(image_id).working
    full = _render(store, image_id, "enhanced")
    half = _render(store, image_id, "enhanced", strength=0.5)
    zero = _render(store, image_id, "enhanced", strength=0.0)

    assert not np.array_equal(full, original)
    assert not np.array_equal(full, half)
    assert np.array_equal(zero, original)
    white = np.all(original == WHITE, axis=-1)
    assert np.array_equal(full[white], original[white])


def test_overlay_view_adds_patterns_to_the_enhanced_image():
    store, image_id = _uploaded()
    original = store.load(image_id).working
    enhanced = _render(store, image_id, "enhanced")
    overlay = _render(store, image_id, "overlay")
    assert not np.array_equal(enhanced, overlay)
    white = np.all(original == WHITE, axis=-1)
    assert np.array_equal(overlay[white], original[white])


@pytest.mark.parametrize("view", ["enhanced", "overlay"])
def test_enhanced_and_overlay_need_a_cvd_type(view):
    store, image_id = _uploaded()
    with pytest.raises(NoEnhancementForProfile):
        _render(store, image_id, view, NONE)


def test_preview_is_at_most_two_megapixels():
    store, image_id = _uploaded(_png(2000, 1500))
    preview = _render(store, image_id, "original")
    assert preview.shape[0] * preview.shape[1] <= 2_000_000
    assert preview.shape[1] / preview.shape[0] == pytest.approx(2000 / 1500, abs=0.01)


def test_rendered_views_are_not_stored():
    store, image_id = _uploaded()
    before = store.images[image_id]
    _render(store, image_id, "enhanced")
    assert store.images[image_id] is before


def test_unknown_image_is_refused_by_each_use_case():
    store = FakeImageStore()
    missing = "0" * 32
    with pytest.raises(ImageNotFound):
        RenderView(store, THRESHOLD).execute(RenderViewRequest(missing, "original", NONE))
    with pytest.raises(ImageNotFound):
        IdentifyColor(store).execute(IdentifyColorRequest(missing, 0, 0, NONE))
    with pytest.raises(ImageNotFound):
        ExportImage(store, THRESHOLD).execute(ExportImageRequest(missing, DEUTAN))


def test_identify_returns_the_known_color_with_values_from_the_namer():
    store, image_id = _uploaded()
    result = IdentifyColor(store).execute(IdentifyColorRequest(image_id, 60, 50, NONE))
    assert result.color == ColorNamer().describe(RED)
    assert result.color.rgb == RED
    assert result.color.hex == "#DC1E1E"
    assert result.color.family == "red"


def test_identify_simulated_value_changes_with_the_profile_and_is_none_with_no_cvd():
    store, image_id = _uploaded()
    use_case = IdentifyColor(store)
    deutan = use_case.execute(IdentifyColorRequest(image_id, 60, 50, DEUTAN))
    tritan = use_case.execute(IdentifyColorRequest(image_id, 60, 50, TRITAN))
    none = use_case.execute(IdentifyColorRequest(image_id, 60, 50, NONE))
    assert deutan.simulated_rgb != tritan.simulated_rgb
    assert deutan.simulated_hex.startswith("#")
    assert none.simulated_rgb is None
    assert none.simulated_hex is None


@pytest.mark.parametrize("point", [(-1, 0), (0, -1), (300, 0), (0, 200)])
def test_identify_refuses_a_point_outside_the_image(point):
    store, image_id = _uploaded()
    with pytest.raises(InvalidCoordinates):
        IdentifyColor(store).execute(IdentifyColorRequest(image_id, *point, NONE))


def test_export_of_a_twenty_megapixel_upload_keeps_the_original_dimensions():
    store, image_id = _uploaded(_png(5000, 4000))
    png = ExportImage(store, THRESHOLD).execute(ExportImageRequest(image_id, DEUTAN)).png
    with Image.open(BytesIO(png)) as image:
        assert image.size == (5000, 4000)
    assert store.load(image_id).working.shape[1] < 5000


def test_export_decodes_to_the_enhanced_image_from_the_original_pixels():
    store, image_id = _uploaded()
    stored = store.load(image_id)
    png = ExportImage(store, THRESHOLD).execute(ExportImageRequest(image_id, DEUTAN)).png
    pixels = decode_1(stored.original).pixels
    confusion = detect_confusion_8(pixels, stored.analysis.palette, DEUTAN, THRESHOLD)
    assert np.array_equal(_decode(png), enhance_9(pixels, confusion).pixels)
    remaining = detect_confusion_8(
        _decode(png), extract_palette_3(_decode(png), 12), DEUTAN, THRESHOLD
    )
    assert len(remaining.pairs) < len(confusion.pairs)


def test_export_strength_changes_the_result():
    store, image_id = _uploaded()
    use_case = ExportImage(store, THRESHOLD)
    full = use_case.execute(ExportImageRequest(image_id, DEUTAN, 1.0)).png
    half = use_case.execute(ExportImageRequest(image_id, DEUTAN, 0.5)).png
    assert not np.array_equal(_decode(full), _decode(half))


def test_export_needs_a_cvd_type():
    store, image_id = _uploaded()
    with pytest.raises(NoEnhancementForProfile):
        ExportImage(store, THRESHOLD).execute(ExportImageRequest(image_id, NONE))
