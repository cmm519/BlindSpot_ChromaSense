import numpy as np

from color_engine.rules.color_spaces import linear_to_srgb, srgb_to_linear


def test_known_values():
    assert np.allclose(srgb_to_linear(np.array([0.0, 0.5, 1.0])), [0.0, 0.2140411, 1.0])


def test_uint8_input_is_scaled():
    assert np.allclose(srgb_to_linear(np.array([128], dtype=np.uint8)), [0.2158605])


def test_low_values_use_the_linear_segment():
    assert np.allclose(srgb_to_linear(np.array([0.04])), [0.04 / 12.92])
    assert np.allclose(linear_to_srgb(np.array([0.001])), [0.01292])


def test_round_trip_covers_every_level():
    levels = np.arange(256, dtype=np.uint8)
    restored = np.rint(linear_to_srgb(srgb_to_linear(levels)) * 255)
    assert np.array_equal(restored, levels)


def test_encoding_clips_out_of_range_values():
    assert np.allclose(linear_to_srgb(np.array([-0.5, 1.5])), [0.0, 1.0])
