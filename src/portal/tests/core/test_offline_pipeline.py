"""Run every feature except AI. Increment 27 runs this file in a container with no network."""

from datetime import timedelta
from io import BytesIO

import numpy as np
from fakes import FakeClock
from PIL import Image, ImageDraw, ImageFont

from chromasense.core.use_cases.export_image import ExportImage, ExportImageRequest
from chromasense.core.use_cases.get_analysis import GetAnalysis, GetAnalysisRequest
from chromasense.core.use_cases.identify_color import IdentifyColor, IdentifyColorRequest
from chromasense.core.use_cases.process_upload import ProcessUpload, ProcessUploadRequest
from chromasense.core.use_cases.reanalyze_for_profile import ReanalyzeForProfile, ReanalyzeRequest
from chromasense.core.use_cases.render_view import RenderView, RenderViewRequest
from chromasense.storage.filesystem_image_store import FilesystemImageStore
from color_engine.models import CvdProfile, CvdType

DEUTAN = CvdProfile(CvdType.DEUTAN, 1.0)
THRESHOLD = 10.0


def _png() -> bytes:
    image = Image.new("RGB", (640, 360), (255, 255, 255))
    draw = ImageDraw.Draw(image)
    draw.text((30, 20), "Offline Graphic", font=ImageFont.load_default(size=32), fill=(0, 0, 0))
    draw.rectangle([30, 90, 250, 320], fill=(220, 30, 30))
    draw.ellipse([320, 100, 540, 320], fill=(30, 150, 30))
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def _decode(png: bytes) -> np.ndarray:
    with Image.open(BytesIO(png)) as image:
        return np.array(image.convert("RGB"))


def test_every_feature_except_ai_completes(tmp_path):
    store = FilesystemImageStore(tmp_path)
    upload = ProcessUpload(store, FakeClock(), THRESHOLD, timedelta(hours=24))

    uploaded = upload.execute(ProcessUploadRequest(_png(), DEUTAN))
    image_id = uploaded.image_id
    assert uploaded.pairs

    analysis = GetAnalysis(store).execute(GetAnalysisRequest(image_id)).analysis
    assert analysis.regions and analysis.shapes and analysis.text

    render = RenderView(store, THRESHOLD)
    original = _decode(render.execute(RenderViewRequest(image_id, "original", DEUTAN)).png)
    simulated = _decode(render.execute(RenderViewRequest(image_id, "simulated", DEUTAN)).png)
    enhanced = _decode(render.execute(RenderViewRequest(image_id, "enhanced", DEUTAN)).png)
    assert not np.array_equal(original, simulated)
    assert not np.array_equal(original, enhanced)

    color = IdentifyColor(store).execute(IdentifyColorRequest(image_id, 100, 200, DEUTAN))
    assert color.color.rgb == (220, 30, 30)
    assert color.color.name

    export = ExportImage(store, THRESHOLD).execute(ExportImageRequest(image_id, DEUTAN))
    assert _decode(export.png).shape == original.shape

    changed = ReanalyzeForProfile(store, THRESHOLD).execute(
        ReanalyzeRequest(image_id, CvdProfile(CvdType.TRITAN, 1.0))
    )
    assert changed.pairs != uploaded.pairs
