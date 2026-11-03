import ast
from pathlib import Path

import numpy as np
import pytest
from daltonlens.simulate import Deficiency, Simulator_Brettel1997, Simulator_Machado2009
from PIL import Image

import color_engine
from color_engine.models import CvdProfile, CvdType
from color_engine.rules import simulation
from color_engine.rules.color_spaces import linear_to_srgb, srgb_to_linear
from color_engine.rules.simulation import simulate

TOLERANCE = 0.01
DATA = Path(__file__).parent.parent / "data"
TABLE_SEVERITIES = [0.0, 0.1, 0.3, 0.5, 0.7, 0.9, 1.0]


def _gradient() -> np.ndarray:
    red, green = np.meshgrid(np.linspace(0, 255, 64), np.linspace(0, 255, 64))
    blue = np.linspace(255, 0, 64)[np.newaxis, :].repeat(64, axis=0)
    return np.rint(np.dstack([red, green, blue])).astype(np.uint8)


def _flat() -> np.ndarray:
    colors = np.array(
        [[230, 25, 75], [60, 180, 75], [255, 225, 25], [0, 130, 200], [128, 128, 128]],
        dtype=np.uint8,
    )
    return np.repeat(colors[np.newaxis, :, :], 16, axis=0)


def _file_image() -> np.ndarray:
    return np.array(Image.open(DATA / "simulation_fixture.png").convert("RGB"))


IMAGES = {"gradient": _gradient, "flat": _flat, "file": _file_image}


def _difference(actual: np.ndarray, reference: np.ndarray) -> float:
    return float(np.mean(np.abs(actual.astype(float) - reference.astype(float))) / 255)


@pytest.mark.parametrize("image", IMAGES)
@pytest.mark.parametrize("severity", TABLE_SEVERITIES)
@pytest.mark.parametrize(
    ("cvd_type", "deficiency"),
    [(CvdType.PROTAN, Deficiency.PROTAN), (CvdType.DEUTAN, Deficiency.DEUTAN)],
)
def test_machado_matches_reference(image, severity, cvd_type, deficiency):
    pixels = IMAGES[image]()
    reference = Simulator_Machado2009().simulate_cvd(pixels, deficiency, severity)
    assert _difference(simulate(pixels, CvdProfile(cvd_type, severity)), reference) < TOLERANCE


@pytest.mark.parametrize("cvd_type", [CvdType.PROTAN, CvdType.DEUTAN])
def test_machado_interpolates_halfway_between_table_rows(cvd_type):
    pixels = _gradient()
    low = srgb_to_linear(simulate(pixels, CvdProfile(cvd_type, 0.3)))
    high = srgb_to_linear(simulate(pixels, CvdProfile(cvd_type, 0.4)))
    middle = simulate(pixels, CvdProfile(cvd_type, 0.35))
    expected = np.rint(linear_to_srgb((low + high) / 2) * 255)
    assert _difference(middle, expected) < TOLERANCE


@pytest.mark.parametrize("image", IMAGES)
@pytest.mark.parametrize("severity", [0.0, 0.25, 0.5, 0.75, 1.0])
def test_brettel_tritan_matches_reference(image, severity):
    pixels = IMAGES[image]()
    reference = Simulator_Brettel1997().simulate_cvd(pixels, Deficiency.TRITAN, severity)
    actual = simulate(pixels, CvdProfile(CvdType.TRITAN, severity))
    assert _difference(actual, reference) < TOLERANCE


def test_tritan_planes_match_published_constants():
    plane_a, plane_b, separation = simulation._tritan_planes()
    assert np.allclose(plane_a[2, :2], [-0.00213, 0.05477], atol=1e-4)
    assert np.allclose(plane_b[2, :2], [-0.06195, 0.16826], atol=1e-4)
    assert np.allclose(separation[:2], [0.34516, -0.65480], atol=1e-4)


@pytest.mark.parametrize("image", IMAGES)
def test_achromatopsia_has_equal_channels_equal_to_luminance(image):
    pixels = IMAGES[image]()
    result = simulate(pixels, CvdProfile(CvdType.ACHROMATOPSIA, 1.0))
    assert np.array_equal(result[..., 0], result[..., 1])
    assert np.array_equal(result[..., 1], result[..., 2])

    linear = srgb_to_linear(pixels)
    luminance = 0.2126 * linear[..., 0] + 0.7152 * linear[..., 1] + 0.0722 * linear[..., 2]
    expected = np.rint(linear_to_srgb(luminance) * 255)
    assert np.array_equal(result[..., 0], expected)


