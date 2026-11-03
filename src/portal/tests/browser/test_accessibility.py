import pytest
from axe_playwright_python.sync_playwright import Axe
from browser_support import (
    PROFILE_DEUTAN,
    PROFILE_NONE,
    active_element_id,
    known_graphic,
    upload_file,
    wait_for_image,
    wait_for_workspace,
    write_image,
)

PHONE = {"width": 390, "height": 844}
COMPUTER = {"width": 1280, "height": 800}
ZOOM_200 = {"width": 640, "height": 400}
ZOOM_400 = {"width": 320, "height": 200}


def _upload(page, portal, tmp_path) -> str:
    page.goto(portal.url)
    upload_file(page, write_image(tmp_path, "known.png", known_graphic()))
    wait_for_workspace(page)
    page.wait_for_function("window.__liveMessages.some((m) => m.includes('pipeline finished'))")
    return page.url.rsplit("/", 1)[1]


def _pages(portal, image_id):
    return [
        f"{portal.url}/",
        f"{portal.url}/intro",
        f"{portal.url}/settings?image_id={image_id}",
        f"{portal.url}/simulator?image_id={image_id}",
        f"{portal.url}/workspace/{image_id}",
    ]


def _settle(page):
    if page.locator("#workspace").count():
        wait_for_workspace(page)
        page.wait_for_function("window.__liveMessages.some((m) => m.includes('results loaded'))")
    if page.locator("#simulator").count():
        wait_for_image(page, "#simulator-simulated")


def _no_horizontal_scroll(page) -> bool:
    return page.evaluate(
        "document.documentElement.scrollWidth <= document.documentElement.clientWidth"
    )


def _violations(page) -> list[str]:
    results = Axe().run(page)
    return [
        f"{item['id']}: {node['html'][:100]}"
        for item in results.response["violations"]
        for node in item["nodes"]
    ]


def _open_all_lists(page):
    page.evaluate("document.querySelectorAll('details').forEach((d) => { d.open = true; })")


def test_axe_finds_no_violation_on_any_page(new_page, portal, tmp_path):
    page = new_page(PROFILE_DEUTAN)
    image_id = _upload(page, portal, tmp_path)
    found = {}
    for url in _pages(portal, image_id):
        page.goto(url)
        _settle(page)
        _open_all_lists(page)
        found[url] = _violations(page)
    assert found == {url: [] for url in found}


def test_axe_finds_no_violation_after_explain_with_results_on_screen(new_page, portal, tmp_path):
    page = new_page(PROFILE_DEUTAN)
    _upload(page, portal, tmp_path)
    page.locator("#explain-button").click()
    page.wait_for_function("document.querySelector('#ai-summary').textContent.length > 0")
    page.locator("#question-input").fill("What does it show?")
    page.locator("#question-button").click()
    page.wait_for_selector("#answer-list > li")
    page.locator("#point-area").focus()
    page.keyboard.press("n")
    page.wait_for_function("document.querySelector('#color-result').innerText.includes('HEX')")
    _open_all_lists(page)
    assert _violations(page) == []


def test_axe_finds_no_violation_with_the_profile_prompt_open(new_page, portal, tmp_path):
    page = new_page()
    page.goto(portal.url)
    upload_file(page, write_image(tmp_path, "known.png", known_graphic()))
    page.locator("#profile-dialog").wait_for(state="visible")
    assert _violations(page) == []


def test_axe_finds_no_violation_with_no_image_on_the_simulator(new_page, portal):
    page = new_page()
    page.goto(f"{portal.url}/simulator")
    assert _violations(page) == []


def test_new_session_uses_every_feature_with_no_sign_in(new_page, portal, tmp_path):
    page = new_page(PROFILE_DEUTAN)
    image_id = _upload(page, portal, tmp_path)
    words = ("sign in", "log in", "login", "password", "create an account", "privacy notice")
    for url in _pages(portal, image_id):
        page.goto(url)
        _settle(page)
        text = page.locator("body").inner_text().casefold()
        assert not any(word in text for word in words), url
        assert page.locator("input[type=password]").count() == 0
        assert page.url.startswith(portal.url)


