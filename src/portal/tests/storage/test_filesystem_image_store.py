from datetime import UTC, datetime, timedelta
from io import BytesIO

import numpy as np
import pytest
from PIL import Image, ImageDraw, ImageFont

from chromasense.core.models import ImageRecord
from chromasense.core.use_cases.get_analysis import GetAnalysis, GetAnalysisRequest
from chromasense.core.use_cases.process_upload import ProcessUpload, ProcessUploadRequest
from chromasense.storage.filesystem_image_store import FilesystemImageStore
from color_engine.models import CvdProfile, CvdType

NOW = datetime(2026, 1, 1, tzinfo=UTC)
ID_A, ID_B = "a" * 32, "b" * 32
NO_CVD = CvdProfile(CvdType.NONE)


class FixedClock:
    def now(self):
        return NOW


def _record(image_id=ID_A, expires_in=timedelta(hours=1)) -> ImageRecord:
    return ImageRecord(image_id, "hash", 4, 2, NOW, NOW + expires_in)


def _working() -> np.ndarray:
    return np.arange(24, dtype=np.uint8).reshape(2, 4, 3)


def _sample_png() -> bytes:
    image = Image.new("RGB", (640, 320), (255, 255, 255))
    draw = ImageDraw.Draw(image)
    draw.rectangle([40, 90, 200, 280], fill=(220, 30, 30))
    draw.ellipse([300, 100, 480, 280], fill=(30, 150, 30))
    draw.text((40, 20), "Sample Graphic", font=ImageFont.load_default(size=32), fill=(0, 0, 0))
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def test_save_and_load_keep_the_bytes_pixels_and_record(tmp_path):
    store = FilesystemImageStore(tmp_path)
    store.save(_record(), b"original bytes", _working())
    loaded = store.load(ID_A)
    assert loaded.record == _record()
    assert loaded.original == b"original bytes"
    assert np.array_equal(loaded.working, _working())
    assert loaded.analysis is None


def test_layout_on_disk(tmp_path):
    store = FilesystemImageStore(tmp_path)
    store.save(_record(), b"x", _working())
    names = {path.name for path in (tmp_path / "images" / ID_A).iterdir()}
    assert names == {"original.bin", "working.png", "record.json"}


def test_analysis_survives_a_round_trip_through_json(tmp_path):
    store = FilesystemImageStore(tmp_path)
    use_case = ProcessUpload(store, FixedClock(), 10.0, timedelta(hours=24))
    response = use_case.execute(ProcessUploadRequest(_sample_png(), NO_CVD))
    assert response.analysis.text and response.analysis.shapes
    assert GetAnalysis(store).execute(GetAnalysisRequest(response.image_id)).analysis == (
        response.analysis
    )
    names = {path.name for path in (tmp_path / "images" / response.image_id).iterdir()}
    assert names == {"original.bin", "working.png", "record.json", "analysis.json"}


@pytest.mark.parametrize(
    "image_id",
    ["../secret", "A" * 32, "a" * 31, "a" * 33, "", "a" * 31 + "/", "..", "a" * 32 + "\n"],
)
def test_load_refuses_an_id_of_the_wrong_form(tmp_path, image_id):
    store = FilesystemImageStore(tmp_path)
    assert store.load(image_id) is None


def test_id_with_a_trailing_newline_is_not_a_valid_folder(tmp_path):
    store = FilesystemImageStore(tmp_path)
    store.save(_record(), b"x", _working())
    assert store.load(ID_A + "\n") is None


def test_save_refuses_an_id_of_the_wrong_form_and_leaves_nothing(tmp_path):
    store = FilesystemImageStore(tmp_path)
    with pytest.raises(ValueError):
        store.save(_record(image_id="../secret"), b"x", _working())
    assert list((tmp_path / "images").iterdir()) == []


def test_load_unknown_id_returns_none(tmp_path):
    assert FilesystemImageStore(tmp_path).load(ID_A) is None


def test_failed_write_leaves_no_partial_image(tmp_path):
    store = FilesystemImageStore(tmp_path)
    with pytest.raises(AttributeError):
        store.save(_record(), b"x", "not pixels")
    assert store.load(ID_A) is None
    assert list((tmp_path / "images").iterdir()) == []


def test_delete_expired_removes_at_or_before_now_and_keeps_later(tmp_path):
    store = FilesystemImageStore(tmp_path)
    store.save(_record(ID_A, timedelta(hours=1)), b"x", _working())
    store.save(_record(ID_B, timedelta(hours=2)), b"x", _working())

    assert store.delete_expired(NOW + timedelta(minutes=59)) == 0
    assert store.delete_expired(NOW + timedelta(hours=1)) == 1
    assert store.load(ID_A) is None
    assert not (tmp_path / "images" / ID_A).exists()
    assert store.load(ID_B) is not None


def test_delete_expired_ignores_a_temporary_folder(tmp_path):
    store = FilesystemImageStore(tmp_path)
    (tmp_path / "images" / ".tmp-partial").mkdir()
    assert store.delete_expired(NOW) == 0


def test_twenty_megapixel_upload_is_analyzed_small_and_the_original_keeps_its_size(tmp_path):
    image = Image.new("RGB", (5000, 4000), (255, 255, 255))
    draw = ImageDraw.Draw(image)
    draw.rectangle([500, 500, 2000, 3000], fill=(220, 30, 30))
    draw.ellipse([2500, 500, 4500, 2500], fill=(30, 150, 30))
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    data = buffer.getvalue()
    assert len(data) < 10_000_000

    store = FilesystemImageStore(tmp_path)
    use_case = ProcessUpload(store, FixedClock(), 10.0, timedelta(hours=24))
    response = use_case.execute(ProcessUploadRequest(data, NO_CVD))

    loaded = store.load(response.image_id)
    assert loaded.working.shape[0] * loaded.working.shape[1] <= 12_000_000
    assert loaded.original == data
    with Image.open(BytesIO(loaded.original)) as original:
        assert original.size == (5000, 4000)
