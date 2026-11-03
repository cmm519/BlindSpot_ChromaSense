"""CVD simulation. Every model is applied in linear RGB."""

import json
from functools import cache
from importlib import resources

import numpy as np
from numpy.typing import NDArray

from color_engine.models import CvdProfile, CvdType
from color_engine.rules.color_spaces import linear_to_srgb, srgb_to_linear

_REC709_LUMINANCE = np.array([0.2126, 0.7152, 0.0722])

# Smith and Pokorny (1975) cone fundamentals with the sRGB primaries.
_LMS_FROM_LINEAR = np.array(
    [
        [0.1788595581, 0.439971169898, 0.035965767024],
        [0.03380393502, 0.275152424014, 0.036206345976],
        [0.00031087464, 0.00191660736, 0.015280889928],
    ]
)
_LINEAR_FROM_LMS = np.linalg.inv(_LMS_FROM_LINEAR)
_LMS_FROM_XYZ = np.array(
    [
        [0.15514, 0.54312, -0.03286],
        [-0.15514, 0.45684, 0.03286],
        [0.0, 0.0, 0.01608],
    ]
)
# Brettel (1997) anchors for tritanopia, as CIE XYZ of the 485 nm and 660 nm stimuli.
_XYZ_485NM = np.array([0.05795, 0.1693, 0.6162])
_XYZ_660NM = np.array([0.1649, 0.0610, 0.0])


def simulate(pixels: NDArray[np.uint8], profile: CvdProfile) -> NDArray[np.uint8]:
    """Return how an sRGB uint8 image of shape (H, W, 3) appears under the profile."""
    image = np.asarray(pixels)
    if image.dtype != np.uint8 or image.ndim < 1 or image.shape[-1] != 3:
        raise ValueError("pixels must be a uint8 RGB array")
    if profile.type is CvdType.NONE:
        return image.copy()

    linear = srgb_to_linear(image)
    if profile.type is CvdType.ACHROMATOPSIA:
        simulated = _achromatopsia(linear)
    elif profile.type is CvdType.TRITAN:
        simulated = _tritan(linear, profile.severity)
    else:
        simulated = linear @ _machado_matrix(profile.type, profile.severity).T
    return np.rint(linear_to_srgb(simulated) * 255).astype(np.uint8)


def _achromatopsia(linear: NDArray) -> NDArray:
    luminance = linear @ _REC709_LUMINANCE
    return np.repeat(luminance[..., np.newaxis], 3, axis=-1)


@cache
def _machado_tables() -> dict[str, NDArray]:
    source = resources.files("color_engine").joinpath("data/machado_2009.json")
    data = json.loads(source.read_text(encoding="utf-8"))
    return {key: np.array(data[key]) for key in ("protan", "deutan")}


def _machado_matrix(cvd_type: CvdType, severity: float) -> NDArray:
    tables = _machado_tables()[cvd_type.value]
    position = severity * (len(tables) - 1)
    lower = min(int(position), len(tables) - 2)
    weight = position - lower
    return (1.0 - weight) * tables[lower] + weight * tables[lower + 1]


@cache
def _tritan_planes() -> tuple[NDArray, NDArray, NDArray]:
    """Return the projections onto Brettel's two half planes, and their separating normal."""
    neutral = _LMS_FROM_LINEAR @ np.ones(3)
    wing_a = _LMS_FROM_XYZ @ _XYZ_485NM
    wing_b = _LMS_FROM_XYZ @ _XYZ_660NM
    separation = np.cross(neutral, np.array([0.0, 0.0, 1.0]))
    if separation @ wing_a < 0:
        wing_a, wing_b = wing_b, wing_a
    return (
        _replace_s_from_plane(np.cross(neutral, wing_a)),
        _replace_s_from_plane(np.cross(neutral, wing_b)),
        separation,
    )


def _replace_s_from_plane(normal: NDArray) -> NDArray:
    """Build the matrix that recomputes the missing S cone response from L and M."""
    return np.array(
        [
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [-normal[0] / normal[2], -normal[1] / normal[2], 0.0],
        ]
    )


def _tritan(linear: NDArray, severity: float) -> NDArray:
    plane_a, plane_b, separation = _tritan_planes()
    lms = linear @ _LMS_FROM_LINEAR.T
    on_b_side = (lms @ separation) < 0
    projected = np.where(on_b_side[..., np.newaxis], lms @ plane_b.T, lms @ plane_a.T)
    full = projected @ _LINEAR_FROM_LMS.T
    return (1.0 - severity) * linear + severity * full