def _enhance_task(page, portal, tmp_path):
    _upload(page, portal, tmp_path)
    wait_for_image(page, "#top-image")
    assert page.locator("#top-image").is_visible()
    assert page.locator("#strength-slider").is_visible()
    page.locator("#strength-slider").fill("60")
    page.wait_for_function("document.querySelector('#top-image').src.includes('strength=0.6')")
    wait_for_image(page, "#top-image")


@pytest.mark.parametrize(
    "viewport", [PHONE, COMPUTER, ZOOM_200, ZOOM_400], ids=["phone", "computer", "200", "400"]
)
def test_enhance_task_completes_with_no_horizontal_scroll(new_page, portal, tmp_path, viewport):
    page = new_page(PROFILE_DEUTAN, viewport=viewport)
    _enhance_task(page, portal, tmp_path)
    assert _no_horizontal_scroll(page)


@pytest.mark.parametrize(
    "viewport", [PHONE, COMPUTER, ZOOM_200, ZOOM_400], ids=["phone", "computer", "200", "400"]
)
def test_each_page_has_no_horizontal_scroll(new_page, portal, tmp_path, viewport):
    page = new_page(PROFILE_DEUTAN, viewport=viewport)
    image_id = _upload(page, portal, tmp_path)
    for url in _pages(portal, image_id):
        page.goto(url)
        _settle(page)
        _open_all_lists(page)
        assert _no_horizontal_scroll(page), url


@pytest.mark.parametrize("viewport", [ZOOM_200, ZOOM_400], ids=["200", "400"])
def test_each_pages_controls_are_visible_and_operable_when_zoomed(
    new_page, portal, tmp_path, viewport
):
    page = new_page(PROFILE_DEUTAN, viewport=viewport)
    image_id = _upload(page, portal, tmp_path)
    selector = "main a:visible, main button:visible, main input:visible, main select:visible"
    for url in _pages(portal, image_id):
        page.goto(url)
        _settle(page)
        controls = page.locator(selector)
        assert controls.count() > 0, url
        for index in range(controls.count()):
            control = controls.nth(index)
            control.scroll_into_view_if_needed()
            box = control.bounding_box()
            assert box is not None
            assert box["x"] >= -1, url
            assert box["x"] + box["width"] <= viewport["width"] + 1, url


def test_explain_task_completes_at_400_percent_zoom(new_page, portal, tmp_path):
    page = new_page(PROFILE_DEUTAN, viewport=ZOOM_400)
    _upload(page, portal, tmp_path)
    page.locator("#explain-button").click()
    page.wait_for_function("document.querySelector('#ai-summary').textContent.length > 0")
    assert page.locator("#ai-summary").is_visible()
    assert _no_horizontal_scroll(page)


def _focus_is_visible(page) -> bool:
    return page.evaluate(
        """() => {
            const style = getComputedStyle(document.activeElement);
            return style.outlineStyle !== "none" && parseFloat(style.outlineWidth) >= 2;
        }"""
    )


def _tab_to(page, target_id, limit=120) -> None:
    """Move by the Tab key alone, checking for visible focus at each stop."""
    for _ in range(limit):
        page.keyboard.press("Tab")
        if page.evaluate("document.activeElement !== document.body"):
            assert _focus_is_visible(page), active_element_id(page)
        if active_element_id(page) == target_id:
            return
    raise AssertionError(f"Tab never reached {target_id}")


