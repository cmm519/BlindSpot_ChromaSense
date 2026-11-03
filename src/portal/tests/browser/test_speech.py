import pytest
from browser_support import (
    PROFILE_DEUTAN,
    known_graphic,
    upload_file,
    wait_for_workspace,
    write_image,
)

RECORD_SPEECH = """
window.__speech = [];
class FakeUtterance {
  constructor(text) { this.text = text; this.rate = 1; }
}
window.SpeechSynthesisUtterance = FakeUtterance;
Object.defineProperty(window, "speechSynthesis", {
  configurable: true,
  value: {
    speak: (u) => window.__speech.push({ call: "speak", text: u.text, rate: u.rate }),
    pause: () => window.__speech.push({ call: "pause" }),
    resume: () => window.__speech.push({ call: "resume" }),
    cancel: () => window.__speech.push({ call: "cancel" }),
  },
});
"""

NO_SPEECH = """
Object.defineProperty(window, "speechSynthesis", { configurable: true, value: undefined });
delete window.speechSynthesis;
"""


@pytest.fixture
def speech_page(new_page):
    return new_page(PROFILE_DEUTAN, init_script=RECORD_SPEECH)


def _open(page, portal, tmp_path):
    page.goto(portal.url)
    upload_file(page, write_image(tmp_path, "known.png", known_graphic()))
    wait_for_workspace(page)
    page.wait_for_function("window.__liveMessages.some((m) => m.includes('pipeline finished'))")


def _calls(page):
    return page.evaluate("window.__speech")


def _spoken(page):
    return [call for call in _calls(page) if call["call"] == "speak"]


def _clear(page):
    page.evaluate("window.__speech.length = 0")


def _press(page, name):
    """Operate a control with the keyboard only."""
    page.get_by_role("button", name=name).focus()
    page.keyboard.press("Enter")


def _explain(page):
    page.locator("#explain-button").click()
    page.wait_for_function("document.querySelector('#ai-summary').textContent.length > 0")


def _identify(page):
    page.locator("#point-area").focus()
    page.keyboard.press("n")
    page.wait_for_function("document.querySelector('#color-result').innerText.includes('HEX')")


def test_keyboard_starts_pauses_resumes_and_stops_the_local_analysis(speech_page, portal, tmp_path):
    page = speech_page
    _open(page, portal, tmp_path)
    assert _spoken(page) == []

    _press(page, "Read the local analysis aloud")
    spoken = _spoken(page)
    assert len(spoken) == 1
    assert "Flag: unverified." in spoken[0]["text"]
    assert "Shape: circle" in spoken[0]["text"]

    _press(page, "Pause reading the local analysis")
    assert _calls(page)[-1]["call"] == "pause"
    _press(page, "Resume reading the local analysis")
    assert _calls(page)[-1]["call"] == "resume"
    _press(page, "Stop reading the local analysis")
    assert _calls(page)[-1]["call"] == "cancel"


def test_spoken_text_matches_the_page_text(speech_page, portal, tmp_path):
    page = speech_page
    _open(page, portal, tmp_path)
    _press(page, "Read the local analysis aloud")
    assert _spoken(page)[0]["text"] == page.locator("#local-results").inner_text()


def test_keyboard_operates_playback_of_an_ai_response_with_its_flags(speech_page, portal, tmp_path):
    page = speech_page
    _open(page, portal, tmp_path)
    _press(page, "Read the AI response aloud")
    assert _spoken(page) == []
    assert "no AI response to read" in page.locator("#live-region").inner_text()

    _explain(page)
    _press(page, "Read the AI response aloud")
    text = _spoken(page)[0]["text"]
    assert "A graphic with three road signs." in text
    assert "Flag: verified." in text
    assert "Flag: unverified." in text
    _press(page, "Pause reading the AI response")
    _press(page, "Resume reading the AI response")
    _press(page, "Stop reading the AI response")
    assert [call["call"] for call in _calls(page)][-3:] == ["pause", "resume", "cancel"]


