import base64

import pytest
from browser_support import (
    ENGINE_DATA,
    active_element_id,
    known_graphic,
    live_messages,
    stored_profile,
    upload_fields,
    upload_file,
    wait_for_workspace,
    write_image,
)


def _shown_in_workspace(page):
    wait_for_workspace(page)
    assert page.locator("#workspace-section").is_visible()
    assert page.locator("#base-image").is_visible()
    assert "/workspace/" in page.url


def test_selecting_a_png_uploads_it_and_the_workspace_shows_it(page, portal, tmp_path):
    page.goto(portal.url)
    upload_file(page, write_image(tmp_path, "known.png", known_graphic()))
    _shown_in_workspace(page)


def test_dropping_a_file_on_the_upload_control_uploads_it(page, portal):
    page.goto(portal.url)
    encoded = base64.b64encode(known_graphic()).decode()
    page.evaluate(
        """(encoded) => {
            const bytes = Uint8Array.from(atob(encoded), (c) => c.charCodeAt(0));
            const data = new DataTransfer();
            data.items.add(new File([bytes], "dropped.png", { type: "image/png" }));
            const zone = document.getElementById("drop-zone");
            const options = { dataTransfer: data, bubbles: true, cancelable: true };
            zone.dispatchEvent(new DragEvent("dragover", options));
            zone.dispatchEvent(new DragEvent("drop", options));
        }""",
        encoded,
    )
    _shown_in_workspace(page)


def test_pasting_a_copied_image_on_the_home_page_uploads_it(page, portal):
    page.goto(portal.url)
    encoded = base64.b64encode(known_graphic()).decode()
    page.evaluate(
        """(encoded) => {
            const bytes = Uint8Array.from(atob(encoded), (c) => c.charCodeAt(0));
            const data = new DataTransfer();
            data.items.add(new File([bytes], "pasted.png", { type: "image/png" }));
            const options = { clipboardData: data, bubbles: true, cancelable: true };
            document.dispatchEvent(new ClipboardEvent("paste", options));
        }""",
        encoded,
    )
    _shown_in_workspace(page)


@pytest.mark.parametrize("name", ["sample.png", "sample.jpg", "sample.heic", "sample.webp"])
def test_each_format_uploads_and_renders(page, portal, name):
    page.goto(portal.url)
    upload_file(page, ENGINE_DATA / name)
    _shown_in_workspace(page)
    assert page.evaluate("document.querySelector('#base-image').naturalWidth") == 32


@pytest.mark.parametrize(
    ("name", "data"),
    [
        ("renamed.png", b"this is a text file, not an image\n"),
        ("truncated.jpg", (ENGINE_DATA / "sample.jpg").read_bytes()[:200]),
    ],
    ids=["text-renamed-as-png", "truncated-jpeg"],
)
def test_bad_file_shows_an_error_and_the_pipeline_does_not_start(
    page, portal, tmp_path, name, data
):
    page.goto(portal.url)
    upload_file(page, write_image(tmp_path, name, data))
    error = page.locator("#upload-error")
    error.wait_for(state="visible")
    assert "not a readable" in error.inner_text()
    assert page.locator("#workspace-section").is_hidden()
    assert "/workspace/" not in page.url
    assert any("failed" in message.casefold() for message in live_messages(page))
    assert any("did not start" in message for message in live_messages(page))


def test_with_empty_storage_an_upload_prompts_then_results_appear(new_page, portal, tmp_path):
    page = new_page()
    page.goto(portal.url)
    assert stored_profile(page) is None
    upload_file(page, write_image(tmp_path, "known.png", known_graphic()))

    dialog = page.locator("#profile-dialog")
    dialog.wait_for(state="visible")
    assert page.evaluate("document.querySelector('#profile-dialog').open") is True
    options = dialog.locator("input[type=radio]")
    assert sorted(options.nth(i).get_attribute("value") for i in range(options.count())) == [
        "achromatopsia",
        "deutan",
        "none",
        "protan",
        "tritan",
    ]
    assert "/workspace/" not in page.url

    dialog.get_by_label("No CVD").check()
    dialog.get_by_role("button", name="Continue").click()
    _shown_in_workspace(page)
    assert upload_fields(page) == {"cvd_type": "none"}
    assert stored_profile(page)["type"] == "none"
    assert active_element_id(page) == "file-input"


def test_prompt_needs_a_choice_and_can_be_canceled(new_page, portal, tmp_path):
    page = new_page()
    page.goto(portal.url)
    upload_file(page, write_image(tmp_path, "known.png", known_graphic()))
    dialog = page.locator("#profile-dialog")
    dialog.wait_for(state="visible")

    dialog.get_by_role("button", name="Continue").click()
    assert page.locator("#profile-dialog-error").is_visible()
    assert dialog.is_visible()

    dialog.get_by_role("button", name="Cancel the upload").click()
    assert dialog.is_hidden()
    assert active_element_id(page) == "file-input"
    assert stored_profile(page) is None
    assert "Upload canceled." in live_messages(page)
    assert "/workspace/" not in page.url


