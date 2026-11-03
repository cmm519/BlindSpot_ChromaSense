"""Images and page helpers shared by the browser tests."""

from io import BytesIO
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ENGINE_DATA = Path(__file__).resolve().parents[3] / "color_engine" / "tests" / "data"
RED = (220, 30, 30)
GREEN = (30, 150, 30)
BLUE = (40, 70, 200)
WHITE = (255, 255, 255)
PROFILE_DEUTAN = '{"type": "deutan", "severity": 1, "updatedAt": "2026-01-01T00:00:00Z"}'
PROFILE_TRITAN = '{"type": "tritan", "severity": 1, "updatedAt": "2026-01-01T00:00:00Z"}'
PROFILE_NONE = '{"type": "none", "updatedAt": "2026-01-01T00:00:00Z"}'


def known_graphic() -> bytes:
    """A flat graphic with a known circle, rectangle, triangle, and text."""
    image = Image.new("RGB", (800, 500), WHITE)
    draw = ImageDraw.Draw(image)
    draw.text((40, 16), "Road Signs", font=ImageFont.load_default(size=34), fill=(0, 0, 0))
    draw.ellipse([60, 120, 240, 300], fill=RED)
    draw.rectangle([300, 120, 480, 300], fill=GREEN)
    draw.polygon([(540, 300), (720, 300), (630, 120)], fill=BLUE)
    return _png(image)


def no_pairs_graphic() -> bytes:
    """Black and white stay distinct under every CVD type."""
    image = Image.new("RGB", (300, 200), WHITE)
    ImageDraw.Draw(image).rectangle([40, 40, 240, 160], fill=(0, 0, 0))
    return _png(image)


def regions_graphic() -> bytes:
    """Four known color regions, far apart, on a white background."""
    image = Image.new("RGB", (400, 300), WHITE)
    draw = ImageDraw.Draw(image)
    draw.rectangle([20, 20, 180, 130], fill=RED)
    draw.rectangle([220, 20, 380, 130], fill=GREEN)
    draw.rectangle([20, 170, 180, 280], fill=BLUE)
    return _png(image)


def _png(image: Image.Image) -> bytes:
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def write_image(folder: Path, name: str, data: bytes) -> Path:
    path = folder / name
    path.write_bytes(data)
    return path


def live_messages(page) -> list[str]:
    return page.evaluate("window.__liveMessages")


def upload_fields(page) -> dict:
    """Return the profile fields of the last upload that the page sent."""
    page.wait_for_function("window.__uploadFields.length > 0")
    return page.evaluate("window.__uploadFields[window.__uploadFields.length - 1]")


def active_element_id(page) -> str:
    return page.evaluate("document.activeElement && document.activeElement.id")


def stored_profile(page) -> dict | None:
    return page.evaluate("JSON.parse(localStorage.getItem('chromasense.profile'))")


def upload_file(page, path: Path) -> None:
    page.locator("#file-input").focus()
    page.locator("#file-input").set_input_files(str(path))


def wait_for_workspace(page) -> None:
    page.wait_for_selector("#workspace #base-image", state="attached", timeout=60_000)
    page.wait_for_function(
        "document.querySelector('#analysis-summary') "
        "&& document.querySelector('#analysis-summary').textContent.length > 0",
        timeout=60_000,
    )
    page.wait_for_function(
        "(() => { const i = document.querySelector('#base-image');"
        " return i.complete && i.naturalWidth > 0; })()",
        timeout=60_000,
    )


def image_loaded(page, selector: str) -> bool:
    return page.evaluate(
        "(s) => { const i = document.querySelector(s); return i.complete && i.naturalWidth > 0; }",
        selector,
    )


def wait_for_image(page, selector: str) -> None:
    page.wait_for_function(
        "(s) => { const i = document.querySelector(s);"
        " return i && i.getAttribute('src') && i.complete && i.naturalWidth > 0; }",
        arg=selector,
        timeout=60_000,
    )


def image_pixels(page, selector: str) -> str:
    """Fetch an image's bytes by its current source, for comparing two views."""
    return page.evaluate(
        """async (s) => {
            const response = await fetch(document.querySelector(s).src);
            const bytes = new Uint8Array(await response.arrayBuffer());
            return Array.from(bytes).join(",");
        }""",
        selector,
    )