def test_keyboard_only_run_completes_every_task_with_visible_focus(new_page, portal, tmp_path):
    speech = """
    window.__speech = [];
    window.SpeechSynthesisUtterance = class { constructor(t) { this.text = t; this.rate = 1; } };
    Object.defineProperty(window, "speechSynthesis", { configurable: true, value: {
      speak: (u) => window.__speech.push(u.text),
      pause: () => {}, resume: () => {}, cancel: () => {},
    }});
    """
    page = new_page(init_script=speech)
    page.goto(portal.url)
    path = write_image(tmp_path, "known.png", known_graphic())

    # Upload: the keyboard opens the file picker. Only the operating system dialog is simulated.
    _tab_to(page, "file-input")
    with page.expect_file_chooser() as chooser:
        page.keyboard.press("Enter")
    chooser.value.set_files(str(path))

    # Profile: the prompt is operated with the keyboard.
    page.locator("#profile-dialog").wait_for(state="visible")
    for _ in range(12):
        focused = page.evaluate("document.activeElement.value")
        if focused == "deutan":
            break
        if page.evaluate("document.activeElement.type") == "radio":
            page.keyboard.press("ArrowDown")
        else:
            page.keyboard.press("Tab")
    assert page.evaluate("document.activeElement.value") == "deutan"
    page.keyboard.press("Space")
    assert page.evaluate("document.activeElement.checked") is True
    for _ in range(4):
        page.keyboard.press("Tab")
        if page.evaluate("document.activeElement.textContent") == "Continue":
            break
    page.keyboard.press("Enter")

    # Enhance: the result appears, and the sliders work by keyboard.
    wait_for_workspace(page)
    page.wait_for_function("window.__liveMessages.some((m) => m.includes('pipeline finished'))")
    assert active_element_id(page) == "file-input"
    wait_for_image(page, "#top-image")
    _tab_to(page, "point-area")

    # Identify.
    page.keyboard.press("n")
    page.wait_for_function("document.querySelector('#color-result').innerText.includes('HEX')")
    assert active_element_id(page) == "point-area"

    _tab_to(page, "compare-slider")
    page.keyboard.press("ArrowLeft")
    assert page.locator("#compare-slider").input_value() == "99"
    _tab_to(page, "strength-slider")
    page.keyboard.press("ArrowLeft")
    assert page.locator("#strength-slider").input_value() == "95"
    _tab_to(page, "overlay-toggle")
    page.keyboard.press("Space")
    assert page.locator("#overlay-toggle").is_checked()

    # Explain.
    _tab_to(page, "explain-button")
    page.keyboard.press("Enter")
    page.wait_for_function("document.querySelector('#ai-summary').textContent.length > 0")
    assert active_element_id(page) == "explain-button"

    # Playback: read the AI response, with the keyboard alone.
    for _ in range(120):
        page.keyboard.press("Tab")
        assert _focus_is_visible(page)
        if page.evaluate("document.activeElement.textContent") == "Read the AI response aloud":
            break
    page.keyboard.press("Enter")
    spoken = page.evaluate("window.__speech")
    assert "A graphic with three road signs." in spoken[-1]


def test_tab_reaches_the_end_of_every_page_with_no_trap(new_page, portal, tmp_path):
    page = new_page(PROFILE_DEUTAN)
    image_id = _upload(page, portal, tmp_path)
    position = """
        document.activeElement === document.body
            ? -1
            : [...document.querySelectorAll("*")].indexOf(document.activeElement)
    """
    for url in _pages(portal, image_id):
        page.goto(url)
        _settle(page)
        previous = -2
        stops = 0
        for _ in range(600):
            page.keyboard.press("Tab")
            current = page.evaluate(position)
            if current == -1 or (stops and current < previous):
                break
            assert current != previous, f"{url}: Tab did not move focus"
            previous = current
            stops += 1
        else:
            raise AssertionError(f"{url}: Tab never reached the end")
        assert stops > 0, url