def test_achromatopsia_ignores_severity():
    pixels = _gradient()
    assert np.array_equal(
        simulate(pixels, CvdProfile(CvdType.ACHROMATOPSIA, 0.0)),
        simulate(pixels, CvdProfile(CvdType.ACHROMATOPSIA, 1.0)),
    )


@pytest.mark.parametrize("cvd_type", [CvdType.PROTAN, CvdType.DEUTAN, CvdType.TRITAN])
def test_model_runs_between_linearize_and_reencode(monkeypatch, cvd_type):
    calls = []
    real_to_linear = simulation.srgb_to_linear
    real_to_srgb = simulation.linear_to_srgb

    def spy_to_linear(values):
        calls.append("linearize")
        return real_to_linear(values)

    def spy_to_srgb(values):
        calls.append("encode")
        return real_to_srgb(values)

    def spy_model(name, real):
        def wrapped(*args):
            calls.append("model")
            return real(*args)

        monkeypatch.setattr(simulation, name, wrapped)

    monkeypatch.setattr(simulation, "srgb_to_linear", spy_to_linear)
    monkeypatch.setattr(simulation, "linear_to_srgb", spy_to_srgb)
    model_name = "_tritan" if cvd_type is CvdType.TRITAN else "_machado_matrix"
    spy_model(model_name, getattr(simulation, model_name))

    pixels = _flat()
    result = simulate(pixels, CvdProfile(cvd_type, 1.0))

    assert calls == ["linearize", "model", "encode"]
    if cvd_type is CvdType.TRITAN:
        reference = Simulator_Brettel1997().simulate_cvd(pixels, Deficiency.TRITAN, 1.0)
    else:
        deficiency = Deficiency.PROTAN if cvd_type is CvdType.PROTAN else Deficiency.DEUTAN
        reference = Simulator_Machado2009().simulate_cvd(pixels, deficiency, 1.0)
    assert _difference(result, reference) < TOLERANCE


def test_matrix_is_applied_to_linear_values_not_encoded_values():
    pixel = np.array([[[200, 100, 50]]], dtype=np.uint8)
    matrix = np.array(simulation._machado_tables()["deutan"][10])
    linear = srgb_to_linear(pixel)[0, 0]
    expected = np.rint(linear_to_srgb(matrix @ linear) * 255)
    assert np.array_equal(simulate(pixel, CvdProfile(CvdType.DEUTAN, 1.0))[0, 0], expected)


@pytest.mark.parametrize("cvd_type", [CvdType.PROTAN, CvdType.DEUTAN, CvdType.TRITAN])
def test_severity_zero_leaves_the_image_unchanged(cvd_type):
    pixels = _gradient()
    assert np.array_equal(simulate(pixels, CvdProfile(cvd_type, 0.0)), pixels)


@pytest.mark.parametrize("cvd_type", [CvdType.PROTAN, CvdType.DEUTAN, CvdType.TRITAN])
@pytest.mark.parametrize("severity", [0.0, 0.5, 1.0])
@pytest.mark.parametrize("level", [0, 128, 255])
def test_neutral_pixels_keep_their_value(cvd_type, severity, level):
    pixel = np.full((1, 1, 3), level, dtype=np.uint8)
    result = simulate(pixel, CvdProfile(cvd_type, severity))
    assert np.abs(result.astype(int) - level).max() <= 1


def test_red_and_green_converge_under_full_deutan():
    pixels = np.array([[[220, 30, 30], [30, 150, 30]]], dtype=np.uint8)
    before = np.abs(pixels[0, 0].astype(int) - pixels[0, 1].astype(int)).sum()
    result = simulate(pixels, CvdProfile(CvdType.DEUTAN, 1.0))
    after = np.abs(result[0, 0].astype(int) - result[0, 1].astype(int)).sum()
    assert after < before / 2


def test_none_returns_a_copy():
    pixels = _flat()
    result = simulate(pixels, CvdProfile(CvdType.NONE))
    assert np.array_equal(result, pixels)
    assert result is not pixels
    result[0, 0, 0] = 1
    assert pixels[0, 0, 0] == 230


def test_rejects_non_uint8_input():
    with pytest.raises(ValueError):
        simulate(np.zeros((2, 2, 3), dtype=float), CvdProfile(CvdType.DEUTAN, 1.0))


def test_color_engine_source_does_not_import_daltonlens():
    package = Path(color_engine.__file__).parent
    for path in package.rglob("*.py"):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            names = []
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                names = [node.module or ""]
            assert not any(name.split(".")[0] == "daltonlens" for name in names), path
