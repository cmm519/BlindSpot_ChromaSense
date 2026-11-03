"""Filter 1: turn uploaded bytes into an sRGB pixel array."""

from io import BytesIO

import numpy as np
from PIL import Image, ImageCms, ImageOps, UnidentifiedImageError
from pillow_heif import register_heif_opener

from color_engine.models import DecodedImage1, ImageDecodeError

register_heif_opener()

_ACCEPTED_FORMATS = ("PNG", "JPEG", "HEIF", "WEBP")
_DIRECT_PROFILE_MODES = ("RGB", "L", "CMYK")


def decode_1(data: bytes) -> DecodedImage1:
    try:
        with Image.open(BytesIO(data), formats=_ACCEPTED_FORMATS) as opened:
            opened.seek(0)
            opened.load()
            icc_profile = opened.info.get("icc_profile")
            pixels = _to_srgb_pixels(ImageOps.exif_transpose(opened), icc_profile)
    except (
        UnidentifiedImageError,
        OSError,
        Image.DecompressionBombError,
        ImageCms.PyCMSError,
        SyntaxError,
        ValueError,
    ) as error:
        raise ImageDecodeError(
            "The file is not a readable PNG, JPEG, HEIC, or WEBP image"
        ) from error

    height, width = pixels.shape[:2]
    return DecodedImage1(pixels=pixels, width=width, height=height)


def _to_srgb_pixels(image: Image.Image, icc_profile: bytes | None) -> np.ndarray:
    alpha = _alpha_channel(image)
    color = _apply_profile(_color_image(image), icc_profile)
    if alpha is None:
        return np.array(color, dtype=np.uint8)
    white = Image.new("RGB", color.size, (255, 255, 255))
    white.paste(color, mask=alpha)
    return np.array(white, dtype=np.uint8)


def _alpha_channel(image: Image.Image) -> Image.Image | None:
    if image.mode in ("RGBA", "LA", "PA") or "transparency" in image.info:
        return image.convert("RGBA").getchannel("A")
    return None


def _color_image(image: Image.Image) -> Image.Image:
    if image.mode.startswith("I;16"):
        eight_bit = (np.asarray(image, dtype=np.uint16) >> 8).astype(np.uint8)
        return Image.fromarray(eight_bit)
    if image.mode in _DIRECT_PROFILE_MODES:
        return image
    if image.mode == "LA":
        return image.convert("L")
    return image.convert("RGBA").convert("RGB")


def _apply_profile(image: Image.Image, icc_profile: bytes | None) -> Image.Image:
    if not icc_profile:
        return image.convert("RGB")
    source = ImageCms.ImageCmsProfile(BytesIO(icc_profile))
    return ImageCms.profileToProfile(
        image, source, ImageCms.createProfile("sRGB"), outputMode="RGB"
    )
