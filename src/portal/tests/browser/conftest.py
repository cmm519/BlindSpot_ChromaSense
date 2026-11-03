"""Start the real app on a free port, with a temporary data folder and a stub AI provider."""

import json
import socket
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest
import uvicorn
from browser_support import PROFILE_DEUTAN
from playwright.sync_api import sync_playwright

from chromasense.main.settings import Settings
from chromasense.main.wiring import build_app

RECORD_LIVE_MESSAGES = """
window.__liveMessages = [];
window.__uploadFields = [];
const realFetch = window.fetch;
window.fetch = (url, options) => {
  if (options && options.body instanceof FormData) {
    window.__uploadFields.push(
      Object.fromEntries(
        [...options.body.entries()].filter(([name]) => name !== "file"),
      ),
    );
  }
  return realFetch(url, options);
};
document.addEventListener("DOMContentLoaded", () => {
  const region = document.getElementById("live-region");
  if (!region) { return; }
  new MutationObserver(() => {
    const text = region.textContent.trim();
    if (text) { window.__liveMessages.push(text); }
  }).observe(region, { childList: true, characterData: true, subtree: true });
});
"""

DEFAULT_READ = {
    "chart_type": "flat graphic",
    "legend": [],
    "text_items": [{"text": "road signs"}, {"text": "Only the AI saw this"}],
    "shape_items": [
        {"kind": "rectangle", "palette_id": 2, "color_name": "bright purple"},
        {"kind": "other", "palette_id": 99, "color_name": "bright purple"},
    ],
    "summary": "A graphic with three road signs.",
}
DEFAULT_ANSWER = {"text": "It shows road signs.", "cited_item_ids": ["text-1"]}


class StubProvider:
    def __init__(self) -> None:
        self.requests: list[dict] = []
        self.read = DEFAULT_READ
        self.answer = DEFAULT_ANSWER
        self.status = 200
        stub = self

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self) -> None:
                length = int(self.headers.get("Content-Length", 0))
                body = json.loads(self.rfile.read(length))
                stub.requests.append(body)
                schema = body["response_format"]["json_schema"]["name"]
                content = stub.read if schema == "image_read" else stub.answer
                reply = json.dumps({"choices": [{"message": {"content": json.dumps(content)}}]})
                self.send_response(stub.status)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(reply.encode())

            def log_message(self, *args) -> None:
                pass

        self._server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.url = f"http://127.0.0.1:{self._server.server_address[1]}/v1/chat/completions"
        threading.Thread(target=self._server.serve_forever, daemon=True).start()

    def stop(self) -> None:
        self._server.shutdown()
        self._server.server_close()


def _free_port() -> int:
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return probe.getsockname()[1]


class Portal:
    def __init__(self, settings: Settings) -> None:
        self.port = _free_port()
        self.url = f"http://127.0.0.1:{self.port}"
        config = uvicorn.Config(
            build_app(settings), host="127.0.0.1", port=self.port, log_level="warning"
        )
        self._server = uvicorn.Server(config)
        self._thread = threading.Thread(target=self._server.run, daemon=True)
        self._thread.start()
        deadline = time.monotonic() + 20
        while not self._server.started:
            if time.monotonic() > deadline:
                raise RuntimeError("the portal did not start")
            time.sleep(0.05)

    def stop(self) -> None:
        self._server.should_exit = True
        self._thread.join(timeout=10)


@pytest.fixture
def provider():
    stub = StubProvider()
    yield stub
    stub.stop()


@pytest.fixture
def start_portal(tmp_path):
    portals = []

    def start(**overrides) -> Portal:
        folder = tmp_path / f"data{len(portals)}"
        folder.mkdir()
        portal = Portal(Settings(data_dir=str(folder), **overrides))
        portals.append(portal)
        return portal

    yield start
    for portal in portals:
        portal.stop()


@pytest.fixture
def portal(start_portal, provider):
    return start_portal(provider_url=provider.url, api_key="stub-key", model="stub-model")


@pytest.fixture(scope="session")
def playwright_driver():
    with sync_playwright() as driver:
        yield driver


@pytest.fixture(scope="session")
def browser(playwright_driver):
    chromium = playwright_driver.chromium.launch(args=["--disable-dev-shm-usage"])
    yield chromium
    chromium.close()


@pytest.fixture
def new_page(browser):
    contexts = []

    def create(profile: str | None = None, init_script: str | None = None, **context_options):
        context = browser.new_context(**context_options)
        context.set_default_timeout(60_000)
        context.add_init_script(RECORD_LIVE_MESSAGES)
        if profile is not None:
            context.add_init_script(
                "if (!localStorage.getItem('chromasense.profile')) {"
                f" localStorage.setItem('chromasense.profile', {json.dumps(profile)}); }}"
            )
        if init_script:
            context.add_init_script(init_script)
        contexts.append(context)
        return context.new_page()

    yield create
    for context in contexts:
        context.close()


@pytest.fixture
def page(new_page):
    """A page whose browser storage already holds a deutan profile."""
    return new_page(PROFILE_DEUTAN)
