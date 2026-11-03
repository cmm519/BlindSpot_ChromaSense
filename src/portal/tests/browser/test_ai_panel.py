import json

import pytest
from browser_support import (
    PROFILE_DEUTAN,
    PROFILE_NONE,
    active_element_id,
    known_graphic,
    live_messages,
    upload_file,
    wait_for_image,
    wait_for_workspace,
    write_image,
)


def _open(page, portal, tmp_path):
    page.goto(portal.url)
    upload_file(page, write_image(tmp_path, "known.png", known_graphic()))
    wait_for_workspace(page)
    page.wait_for_function("window.__liveMessages.some((m) => m.includes('pipeline finished'))")


def _explain(page):
    button = page.locator("#explain-button")
    button.focus()
    button.click()
    page.wait_for_function(
        "document.querySelector('#ai-panel').getAttribute('aria-busy') === 'false'"
    )


def _items(page, list_id):
    return page.locator(f"#{list_id} > li").all_inner_texts()


def _ask(page, question):
    page.locator("#question-input").fill(question)
    page.locator("#question-button").click()


def test_panel_shows_a_text_flag_on_each_item_matching_the_agreement(page, portal, tmp_path):
    _open(page, portal, tmp_path)
    _explain(page)
    text = _items(page, "ai-text")
    matched = next(item for item in text if "road" in item.casefold())
    assert "Flag: verified." in matched
    assert "Source: AI and local analysis." in matched
    only_ai = next(item for item in text if "Only the AI saw this" in item)
    assert "Flag: unverified." in only_ai
    assert "Source: AI." in only_ai

    for list_id in ("ai-text", "ai-shapes", "ai-colors"):
        for item in _items(page, list_id):
            assert "Flag: verified." in item or "Flag: unverified." in item
    shapes = _items(page, "ai-shapes")
    rectangle = next(item for item in shapes if "Shape: rectangle" in item)
    assert "Flag: unverified." in rectangle or "Flag: verified." in rectangle


def test_structure_exposes_chart_type_summary_and_lists_to_screen_readers(page, portal, tmp_path):
    _open(page, portal, tmp_path)
    _explain(page)
    panel = page.locator("#ai-panel")
    for name in ("Chart type", "Summary", "Legend", "Text", "Shapes", "Colors"):
        assert panel.get_by_role("heading", name=name, exact=True).first.is_visible()
    assert page.locator("#ai-chart-type").inner_text() == "flat graphic"
    assert page.locator("#ai-summary").inner_text() == "A graphic with three road signs."
    assert panel.get_by_role("list").count() >= 4


def test_wrong_ai_color_name_is_replaced_and_invalid_id_is_unverified(page, portal, tmp_path):
    _open(page, portal, tmp_path)
    _explain(page)
    assert "bright purple" not in page.locator("#ai-panel").inner_text()
    colors = _items(page, "ai-colors")
    assert any("HEX #" in item and "Flag: verified." in item for item in colors)
    invalid = next(item for item in colors if "99" in item)
    assert "Flag: unverified." in invalid
    other_shape = next(item for item in _items(page, "ai-shapes") if "Shape: other" in item)
    assert "unknown color" in other_shape
    assert "Flag: unverified." in other_shape


def test_typed_question_sends_the_same_image_and_palette_and_shows_the_answer(
    page, portal, provider, tmp_path
):
    _open(page, portal, tmp_path)
    _explain(page)
    _ask(page, "What does it show?")
    page.wait_for_selector("#answer-list > li")
    answer = page.locator("#answer-list > li").first.inner_text()
    assert "It shows road signs." in answer
    assert "Flag: verified" in answer
    assert "text-1" in answer

    read, ask = provider.requests
    read_user = read["messages"][1]["content"]
    ask_user = ask["messages"][1]["content"]
    assert ask_user[1] == read_user[1]
    assert json.loads(ask_user[0]["text"])["palette"] == json.loads(read_user[0]["text"])["palette"]
    assert json.loads(ask_user[0]["text"])["question"] == "What does it show?"