def test_slider_reaches_both_ends_and_the_value_is_sent(new_page, portal, tmp_path):
    page = new_page()
    page.goto(f"{portal.url}/settings")
    page.get_by_label("Deutan").check()
    slider = page.locator("#settings-severity")
    assert (slider.get_attribute("min"), slider.get_attribute("max")) == ("0", "1")
    for value in ("0", "1", "0.35"):
        slider.fill(value)
        assert stored_profile(page)["severity"] == float(value)

    page.goto(portal.url)
    upload_file(page, write_image(tmp_path, "known.png", known_graphic()))
    wait_for_workspace(page)
    assert upload_fields(page) == {"cvd_type": "deutan", "severity": "0.35"}


def test_with_no_cvd_the_slider_is_disabled_and_no_severity_is_sent(new_page, portal, tmp_path):
    page = new_page()
    page.goto(f"{portal.url}/settings")
    page.get_by_label("Deutan").check()
    assert page.locator("#settings-severity").is_enabled()
    page.get_by_label("No CVD").check()
    assert page.locator("#settings-severity").is_disabled()
    assert "severity" not in stored_profile(page)

    page.goto(portal.url)
    upload_file(page, write_image(tmp_path, "known.png", known_graphic()))
    wait_for_workspace(page)
    assert upload_fields(page) == {"cvd_type": "none"}


def test_introduction_explains_profiles_and_enhancement(new_page, portal):
    page = new_page()
    page.goto(portal.url)
    page.get_by_role("link", name="Introduction", exact=True).first.click()
    page.wait_for_url("**/intro")
    assert page.get_by_role("heading", name="CVD profiles").is_visible()
    assert page.get_by_role("heading", name="Enhancement").is_visible()
    assert "does not diagnose" in page.locator("main").inner_text()


def test_settings_page_offers_all_four_types_and_no_cvd(new_page, portal):
    page = new_page()
    page.goto(f"{portal.url}/settings")
    for label in ("Protan", "Deutan", "Tritan", "Achromatopsia", "No CVD"):
        assert page.get_by_label(label).is_visible()


def test_after_a_reload_the_profile_is_still_selected_and_the_upload_carries_it(
    new_page, portal, tmp_path
):
    page = new_page()
    page.goto(f"{portal.url}/settings")
    page.get_by_label("Tritan").check()
    page.reload()
    assert page.get_by_label("Tritan").is_checked()

    page.goto(portal.url)
    upload_file(page, write_image(tmp_path, "known.png", known_graphic()))
    wait_for_workspace(page)
    assert upload_fields(page)["cvd_type"] == "tritan"
    assert stored_profile(page)["updatedAt"]


def test_upload_announces_start_and_completion_and_focus_stays(page, portal, tmp_path):
    page.goto(portal.url)
    path = write_image(tmp_path, "known.png", known_graphic())
    upload_file(page, path)
    before = active_element_id(page)
    assert before == "file-input"
    wait_for_workspace(page)
    page.wait_for_function("window.__liveMessages.some((m) => m.startsWith('Upload finished'))")

    assert active_element_id(page) == before
    messages = live_messages(page)
    assert any(message.startswith("Uploading") for message in messages)
    assert any(message.startswith("Upload finished") for message in messages)
    assert page.locator("#live-region").get_attribute("aria-live") == "polite"


def test_failed_upload_announces_failure_and_focus_stays(page, portal, tmp_path):
    page.goto(portal.url)
    upload_file(page, write_image(tmp_path, "bad.png", b"not an image"))
    before = active_element_id(page)
    page.locator("#upload-error").wait_for(state="visible")
    assert active_element_id(page) == before == "file-input"
    messages = live_messages(page)
    assert any(message.startswith("Uploading") for message in messages)
    assert any(message.startswith("Upload failed") for message in messages)


def test_a_direct_visit_renders_the_same_workspace(page, portal, tmp_path):
    page.goto(portal.url)
    upload_file(page, write_image(tmp_path, "known.png", known_graphic()))
    wait_for_workspace(page)
    summary = page.locator("#analysis-summary").inner_text()
    url = page.url
    page.goto(url)
    wait_for_workspace(page)
    assert page.locator("#analysis-summary").inner_text() == summary
    assert page.locator("main > #workspace").count() == 1


def test_links_keep_the_image_after_an_upload(page, portal, tmp_path):
    page.goto(portal.url)
    upload_file(page, write_image(tmp_path, "known.png", known_graphic()))
    wait_for_workspace(page)
    image_id = page.url.rsplit("/", 1)[1]
    assert page.get_by_role("link", name="Settings", exact=True).get_attribute("href") == (
        f"/settings?image_id={image_id}"
    )
    assert page.get_by_role("link", name="Simulator", exact=True).first.get_attribute("href") == (
        f"/simulator?image_id={image_id}"
    )
