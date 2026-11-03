import json
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from color_engine.models import (
    ConfusablePair,
    ConfusionGroup,
    ConfusionResult8,
    CvdProfile,
    CvdType,
    EnhancedImage9,
)
from color_engine.pipeline.filter_3_palette.extract_palette_3 import extract_palette_3
from color_engine.pipeline.filter_8_confusion.detect_confusion_8 import detect_confusion_8
from color_engine.pipeline.filter_9_enhance.enhance_9 import METHOD, enhance_9

RED, GREEN, GRAY = (220, 30, 30), (30, 150, 30), (240, 240, 240)
THRESHOLD = 10.0
FLAT_GRAPHICS = Path(__file__).parent.parent / "data" / "flat_graphics"
CVD_TYPES = [CvdType.PROTAN, CvdType.DEUTAN, CvdType.TRITAN, CvdType.ACHROMATOPSIA]


def _hand_built() -> tuple[np.ndarray, ConfusionResult8]:
    """A known mask and palette assignment, with no filter 3 or filter 8 involved."""
    pixels = np.hstack([np.full((20, 20, 3), c, dtype=np.uint8) for c in (RED, GREEN, GRAY)])
    color_index = np.zeros(pixels.shape[:2], dtype=np.uint8)
    color_index[:, :20], color_index[:, 20:40], color_index[:, 40:] = 1, 2, 3
    return pixels, ConfusionResult8(
        pairs=(ConfusablePair(1, 2, 70.0, 3.0),),
        groups=(ConfusionGroup(1, (1, 2)),),
        mask=color_index < 3,
        color_index=color_index,
    )


def _changed(before, after):
    return np.any(before != after, axis=-1)


@pytest.mark.parametrize("strength", [0.0, 0.5, 1.0])
def test_no_pixel_changes_outside_the_mask(strength):
    pixels, confusion = _hand_built()
    result = enhance_9(pixels, confusion, strength)
    assert isinstance(result, EnhancedImage9)
    assert not _changed(pixels, result.pixels)[~confusion.mask].any()


def test_strength_zero_returns_the_input_unchanged():
    pixels, confusion = _hand_built()
    result = enhance_9(pixels, confusion, 0.0)
    assert np.array_equal(result.pixels, pixels)
    assert result.pixels is not pixels


def test_output_changes_with_strength_and_stays_inside_the_mask():
    pixels, confusion = _hand_built()
    half = enhance_9(pixels, confusion, 0.5).pixels
    full = enhance_9(pixels, confusion, 1.0).pixels
    assert _changed(pixels, half)[confusion.mask].any()
    assert _changed(half, full)[confusion.mask].any()
    assert not _changed(half, full)[~confusion.mask].any()


def test_default_strength_is_one():
    pixels, confusion = _hand_built()
    assert np.array_equal(
        enhance_9(pixels, confusion).pixels, enhance_9(pixels, confusion, 1.0).pixels
    )


def test_exactly_one_method_ships_and_the_evaluation_names_it():
    pixels, confusion = _hand_built()
    assert enhance_9(pixels, confusion).method == METHOD == "lightness separation"


def test_input_is_not_modified():
    pixels, confusion = _hand_built()
    before = pixels.copy()
    enhance_9(pixels, confusion)
    assert np.array_equal(pixels, before)


def test_empty_mask_returns_a_copy():
    pixels = np.full((4, 4, 3), 90, dtype=np.uint8)
    confusion = ConfusionResult8(
        (), (), np.zeros((4, 4), dtype=bool), np.ones((4, 4), dtype=np.uint8)
    )
    assert np.array_equal(enhance_9(pixels, confusion).pixels, pixels)


@pytest.mark.parametrize("strength", [-0.1, 1.1])
def test_invalid_strength_is_rejected(strength):
    pixels, confusion = _hand_built()
    with pytest.raises(ValueError):
        enhance_9(pixels, confusion, strength)


def test_redetection_on_the_hand_built_result_finds_no_pair():
    pixels, confusion = _hand_built()
    enhanced = enhance_9(pixels, confusion).pixels
    palette = extract_palette_3(enhanced, 12)
    profile = CvdProfile(CvdType.DEUTAN, 1.0)
    assert detect_confusion_8(enhanced, palette, profile, THRESHOLD).pairs == ()


def test_dataset_has_at_least_twenty_labeled_graphics():
    labels = json.loads((FLAT_GRAPHICS / "labels.json").read_text())["images"]
    assert len(labels) >= 20
    for label in labels:
        pixels = np.array(Image.open(FLAT_GRAPHICS / label["file"]).convert("RGB"))
        present = {tuple(color) for color in np.unique(pixels.reshape(-1, 3), axis=0).tolist()}
        assert present == {tuple(color) for color in label["colors"]}, label["file"]


def _dataset_counts() -> dict[CvdType, tuple[int, int]]:
    labels = json.loads((FLAT_GRAPHICS / "labels.json").read_text())["images"]
    counts = {cvd_type: (0, 0) for cvd_type in CVD_TYPES}
    for label in labels:
        pixels = np.array(Image.open(FLAT_GRAPHICS / label["file"]).convert("RGB"))
        palette = extract_palette_3(pixels, 12)
        for cvd_type in CVD_TYPES:
            profile = CvdProfile(cvd_type, 1.0)
            confusion = detect_confusion_8(pixels, palette, profile, THRESHOLD)
            enhanced = enhance_9(pixels, confusion).pixels
            assert not _changed(pixels, enhanced)[~confusion.mask].any()
            remaining = detect_confusion_8(
                enhanced, extract_palette_3(enhanced, 12), profile, THRESHOLD
            )
            before, after = counts[cvd_type]
            counts[cvd_type] = (before + len(confusion.pairs), after + len(remaining.pairs))
    return counts


def test_enhancement_reduces_pairs_by_at_least_80_percent_on_the_dataset():
    counts = _dataset_counts()
    before = sum(pair[0] for pair in counts.values())
    after = sum(pair[1] for pair in counts.values())
    print(f"SRS-NFR-024: {before} pairs before, {after} after, {1 - after / before:.1%} reduction")
    assert all(pair[0] > 0 for pair in counts.values()), "each CVD type must have flagged pairs"
    assert 1 - after / before >= 0.80
