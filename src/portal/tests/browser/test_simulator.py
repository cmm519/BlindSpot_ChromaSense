from browser_support import (
    PROFILE_DEUTAN,
    PROFILE_NONE,
    known_graphic,
    stored_profile,
    upload_file,
    wait_for_image,
    wait_for_workspace,
    write_image,
)


def _image_id(page, portal, tmp_path) -> str:
    page.goto(portal.url)
    upload_file(page, write_image(tmp_path, "known.png", known_graphic()))
    wait_for_workspace(page)
    return page.url.rsplit("/", 1)[1]


def _open_simulator(page, portal, image_id):
    page.goto(f"{portal.url}/simulator?image_id={image_id}")
    wait_for_image(page, "#simulator-original")
    wait_for_image(page, "#simulator-simulated")


def test_selected_type_on_settings_is_used_in_the_next_simulation(new_page, portal, tmp_path):
    page = new_page(PROFILE_DEUTAN)
    image_id = _image_id(page, portal, tmp_path)
    page.goto(f"{portal.url}/settings?image_id={image_id}")
    for label in ("Protan", "Deutan", "Tritan", "Achromatopsia", "No CVD"):
        assert page.get_by_label(label).is_visible()
    page.get_by_label("Tritan").check()

    _open_simulator(page, portal, image_id)
    assert page.locator("#simulator-type").input_value() == "tritan"
    assert "cvd_type=tritan" in page.locator("#simulator-simulated").get_attribute("src")


def test_both_images_are_side_by_side_on_a_wide_screen_and_stack_when_narrow(
    new_page, portal, tmp_path
):
    page = new_page(PROFILE_DEUTAN, viewport={"width": 1200, "height": 900})
    image_id = _image_id(page, portal, tmp_path)
    _open_simulator(page, portal, image_id)
    original = page.locator("#simulator-original").bounding_box()
    simulated = page.locator("#simulator-simulated").bounding_box()
    assert simulated["x"] >= original["x"] + original["width"]
    assert abs(simulated["y"] - original["y"]) < 2

    page.set_viewport_size({"width": 380, "height": 800})
    original = page.locator("#simulator-original").bounding_box()
    simulated = page.locator("#simulator-simulated").bounding_box()
    assert simulated["y"] >= original["y"] + original["height"]


def test_releasing_the_slider_updates_the_preview_with_no_reload(new_page, portal, tmp_path):
    page = new_page(PROFILE_DEUTAN)
    image_id = _image_id(page, portal, tmp_path)
    _open_simulator(page, portal, image_id)
    page.evaluate("window.__notReloaded = true")
    before = page.locator("#simulator-simulated").get_attribute("src")

    page.locator("#simulator-severity").fill("0.4")
    page.wait_for_function(
        "document.querySelector('#simulator-simulated').src.includes('severity=0.4')"
    )
    wait_for_image(page, "#simulator-simulated")
    assert page.locator("#simulator-simulated").get_attribute("src") != before
    assert page.evaluate("window.__notReloaded") is True
    page.wait_for_function("window.__liveMessages.some((m) => m.startsWith('Updated.'))")


def test_rapid_slider_moves_request_one_preview_after_movement_stops(new_page, portal, tmp_path):
    page = new_page(PROFILE_DEUTAN)
    image_id = _image_id(page, portal, tmp_path)
    _open_simulator(page, portal, image_id)
    requests = []
    page.on(
        "request",
        lambda request: requests.append(request.url) if "view=simulated" in request.url else None,
    )
    for value in ("0.9", "0.8", "0.7", "0.6"):
        page.locator("#simulator-severity").fill(value)
    page.wait_for_function(
        "document.querySelector('#simulator-simulated').src.includes('severity=0.6')"
    )
    wait_for_image(page, "#simulator-simulated")
    assert len(requests) == 1