def test_question_with_an_unverified_citation_is_flagged_unverified(
    page, portal, provider, tmp_path
):
    provider.answer = {"text": "Maybe.", "cited_item_ids": ["ai-text-2"]}
    _open(page, portal, tmp_path)
    _explain(page)
    _ask(page, "What?")
    page.wait_for_selector("#answer-list > li")
    assert "Flag: unverified" in page.locator("#answer-list > li").first.inner_text()


def test_question_before_explain_says_to_click_explain_first(page, portal, tmp_path):
    _open(page, portal, tmp_path)
    _ask(page, "What is this?")
    message = page.locator("#ai-message")
    message.wait_for(state="visible")
    assert "Click Explain first" in message.inner_text()


def test_unreachable_provider_shows_the_message_and_other_features_still_work(
    new_page, start_portal, tmp_path
):
    portal = start_portal(
        provider_url="http://127.0.0.1:9/unreachable", api_key="stub-key", model="stub-model"
    )
    page = new_page(PROFILE_DEUTAN)
    _open(page, portal, tmp_path)
    _explain(page)
    message = page.locator("#ai-message")
    assert message.is_visible()
    assert "AI service is unavailable" in message.inner_text()

    area = page.locator("#point-area")
    area.click(position={"x": 150, "y": 210})
    page.wait_for_function("document.querySelector('#color-result').innerText.includes('HEX #')")
    page.locator("#strength-slider").fill("50")
    page.wait_for_function("document.querySelector('#top-image').src.includes('strength=0.5')")


def test_no_provider_configured_shows_the_same_message(new_page, start_portal, tmp_path):
    portal = start_portal()
    page = new_page(PROFILE_DEUTAN)
    _open(page, portal, tmp_path)
    _explain(page)
    assert "AI service is unavailable" in page.locator("#ai-message").inner_text()


def test_no_cvd_upload_supports_color_identification_and_explain(new_page, portal, tmp_path):
    page = new_page(PROFILE_NONE)
    _open(page, portal, tmp_path)
    assert page.locator("#top-image").is_hidden()
    assert _items(page, "color-list")
    assert _items(page, "text-list")
    page.locator("#point-area").click(position={"x": 150, "y": 210})
    page.wait_for_function("document.querySelector('#color-result').innerText.includes('HEX #')")
    _explain(page)
    assert page.locator("#ai-summary").is_visible()


def test_explanation_is_reachable_by_keyboard_and_states_all_three_points(page, portal, tmp_path):
    _open(page, portal, tmp_path)
    page.locator("#explain-button").focus()
    for _ in range(6):
        page.keyboard.press("Tab")
        if active_element_id(page) == "flag-explanation":
            break
    assert active_element_id(page) == "flag-explanation"
    text = page.locator("#flag-explanation").inner_text()
    assert "verified color was checked against the image's pixels" in text
    assert "AI read and the local analysis agreed" in text
    assert "Neither guarantees" in text


def test_explain_announces_start_and_completion_and_focus_stays(page, portal, tmp_path):
    _open(page, portal, tmp_path)
    _explain(page)
    assert active_element_id(page) == "explain-button"
    messages = live_messages(page)
    assert any(message.startswith("Explain started") for message in messages)
    assert any(message.startswith("Explain finished") for message in messages)


def test_failed_explain_announces_failure_and_focus_stays(page, portal, provider, tmp_path):
    provider.status = 500
    _open(page, portal, tmp_path)
    _explain(page)
    assert active_element_id(page) == "explain-button"
    assert any(message.startswith("The AI request failed") for message in live_messages(page))


def test_panel_is_marked_busy_during_a_request(page, portal, provider, tmp_path):
    _open(page, portal, tmp_path)
    page.evaluate(
        """() => {
            window.__busyStates = [];
            new MutationObserver(() => {
                window.__busyStates.push(document.querySelector("#ai-panel").getAttribute("aria-busy"));
            }).observe(document.querySelector("#ai-panel"), { attributes: true });
        }"""
    )
    _explain(page)
    assert page.evaluate("window.__busyStates") == ["true", "false"]


