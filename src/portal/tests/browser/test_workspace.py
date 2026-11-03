from io import BytesIO

import numpy as np
import pytest
from browser_support import (
    ENGINE_DATA,
    PROFILE_NONE,
    active_element_id,
    image_pixels,
    known_graphic,
    live_messages,
    no_pairs_graphic,
    upload_fields,
    upload_file,
    wait_for_image,
    wait_for_workspace,
    write_image,
)
from PIL import Image


def _open(page, portal, tmp_path, data=None, name="known.png"):
    page.goto(portal.url)
    upload_file(page, write_image(tmp_path, name, data or known_graphic()))
    wait_for_workspace(page)


def _items(page, list_id):
    return page.locator(f"#{list_id} > li").all_inner_texts()


def _decode(page, selector) -> np.ndarray:
    data = bytes(int(value) for value in image_pixels(page, selector).split(","))
    with Image.open(BytesIO(data)) as image:
        return np.array(image.convert("RGB"))


def test_upload_shows_the_enhanced_result_and_local_analysis_with_no_further_action(
    page, portal, tmp_path
):
    _open(page, portal, tmp_path)
    wait_for_image(page, "#top-image")
    assert page.locator("#top-image").is_visible()
    assert "view=enhanced" in page.locator("#top-image").get_attribute("src")
    assert "severity=1" in page.locator("#top-image").get_attribute("src")
    assert _items(page, "text-list")
    assert _items(page, "shape-list")
    assert page.locator("#remaining-pairs").is_visible()


def test_no_pairs_shows_that_no_enhancement_is_needed(page, portal, tmp_path):
    _open(page, portal, tmp_path, no_pairs_graphic())
    message = page.locator("#no-enhancement-message")
    assert message.is_visible()
    assert "no enhancement is needed" in message.inner_text()
    assert page.locator("#pair-empty").is_visible()


def test_strength_changes_the_enhanced_image_request_and_the_download(page, portal, tmp_path):
    _open(page, portal, tmp_path)
    wait_for_image(page, "#top-image")
    original = _decode(page, "#base-image")
    full = _decode(page, "#top-image")
    full_src = page.locator("#top-image").get_attribute("src")

    with page.expect_request("**/render?view=enhanced*strength=0.4*"):
        page.locator("#strength-slider").fill("40")
    wait_for_image(page, "#top-image")
    assert page.locator("#top-image").get_attribute("src") != full_src
    partial = _decode(page, "#top-image")
    assert not np.array_equal(partial, full)
    white = np.all(original == (255, 255, 255), axis=-1)
    assert np.array_equal(partial[white], original[white])
    assert "strength=0.4" in page.locator("#download-link").get_attribute("href")


def test_before_and_after_slider_shows_each_image_by_keyboard(page, portal, tmp_path):
    _open(page, portal, tmp_path)
    wait_for_image(page, "#top-image")
    assert "view=original" in page.locator("#base-image").get_attribute("src")
    assert "view=enhanced" in page.locator("#top-image").get_attribute("src")
    assert not np.array_equal(_decode(page, "#base-image"), _decode(page, "#top-image"))

    clip = "document.querySelector('#top-image').style.clipPath"
    assert page.evaluate(clip) == "inset(0px)" or "0%" in page.evaluate(clip)
    slider = page.locator("#compare-slider")
    slider.focus()
    page.keyboard.press("Home")
    assert slider.input_value() == "0"
    assert "100%" in page.evaluate(clip)
    page.keyboard.press("End")
    assert slider.input_value() == "100"
    slider.fill("50")
    assert "50%" in page.evaluate(clip)


def test_overlay_control_adds_and_removes_the_patterns(page, portal, tmp_path):
    _open(page, portal, tmp_path)
    wait_for_image(page, "#top-image")
    plain = _decode(page, "#top-image")
    overlay = page.get_by_label("Show a pattern on each confusable color group")

    overlay.check()
    assert "view=overlay" in page.locator("#top-image").get_attribute("src")
    wait_for_image(page, "#top-image")
    assert not np.array_equal(_decode(page, "#top-image"), plain)
    assert "patterns" in page.locator("#top-image").get_attribute("alt").casefold()

    overlay.uncheck()
    wait_for_image(page, "#top-image")
    assert np.array_equal(_decode(page, "#top-image"), plain)


def test_download_saves_a_file_that_opens_as_the_enhanced_image(page, portal, tmp_path):
    _open(page, portal, tmp_path)
    with page.expect_download() as download:
        page.locator("#download-link").click()
    target = tmp_path / "saved.png"
    download.value.save_as(target)
    with Image.open(target) as saved:
        assert saved.format == "PNG"
        assert saved.size == (800, 500)
        pixels = np.array(saved.convert("RGB"))
    wait_for_image(page, "#top-image")
    assert np.array_equal(pixels, _decode(page, "#top-image"))


def test_color_and_pair_lists_are_focusable_and_state_every_value(page, portal, tmp_path):
    _open(page, portal, tmp_path)
    colors = page.locator("#color-list > li")
    assert colors.count() >= 4
    text = " ".join(colors.all_inner_texts())
    for word in ("HEX #", "RGB ", "HSL ", "Color family:", "Pattern:", "Confused with:"):
        assert word in text
    assert "hatching" in text

    pairs = page.locator("#pair-list > li")
    assert pairs.count() >= 1
    pair = pairs.first.inner_text()
    assert "look alike" in pair
    assert "Original distance" in pair
    assert "Simulated distance".casefold() in pair.casefold()
    assert "Pattern: hatching" in pair
    assert pairs.first.locator(".swatch").count() == 2
    assert pairs.first.locator(".swatch").first.get_attribute("aria-hidden") == "true"

    pairs.first.focus()
    assert page.evaluate("document.activeElement.parentElement.id") == "pair-list"
    colors.first.focus()
    page.keyboard.press("Tab")
    assert page.evaluate("document.activeElement.parentElement.id") == "color-list"


