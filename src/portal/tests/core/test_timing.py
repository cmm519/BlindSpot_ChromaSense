"""Measure the speed targets. The Compose service limits this container to 4 CPUs and 8 GB."""

import time
from datetime import timedelta
from io import BytesIO

import numpy as np
import pytest
from fakes import FakeClock, FakeImageStore
from PIL import Image, ImageDraw, ImageFont

from chromasense.core.use_cases.export_image import ExportImage, ExportImageRequest
from chromasense.core.use_cases.process_upload import ProcessUpload, ProcessUploadRequest
from color_engine.models import CvdProfile, CvdType, DecodedImage1
from color_engine.pipeline.filter_2_downscale.downscale_2 import downscale_2
from color_engine.pipeline.filter_3_palette.extract_palette_3 import extract_palette_3
from color_engine.pipeline.filter_4_regions.find_regions_4 import find_regions_4
from color_engine.pipeline.filter_5_shapes.find_shapes_5 import find_shapes_5
from color_engine.pipeline.filter_6_text.read_text_6 import read_text_6
from color_engine.pipeline.filter_7_layout.analyze_layout_7 import analyze_layout_7
from color_engine.pipeline.filter_8_confusion.detect_confusion_8 import detect_confusion_8
from color_engine.pipeline.filter_9_enhance.enhance_9 import enhance_9
from color_engine.rules.simulation import simulate

DEUTAN = CvdProfile(CvdType.DEUTAN, 1.0)
THRESHOLD = 10.0


def _chart(width: int, height: int) -> np.ndarray:
    """A chart-like image with confusable fills, a legend, axes, and text, scaled to its size."""
    image = Image.new("RGB", (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(image)
    unit = width / 100
    colors = [(220, 30, 30), (30, 150, 30), (40, 70, 200), (240, 180, 20)]
    font = ImageFont.load_default(size=max(12, int(3 * unit)))
    draw.text((5 * unit, 2 * unit), "Quarterly Sales by Region", font=font, fill=(0, 0, 0))
    draw.line([(10 * unit, 10 * unit), (10 * unit, height - 10 * unit)], fill=(0, 0, 0), width=2)
    draw.line(
        [(10 * unit, height - 10 * unit), (70 * unit, height - 10 * unit)],
        fill=(0, 0, 0),
        width=2,
    )
    for bar in range(8):
        left = (12 + bar * 7) * unit
        top = height - 10 * unit - (bar % 4 + 1) * (height - 25 * unit) / 4
        draw.rectangle([left, top, left + 5 * unit, height - 10 * unit], fill=colors[bar % 4])
    for row, color in enumerate(colors):
        top = (15 + row * 7) * unit
        draw.rectangle([75 * unit, top, 79 * unit, top + 4 * unit], fill=color)
        draw.text((81 * unit, top), f"Series {row + 1}", font=font, fill=(0, 0, 0))
    return np.array(image)


def _png(pixels: np.ndarray) -> bytes:
    buffer = BytesIO()
    Image.fromarray(pixels).save(buffer, format="PNG")
    return buffer.getvalue()


def _timed(action) -> float:
    start = time.perf_counter()
    action()
    return time.perf_counter() - start


def _best_of(runs: int, action) -> float:
    """The first run pays for one-time set up, such as model loading and lookup tables."""
    return min(_timed(action) for _ in range(runs))


@pytest.fixture(scope="module")
def two_megapixels():
    pixels = _chart(1732, 1155)
    return pixels, extract_palette_3(pixels, 12)


@pytest.fixture(scope="module")
def twelve_megapixels():
    pixels = _chart(4000, 3000)
    return pixels, extract_palette_3(pixels, 12)


def test_simulation_and_enhancement_of_two_megapixels_take_under_one_second(two_megapixels):
    pixels, palette = two_megapixels

    def work():
        simulate(pixels, DEUTAN)
        confusion = detect_confusion_8(pixels, palette, DEUTAN, THRESHOLD)
        enhance_9(pixels, confusion)

    seconds = _best_of(3, work)
    print(f"SRS-NFR-001: {seconds:.3f} s on {pixels.shape[1]}x{pixels.shape[0]}")
    assert seconds < 1.0


def test_detection_on_a_downscaled_image_takes_under_500_milliseconds(twelve_megapixels):
    pixels, palette = twelve_megapixels
    seconds = _best_of(3, lambda: detect_confusion_8(pixels, palette, DEUTAN, THRESHOLD))
    print(f"SRS-NFR-003: {seconds * 1000:.0f} ms on {pixels.shape[1]}x{pixels.shape[0]}")
    assert seconds < 0.5


def test_export_of_twelve_megapixels_takes_under_five_seconds(twelve_megapixels):
    pixels, _ = twelve_megapixels
    store = FakeImageStore()
    upload = ProcessUpload(store, FakeClock(), THRESHOLD, timedelta(hours=24))
    image_id = upload.execute(ProcessUploadRequest(_png(pixels), DEUTAN)).image_id
    export = ExportImage(store, THRESHOLD)
    seconds = _best_of(2, lambda: export.execute(ExportImageRequest(image_id, DEUTAN)))
    print(f"SRS-NFR-002: {seconds:.3f} s on {pixels.shape[1]}x{pixels.shape[0]}")
    assert seconds < 5.0


def test_local_analysis_of_twelve_megapixels_takes_under_ten_seconds(twelve_megapixels):
    pixels, _ = twelve_megapixels
    decoded = DecodedImage1(pixels, pixels.shape[1], pixels.shape[0])
    steps = {}

    def work():
        working = downscale_2(decoded, 12.0).pixels
        started = time.perf_counter()
        palette = extract_palette_3(working, 12)
        steps["palette"] = time.perf_counter() - started
        started = time.perf_counter()
        regions = find_regions_4(working, palette)
        steps["regions"] = time.perf_counter() - started
        started = time.perf_counter()
        find_shapes_5(regions)
        steps["shapes"] = time.perf_counter() - started
        started = time.perf_counter()
        text = read_text_6(working)
        steps["text"] = time.perf_counter() - started
        started = time.perf_counter()
        analyze_layout_7(working, palette, regions, text)
        steps["layout"] = time.perf_counter() - started

    seconds = _best_of(2, work)
    detail = ", ".join(f"{name} {value:.2f}" for name, value in steps.items())
    print(f"SRS-NFR-041: {seconds:.3f} s on {pixels.shape[1]}x{pixels.shape[0]} ({detail})")
    assert seconds < 10.0