def test_image_alternatives_gain_the_interpretation_summary_after_explain(page, portal, tmp_path):
    _open(page, portal, tmp_path)
    local = page.locator("#analysis-summary").inner_text()
    _explain(page)
    for selector, view in (("#base-image", "Original view."), ("#top-image", "Enhanced view.")):
        alt = page.locator(selector).get_attribute("alt")
        assert alt.startswith(view)
        assert local in alt
        assert "A graphic with three road signs." in alt
    assert (
        "A graphic with three road signs." in page.locator("#interpretation-summary").inner_text()
    )


def test_upload_makes_no_provider_request_and_a_matching_item_becomes_verified(
    page, portal, provider, tmp_path
):
    _open(page, portal, tmp_path)
    assert provider.requests == []
    local_before = next(item for item in _items(page, "text-list") if "road" in item.casefold())
    assert "Source: local analysis. Flag: unverified." in local_before

    _explain(page)
    assert len(provider.requests) == 1
    local_after = next(item for item in _items(page, "text-list") if "road" in item.casefold())
    assert "Source: AI and local analysis. Flag: verified." in local_after


def test_local_item_the_ai_did_not_see_stays_listed_and_unverified(page, portal, tmp_path):
    _open(page, portal, tmp_path)
    before = len(_items(page, "shape-list"))
    _explain(page)
    shapes = _items(page, "shape-list")
    assert len(shapes) == before
    circle = next(item for item in shapes if "Shape: circle" in item)
    assert "Source: local analysis. Flag: unverified." in circle


def test_request_past_a_low_cap_makes_no_provider_call_and_says_unavailable(
    new_page, start_portal, provider, tmp_path
):
    portal = start_portal(
        provider_url=provider.url,
        api_key="stub-key",
        model="stub-model",
        cost_per_request=1.0,
        spend_cap=1.0,
    )
    page = new_page(PROFILE_DEUTAN)
    _open(page, portal, tmp_path)
    _explain(page)
    assert len(provider.requests) == 1

    _ask(page, "Past the cap?")
    message = page.locator("#ai-message")
    message.wait_for(state="visible")
    assert "AI is temporarily unavailable" in message.inner_text()
    assert len(provider.requests) == 1


def test_rate_limit_has_its_own_message(new_page, start_portal, provider, tmp_path):
    portal = start_portal(
        provider_url=provider.url, api_key="stub-key", model="stub-model", rate_limit_session=1
    )
    page = new_page(PROFILE_DEUTAN)
    _open(page, portal, tmp_path)
    _explain(page)
    _ask(page, "One too many?")
    message = page.locator("#ai-message")
    message.wait_for(state="visible")
    assert "too many AI requests" in message.inner_text()
    assert len(provider.requests) == 1


def test_after_a_failed_explain_results_remain_and_the_next_request_works(
    page, portal, provider, tmp_path
):
    provider.status = 500
    _open(page, portal, tmp_path)
    wait_for_image(page, "#top-image")
    pairs_before = _items(page, "pair-list")
    assert pairs_before
    _explain(page)
    assert page.locator("#ai-message").is_visible()
    assert page.locator("#top-image").is_visible()
    assert _items(page, "pair-list") == pairs_before

    provider.status = 200
    _explain(page)
    assert page.locator("#ai-message").is_hidden()
    assert page.locator("#ai-summary").is_visible()


@pytest.mark.parametrize("question", ["", "   "], ids=["empty", "blank"])
def test_blank_question_asks_for_text_and_sends_nothing(page, portal, provider, tmp_path, question):
    _open(page, portal, tmp_path)
    _ask(page, question)
    assert "Type a question first." in page.locator("#ai-message").inner_text()
    assert provider.requests == []
