from io import BytesIO
from pathlib import Path

import numpy as np
import pytest
from PIL import Image, ImageCms

from color_engine.models import DecodedImage1, ImageDecodeError
from color_engine.pipeline.filter_1_decode.decode_1 import decode_1

DATA = Path(__file__).parent.parent / "data"

P3_RGB_TO_XYZ = np.array(
    [
        [0.4865709486, 0.2656676932, 0.1982172852],
        [0.2289745641, 0.6917385218, 0.0792869141],
        [0.0, 0.0451133819, 1.0439443689],
    ]
)
XYZ_TO_SRGB = np.array(
    [
        [3.2409699419, -1.5373831776, -0.4986107603],
        [-0.9692436363, 1.8759675015, 0.0415550574],
        [0.0556300797, -0.2039769589, 1.0569715142],
    ]
)


def _expected_srgb_from_p3(level: tuple[int, int, int]) -> np.ndarray:
    """Compute the expected value from the published matrices, without any color library."""
    encoded = np.array(level) / 255
    linear = np.where(encoded <= 0.04045, encoded / 12.92, ((encoded + 0.055) / 1.055) ** 2.4)
    srgb = XYZ_TO_SRGB @ P3_RGB_TO_XYZ @ linear
    assert ((srgb >= 0) & (srgb <= 1)).all(), "the fixture color must be inside the sRGB gamut"
    return 255 * np.where(srgb <= 0.0031308, srgb * 12.92, 1.055 * srgb ** (1 / 2.4) - 0.055)


def _encode(image: Image.Image, image_format: str = "PNG", **options) -> bytes:
    buffer = BytesIO()
    image.save(buffer, format=image_format, **options)
    return buffer.getvalue()


@pytest.mark.parametrize("name", ["sample.png", "sample.jpg", "sample.heic", "sample.webp"])
def test_decodes_each_accepted_format(name):
    decoded = decode_1((DATA / name).read_bytes())
    assert isinstance(decoded, DecodedImage1)
    assert (decoded.width, decoded.height) == (32, 16)
    assert decoded.pixels.shape == (16, 32, 3)
    assert decoded.pixels.dtype == np.uint8
    left, right = decoded.pixels[8, 4].astype(int), decoded.pixels[8, 28].astype(int)
    assert np.abs(left - [200, 40, 40]).max() <= 12
    assert np.abs(right - [40, 80, 200]).max() <= 12


@pytest.mark.parametrize("level", [(180, 120, 90), (120, 160, 110), (90, 110, 170)])
def test_display_p3_profile_converts_to_expected_srgb(level):
    profile = (DATA / "display_p3.icc").read_bytes()
    data = _encode(Image.new("RGB", (4, 4), level), icc_profile=profile)
    expected = _expected_srgb_from_p3(level)
    actual = decode_1(data).pixels[0, 0].astype(float)
    assert np.abs(actual - expected).max() <= 2
    assert not np.array_equal(actual, np.array(level, dtype=float))


def test_image_with_no_profile_is_treated_as_srgb():
    pixels = decode_1(_encode(Image.new("RGB", (2, 2), (180, 120, 90)))).pixels
    assert pixels[0, 0].tolist() == [180, 120, 90]


def test_srgb_profile_leaves_values_nearly_unchanged():
    profile = ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB")).tobytes()
    data = _encode(Image.new("RGB", (2, 2), (180, 120, 90)), icc_profile=profile)
    assert np.abs(decode_1(data).pixels[0, 0].astype(int) - [180, 120, 90]).max() <= 1


def test_text_file_renamed_as_png_is_rejected():
    with pytest.raises(ImageDecodeError):
        decode_1(b"this is a text file, not an image\n")


def test_truncated_jpeg_is_rejected():
    data = (DATA / "sample.jpg").read_bytes()
    with pytest.raises(ImageDecodeError):
        decode_1(data[: len(data) // 2])


def test_empty_data_is_rejected():
    with pytest.raises(ImageDecodeError):
        decode_1(b"")


def test_unsupported_format_is_rejected():
    with pytest.raises(ImageDecodeError):
        decode_1(_encode(Image.new("RGB", (2, 2)), "BMP"))


def test_corrupted_profile_is_rejected():
    data = _encode(Image.new("RGB", (2, 2)), icc_profile=b"not a profile")
    with pytest.raises(ImageDecodeError):
        decode_1(data)


def test_alpha_is_flattened_onto_white():
    image = Image.new("RGBA", (2, 1), (0, 0, 0, 0))
    image.putpixel((1, 0), (10, 20, 30, 255))
    pixels = decode_1(_encode(image)).pixels
    assert pixels.shape == (1, 2, 3)
    assert pixels[0, 0].tolist() == [255, 255, 255]
    assert pixels[0, 1].tolist() == [10, 20, 30]


def test_palette_transparency_is_flattened_onto_white():
    image = Image.new("P", (1, 1), 0)
    image.putpalette([1, 2, 3])
    assert decode_1(_encode(image, transparency=0)).pixels[0, 0].tolist() == [255, 255, 255]


def test_grayscale_becomes_three_channels():
    pixels = decode_1(_encode(Image.new("L", (1, 1), 77))).pixels
    assert pixels[0, 0].tolist() == [77, 77, 77]


def test_sixteen_bit_grayscale_keeps_its_level():
    image = Image.fromarray(np.full((1, 1), 32768, dtype=np.uint16))
    assert decode_1(_encode(image)).pixels[0, 0].tolist() == [128, 128, 128]


def test_exif_orientation_is_applied():
    image = Image.new("RGB", (4, 2), (10, 10, 10))
    exif = Image.Exif()
    exif[0x0112] = 6
    decoded = decode_1(_encode(image, exif=exif))
    assert (decoded.width, decoded.height) == (2, 4)


def test_animated_webp_uses_the_first_frame():
    frames = [Image.new("RGB", (4, 4), color) for color in ((200, 0, 0), (0, 0, 200))]
    data = _encode(
        frames[0], "WEBP", save_all=True, append_images=frames[1:], lossless=True, duration=100
    )
    pixel = decode_1(data).pixels[0, 0].astype(int)
    assert np.abs(pixel - [200, 0, 0]).max() <= 4