def test_back_from_a_placed_workspace_returns_to_the_home_page(new_page, portal, tmp_path):
    page = new_page(PROFILE_DEUTAN)
    _upload(page, portal, tmp_path)
    page.go_back()
    page.wait_for_selector("#upload-heading")
    assert page.locator("#workspace-section").is_hidden()


def test_skip_link_is_first_and_moves_to_main_content(new_page, portal):
    page = new_page(PROFILE_DEUTAN)
    page.goto(portal.url)
    page.keyboard.press("Tab")
    assert page.evaluate("document.activeElement.textContent") == "Skip to main content"
    page.keyboard.press("Enter")
    assert page.evaluate("document.activeElement.id") == "main"


def test_forced_colors_keeps_everything_visible_during_keyboard_navigation(
    new_page, portal, tmp_path
):
    page = new_page(PROFILE_DEUTAN, forced_colors="active")
    image_id = _upload(page, portal, tmp_path)
    assert page.evaluate("matchMedia('(forced-colors: active)').matches") is True
    for url in _pages(portal, image_id):
        page.goto(url)
        _settle(page)
        for _ in range(12):
            page.keyboard.press("Tab")
            if page.evaluate("document.activeElement !== document.body"):
                assert _focus_is_visible(page), url
    page.goto(f"{portal.url}/workspace/{image_id}")
    _settle(page)
    flag = page.locator(".flag").first
    assert flag.is_visible()
    border = flag.evaluate("(e) => getComputedStyle(e).borderTopStyle")
    assert border == "solid"
    text, background = flag.evaluate(
        "(e) => [getComputedStyle(e).color, getComputedStyle(document.body).backgroundColor]"
    )
    assert text != background
    button = page.locator("#explain-button")
    assert button.evaluate("(e) => getComputedStyle(e).borderTopStyle") == "solid"
    swatch = page.locator(".swatch").first
    assert swatch.evaluate("(e) => getComputedStyle(e).forcedColorAdjust") == "none"


def test_each_flag_and_status_has_a_text_equivalent(new_page, portal, tmp_path):
    page = new_page(PROFILE_DEUTAN)
    _upload(page, portal, tmp_path)
    page.locator("#explain-button").click()
    page.wait_for_function("document.querySelector('#ai-summary').textContent.length > 0")
    flags = page.locator(".flag")
    assert flags.count() > 0
    for index in range(flags.count()):
        assert flags.nth(index).inner_text() in ("verified", "unverified")
    for swatch_index in range(page.locator(".swatch").count()):
        swatch = page.locator(".swatch").nth(swatch_index)
        assert swatch.get_attribute("aria-hidden") == "true"
        parent_text = swatch.evaluate("(e) => e.parentElement.textContent")
        assert "#" in parent_text or "look alike" in parent_text
    colors = " ".join(page.locator("#color-list > li").all_inner_texts())
    assert "Pattern:" in colors
    assert page.locator("#point-position").inner_text()
    assert page.locator("#compare-value").inner_text()


def test_grayscale_rendering_keeps_every_status_as_text(new_page, portal, tmp_path):
    page = new_page(PROFILE_NONE)
    _upload(page, portal, tmp_path)
    page.add_style_tag(content="html { filter: grayscale(1); }")
    assert page.locator("#no-cvd-message").is_visible()
    items = page.locator("#text-list > li").all_inner_texts()
    assert all("Flag: unverified." in item for item in items)


def test_enhanced_result_takes_at_most_three_clicks_from_home(new_page, portal, tmp_path):
    page = new_page(PROFILE_DEUTAN)
    path = write_image(tmp_path, "known.png", known_graphic())
    page.goto(portal.url)
    clicks = 1
    with page.expect_file_chooser() as chooser:
        page.locator("#file-input").click()
    chooser.value.set_files(str(path))
    wait_for_workspace(page)
    wait_for_image(page, "#top-image")
    assert page.locator("#top-image").is_visible()
    assert "view=enhanced" in page.locator("#top-image").get_attribute("src")
    assert clicks <= 3