def test_ai_playback_includes_answers_and_their_flags(speech_page, portal, tmp_path):
    page = speech_page
    _open(page, portal, tmp_path)
    _explain(page)
    page.locator("#question-input").fill("What does it show?")
    page.locator("#question-button").click()
    page.wait_for_selector("#answer-list > li")
    _press(page, "Read the AI response aloud")
    text = _spoken(page)[0]["text"]
    assert "It shows road signs." in text
    assert "Flag: verified" in text


def test_keyboard_operates_playback_of_a_color_result(speech_page, portal, tmp_path):
    page = speech_page
    _open(page, portal, tmp_path)
    _identify(page)
    _press(page, "Read the color result aloud")
    assert "HEX #" in _spoken(page)[0]["text"]
    _press(page, "Pause reading the color result")
    _press(page, "Stop reading the color result")
    assert _calls(page)[-1]["call"] == "cancel"


def test_control_state_is_announced_as_text(speech_page, portal, tmp_path):
    page = speech_page
    _open(page, portal, tmp_path)
    _press(page, "Read the local analysis aloud")
    assert page.locator("#live-region").inner_text() == "Reading the local analysis."
    _press(page, "Pause reading the local analysis")
    assert page.locator("#live-region").inner_text() == "Paused reading the local analysis."
    _press(page, "Stop reading the local analysis")
    assert page.locator("#live-region").inner_text() == "Stopped reading the local analysis."


def test_with_automatic_reading_off_a_new_result_is_not_spoken(speech_page, portal, tmp_path):
    page = speech_page
    _open(page, portal, tmp_path)
    _identify(page)
    _explain(page)
    assert _spoken(page) == []


def test_with_automatic_reading_on_results_are_spoken_at_the_set_rate(
    speech_page, portal, tmp_path
):
    page = speech_page
    page.goto(f"{portal.url}/settings")
    page.locator("#speech-rate").fill("1.5")
    page.get_by_label("Read new results aloud automatically").check()

    _open(page, portal, tmp_path)
    assert any("Flag: unverified." in call["text"] for call in _spoken(page))

    _clear(page)
    _identify(page)
    page.wait_for_function("window.__speech.some((c) => c.call === 'speak')")
    color = _spoken(page)[-1]
    assert "HEX #" in color["text"]
    assert color["rate"] == 1.5

    _clear(page)
    _explain(page)
    page.wait_for_function("window.__speech.some((c) => c.call === 'speak')")
    assert "A graphic with three road signs." in _spoken(page)[-1]["text"]


def test_both_settings_survive_a_reload_and_are_off_and_one_by_default(speech_page, portal):
    page = speech_page
    page.goto(f"{portal.url}/settings")
    assert page.locator("#speech-rate").input_value() == "1"
    assert page.get_by_label("Read new results aloud automatically").is_checked() is False
    rate = page.locator("#speech-rate")
    assert (rate.get_attribute("min"), rate.get_attribute("max")) == ("0.5", "2")

    rate.fill("0.7")
    page.get_by_label("Read new results aloud automatically").check()
    page.reload()
    assert page.locator("#speech-rate").input_value() == "0.7"
    assert page.get_by_label("Read new results aloud automatically").is_checked()


def test_rate_set_on_the_settings_page_applies_to_playback(speech_page, portal, tmp_path):
    page = speech_page
    page.goto(f"{portal.url}/settings")
    page.locator("#speech-rate").fill("0.5")
    _open(page, portal, tmp_path)
    _press(page, "Read the local analysis aloud")
    assert _spoken(page)[0]["rate"] == 0.5


def test_a_browser_with_no_speech_says_so_and_everything_else_works(new_page, portal, tmp_path):
    page = new_page(PROFILE_DEUTAN, init_script=NO_SPEECH)
    page.goto(f"{portal.url}/settings")
    assert page.locator("#speech-settings-unavailable").is_visible()
    _open(page, portal, tmp_path)
    assert page.get_by_role("button", name="Read the local analysis aloud").count() == 0
    assert "cannot read the local analysis aloud" in page.locator("main").inner_text()
    assert page.locator("#text-list > li").count() > 0