def test_changing_type_and_severity_changes_the_simulated_view(new_page, portal, tmp_path):
    page = new_page(PROFILE_DEUTAN)
    image_id = _image_id(page, portal, tmp_path)
    _open_simulator(page, portal, image_id)

    def view_bytes():
        return page.evaluate(
            """async () => {
                const url = document.querySelector("#simulator-simulated").src;
                const bytes = new Uint8Array(await (await fetch(url)).arrayBuffer());
                return bytes.join(",");
            }"""
        )

    first = view_bytes()
    page.locator("#simulator-type").select_option("tritan")
    page.wait_for_function(
        "document.querySelector('#simulator-simulated').src.includes('cvd_type=tritan')"
    )
    wait_for_image(page, "#simulator-simulated")
    second = view_bytes()
    assert second != first

    page.locator("#simulator-severity").fill("0.25")
    page.wait_for_function(
        "document.querySelector('#simulator-simulated').src.includes('severity=0.25')"
    )
    wait_for_image(page, "#simulator-simulated")
    assert view_bytes() != second


def test_simulator_lists_pairs_with_swatches_names_and_patterns(new_page, portal, tmp_path):
    page = new_page(PROFILE_DEUTAN)
    image_id = _image_id(page, portal, tmp_path)
    workspace_pairs = page.locator("#pair-list > li")
    assert workspace_pairs.first.locator(".swatch").count() == 2
    assert "Pattern:" in workspace_pairs.first.inner_text()

    _open_simulator(page, portal, image_id)
    page.wait_for_selector("#simulator-pair-list > li")
    pair = page.locator("#simulator-pair-list > li").first
    assert pair.locator(".swatch").count() == 2
    assert "look alike" in pair.inner_text()
    assert "Pattern: hatching" in pair.inner_text()


def test_pairs_follow_the_simulator_selection(new_page, portal, tmp_path):
    page = new_page(PROFILE_DEUTAN)
    image_id = _image_id(page, portal, tmp_path)
    _open_simulator(page, portal, image_id)
    page.wait_for_selector("#simulator-pair-list > li")
    before = page.locator("#simulator-pair-list").inner_text()
    with page.expect_response("**/analyze") as response:
        page.locator("#simulator-type").select_option("tritan")
    assert response.value.request.post_data_json == {"cvd_type": "tritan", "severity": 1}
    page.wait_for_function(
        "(before) => document.querySelector('#simulator-pair-list').innerText !== before",
        arg=before,
    )


def test_a_change_here_is_not_saved_as_the_profile(new_page, portal, tmp_path):
    page = new_page(PROFILE_DEUTAN)
    image_id = _image_id(page, portal, tmp_path)
    _open_simulator(page, portal, image_id)
    page.locator("#simulator-type").select_option("tritan")
    page.locator("#simulator-severity").fill("0.25")
    page.wait_for_function(
        "document.querySelector('#simulator-simulated').src.includes('severity=0.25')"
    )
    assert stored_profile(page)["type"] == "deutan"
    assert stored_profile(page)["severity"] == 1


def test_with_no_cvd_the_type_starts_at_protan(new_page, portal, tmp_path):
    page = new_page(PROFILE_NONE)
    image_id = _image_id(page, portal, tmp_path)
    _open_simulator(page, portal, image_id)
    assert page.locator("#simulator-type").input_value() == "protan"
    options = page.locator("#simulator-type option").all_inner_texts()
    assert options == ["Protan", "Deutan", "Tritan", "Achromatopsia"]


def test_text_alternative_names_the_view_type_and_severity(new_page, portal, tmp_path):
    page = new_page(PROFILE_DEUTAN)
    image_id = _image_id(page, portal, tmp_path)
    _open_simulator(page, portal, image_id)
    alt = page.locator("#simulator-simulated").get_attribute("alt")
    assert alt.startswith("Simulated view, deutan, severity 1.")
    assert page.locator("#simulator-original").get_attribute("alt").startswith("Original view.")


def test_with_no_image_the_page_links_to_the_home_page(new_page, portal):
    page = new_page(PROFILE_DEUTAN)
    page.goto(f"{portal.url}/simulator")
    assert "Upload an image first" in page.locator("main").inner_text()
    assert page.get_by_role("link", name="Go to the home page").get_attribute("href") == "/"