def test_text_is_listed_with_its_location_in_reading_order(page, portal, tmp_path):
    _open(page, portal, tmp_path)
    items = _items(page, "text-list")
    assert "Road".casefold() in items[0].casefold()
    assert "pixels from the left" in items[0]
    assert "pixels from the top" in items[0]


def test_known_shapes_are_listed_with_kind_location_and_color_name(page, portal, tmp_path):
    _open(page, portal, tmp_path)
    shapes = _items(page, "shape-list")
    for kind in ("circle", "rectangle", "triangle"):
        match = next(item for item in shapes if f"Shape: {kind}" in item)
        assert "color " in match
        assert "pixels from the left" in match
    assert "unknown color" not in " ".join(shapes)


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("chart_sales.png", "chart"),
        ("map_districts.png", "map"),
        ("flat_shapes.png", "flat graphic"),
        ("photo_astronaut.jpg", "photograph"),
    ],
)
def test_each_labeled_image_receives_a_type(page, portal, name, expected):
    page.goto(portal.url)
    upload_file(page, ENGINE_DATA / "labeled" / name)
    wait_for_workspace(page)
    assert page.locator("#image-type").inner_text() == f"Image type: {expected}."
    assert page.locator("#best-effort-message").is_visible() == (expected == "photograph")


def test_photograph_shows_the_best_effort_message(page, portal):
    page.goto(portal.url)
    upload_file(page, ENGINE_DATA / "labeled" / "photo_cat.jpg")
    wait_for_workspace(page)
    assert "best effort" in page.locator("#best-effort-message").inner_text()


def test_enhancement_requests_carry_the_stored_profile(page, portal, tmp_path):
    _open(page, portal, tmp_path)
    assert upload_fields(page) == {"cvd_type": "deutan", "severity": "1"}
    wait_for_image(page, "#top-image")
    src = page.locator("#top-image").get_attribute("src")
    assert "cvd_type=deutan" in src and "severity=1" in src
    href = page.locator("#download-link").get_attribute("href")
    assert "cvd_type=deutan" in href and "severity=1" in href


def test_no_cvd_shows_the_original_color_list_and_local_results_with_no_enhanced_image(
    new_page, portal, tmp_path
):
    page = new_page(PROFILE_NONE)
    _open(page, portal, tmp_path)
    assert "view=original" in page.locator("#base-image").get_attribute("src")
    assert page.locator("#top-image").is_hidden()
    assert page.locator("#enhancement-controls").is_hidden()
    assert page.locator("#no-cvd-message").is_visible()
    assert _items(page, "color-list")
    assert _items(page, "text-list")
    assert _items(page, "shape-list")
    assert page.locator("#download-link").is_hidden()


def test_pipeline_messages_are_announced_with_no_focus_change(page, portal, tmp_path):
    _open(page, portal, tmp_path)
    page.wait_for_function("window.__liveMessages.some((m) => m.includes('pipeline finished'))")
    messages = live_messages(page)
    assert any("starting the analysis pipeline" in message for message in messages)
    assert any("pipeline finished" in message for message in messages)
    assert active_element_id(page) == "file-input"


def test_a_failed_pipeline_load_shows_a_message(page, portal):
    page.goto(f"{portal.url}/workspace/{'0' * 32}")
    error = page.locator("#workspace-error")
    error.wait_for(state="visible")
    assert "No image" in error.inner_text()
    assert any("failed" in message for message in live_messages(page))


def test_each_image_alternative_states_its_view_and_the_summary(page, portal, tmp_path):
    _open(page, portal, tmp_path)
    summary = page.locator("#analysis-summary").inner_text()
    assert page.locator("#base-image").get_attribute("alt") == f"Original view. {summary}"
    assert page.locator("#top-image").get_attribute("alt") == f"Enhanced view. {summary}"
    for selector in ("#base-image", "#top-image"):
        assert page.locator(selector).get_attribute("aria-describedby") == "analysis-summary"


def test_results_list_each_item_as_local_and_unverified_with_no_provider_request(
    page, portal, provider, tmp_path
):
    _open(page, portal, tmp_path)
    for list_id in ("text-list", "shape-list"):
        for item in _items(page, list_id):
            assert "Source: local analysis." in item
            assert "Flag: unverified." in item
    assert provider.requests == []


def test_profile_changed_in_settings_applies_when_returning_to_the_image(page, portal, tmp_path):
    _open(page, portal, tmp_path)
    deutan_pairs = _items(page, "pair-list")
    image_id = page.url.rsplit("/", 1)[1]

    page.goto(f"{portal.url}/settings?image_id={image_id}")
    page.get_by_label("Tritan").check()
    with page.expect_request("**/analyze") as request:
        page.get_by_role("link", name="Return to your image").click()
    assert request.value.post_data_json == {"cvd_type": "tritan", "severity": 1}
    wait_for_workspace(page)
    page.wait_for_function("window.__liveMessages.some((m) => m.includes('results loaded'))")
    assert _items(page, "pair-list") != deutan_pairs
    assert "cvd_type=tritan" in page.locator("#top-image").get_attribute("src")
