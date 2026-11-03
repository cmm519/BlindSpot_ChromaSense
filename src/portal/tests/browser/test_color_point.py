from browser_support import (
    PROFILE_DEUTAN,
    PROFILE_NONE,
    live_messages,
    regions_graphic,
    upload_file,
    wait_for_workspace,
    write_image,
)

# regions_graphic is 400 by 300, with red, green, and blue rectangles on white.
RED_HEX, GREEN_HEX, BLUE_HEX = "#DC1E1E", "#1E961E", "#2846C8"


def _open(page, portal, tmp_path):
    page.goto(portal.url)
    upload_file(page, write_image(tmp_path, "regions.png", regions_graphic()))
    wait_for_workspace(page)
    page.wait_for_function("window.__liveMessages.some((m) => m.includes('pipeline finished'))")


def _click_share(page, x_share, y_share, method="click"):
    area = page.locator("#point-area")
    box = area.bounding_box()
    position = {"x": box["width"] * x_share, "y": box["height"] * y_share}
    getattr(area, method)(position=position)


def _last_live(page):
    return page.locator("#live-region").inner_text()


def _wait_for_live(page, text):
    page.wait_for_function(
        "(t) => document.querySelector('#live-region').textContent.includes(t)", arg=text
    )


def _wait_for_result(page, text):
    page.wait_for_function(
        "(t) => document.querySelector('#color-result').innerText.includes(t)", arg=text
    )


def test_clicking_returns_the_regions_color_with_correct_values(new_page, portal, tmp_path):
    page = new_page(PROFILE_DEUTAN)
    _open(page, portal, tmp_path)
    _click_share(page, 0.25, 0.25)
    _wait_for_result(page, RED_HEX)
    text = page.locator("#color-result").inner_text()
    assert "RGB 220, 30, 30" in text
    assert "HSL 0 degrees, 76 percent, 49 percent" in text
    assert "Color family: red" in text


def test_tapping_returns_the_regions_color(new_page, portal, tmp_path):
    page = new_page(PROFILE_DEUTAN, has_touch=True)
    _open(page, portal, tmp_path)
    _click_share(page, 0.75, 0.25, method="tap")
    _wait_for_result(page, GREEN_HEX)


def test_pointer_position_scales_on_a_small_display(new_page, portal, tmp_path):
    page = new_page(PROFILE_DEUTAN, viewport={"width": 320, "height": 700})
    _open(page, portal, tmp_path)
    assert page.locator("#point-area").bounding_box()["width"] < 400
    _click_share(page, 0.25, 0.75)
    _wait_for_result(page, BLUE_HEX)


def test_click_puts_the_color_name_in_the_live_region(new_page, portal, tmp_path):
    page = new_page(PROFILE_DEUTAN)
    _open(page, portal, tmp_path)
    _click_share(page, 0.25, 0.25)
    _wait_for_result(page, RED_HEX)
    assert page.locator("#live-region").get_attribute("aria-live") == "polite"
    _wait_for_live(page, RED_HEX)
    assert "crimson" in _last_live(page).casefold() or "red" in _last_live(page).casefold()


def test_simulated_swatch_has_text_and_changes_with_the_profile(new_page, portal, tmp_path):
    page = new_page(PROFILE_DEUTAN)
    _open(page, portal, tmp_path)
    _click_share(page, 0.25, 0.25)
    _wait_for_result(page, RED_HEX)
    first = page.locator("#simulated-color").inner_text()
    assert "Under your profile" in first
    assert page.locator("#simulated-color .swatch").count() == 1
    image_id = page.url.rsplit("/", 1)[1]

    page.goto(f"{portal.url}/settings?image_id={image_id}")
    page.get_by_label("Tritan").check()
    page.goto(f"{portal.url}/workspace/{image_id}")
    wait_for_workspace(page)
    page.wait_for_function("window.__liveMessages.some((m) => m.includes('results loaded'))")
    _click_share(page, 0.25, 0.25)
    _wait_for_result(page, RED_HEX)
    assert page.locator("#simulated-color").inner_text() != first


def test_with_no_cvd_the_simulated_swatch_is_omitted(new_page, portal, tmp_path):
    page = new_page(PROFILE_NONE)
    _open(page, portal, tmp_path)
    _click_share(page, 0.25, 0.25)
    _wait_for_result(page, RED_HEX)
    assert page.locator("#simulated-color").count() == 0


def test_after_a_reload_simulation_enhancement_and_color_requests_carry_the_profile(
    new_page, portal, tmp_path
):
    page = new_page(PROFILE_DEUTAN)
    _open(page, portal, tmp_path)
    page.reload()
    wait_for_workspace(page)
    page.wait_for_function("window.__liveMessages.some((m) => m.includes('results loaded'))")
    enhanced = page.locator("#top-image").get_attribute("src")
    assert (
        "view=enhanced" in enhanced and "cvd_type=deutan" in enhanced and "severity=1" in enhanced
    )

    with page.expect_request("**/color?*") as color:
        _click_share(page, 0.25, 0.25)
    assert "cvd_type=deutan" in color.value.url and "severity=1" in color.value.url

    image_id = page.url.rsplit("/", 1)[1]
    page.goto(f"{portal.url}/simulator?image_id={image_id}")
    page.wait_for_function("document.querySelector('#simulator-simulated').getAttribute('src')")
    simulated = page.locator("#simulator-simulated").get_attribute("src")
    assert "cvd_type=deutan" in simulated and "severity=1" in simulated


def test_arrow_keys_alone_move_the_point_onto_a_known_region(new_page, portal, tmp_path):
    page = new_page(PROFILE_DEUTAN)
    _open(page, portal, tmp_path)
    page.locator("#point-area").focus()
    # The point starts at the center, which is white. 1 percent steps reach the red rectangle.
    for _ in range(30):
        page.keyboard.press("ArrowLeft")
    for _ in range(30):
        page.keyboard.press("ArrowUp")
    _wait_for_live(page, RED_HEX)
    assert "percent from the left" in page.locator("#point-position").inner_text()
    assert page.locator("#point-mark").is_visible()


def test_arrow_key_steps_are_one_percent_and_stay_inside_the_image(new_page, portal, tmp_path):
    page = new_page(PROFILE_DEUTAN)
    _open(page, portal, tmp_path)
    page.locator("#point-area").focus()
    with page.expect_request("**/color?*") as first:
        page.keyboard.press("ArrowRight")
    assert "x=204&y=150" in first.value.url
    with page.expect_request("**/color?*") as second:
        page.keyboard.press("ArrowDown")
    assert "x=204&y=153" in second.value.url
    for _ in range(60):
        page.keyboard.press("ArrowRight")
    page.wait_for_function(
        "document.querySelector('#point-position').textContent.includes('100 percent')"
        " || document.querySelector('#point-position').textContent.includes('99 percent')"
    )
    assert not any("could not be identified" in message for message in live_messages(page))


def test_keyboard_moves_through_each_region_and_announces_its_details(new_page, portal, tmp_path):
    page = new_page(PROFILE_DEUTAN)
    _open(page, portal, tmp_path)
    total = page.locator("#region-list > li").count()
    assert total >= 3
    page.locator("#point-area").focus()
    seen = set()
    for number in range(1, total + 1):
        page.keyboard.press("n")
        _wait_for_live(page, f"Region {number} of {total}.")
        message = _last_live(page)
        assert "Size " in message and "pixels" in message
        assert "percent from the left" in message and "percent from the top" in message
        seen.add(message)
    assert len(seen) == total
    page.keyboard.press("p")
    _wait_for_live(page, f"Region {total - 1} of {total}.")


def test_tab_leaves_the_point_area(new_page, portal, tmp_path):
    page = new_page(PROFILE_DEUTAN)
    _open(page, portal, tmp_path)
    page.locator("#point-area").focus()
    page.keyboard.press("ArrowLeft")
    page.keyboard.press("Tab")
    assert page.evaluate("document.activeElement.id") != "point-area"
    page.keyboard.press("Shift+Tab")
    assert page.evaluate("document.activeElement.id") == "point-area"


def test_point_area_has_a_name_with_instructions(new_page, portal, tmp_path):
    page = new_page(PROFILE_DEUTAN)
    _open(page, portal, tmp_path)
    label = page.locator("#point-area").get_attribute("aria-label")
    assert "arrow keys" in label and "next or previous region" in label
