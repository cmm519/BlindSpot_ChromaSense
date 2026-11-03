"""Search every delivered page, script, and API response, and the logs, for a known API key."""

import json
import logging
from io import BytesIO
from pathlib import Path

import httpx
from fastapi.testclient import TestClient
from PIL import Image, ImageDraw

import chromasense
from chromasense.ai_gateway.http_vision_reader import HttpVisionReader
from chromasense.main.settings import Settings
from chromasense.main.wiring import build_app

KEY = "sk-known-fake-key-3f9a7c"
STATIC = Path(chromasense.__file__).parent / "web_ui" / "static"


def _png() -> bytes:
    image = Image.new("RGB", (300, 200), (255, 255, 255))
    draw = ImageDraw.Draw(image)
    draw.rectangle([30, 30, 130, 170], fill=(220, 30, 30))
    draw.rectangle([170, 30, 270, 170], fill=(30, 150, 30))
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def _provider(status: int):
    def handler(request):
        assert request.headers["authorization"] == f"Bearer {KEY}"
        if status != 200:
            return httpx.Response(status, json={"error": {"message": f"bad key {KEY}"}})
        content = {
            "chart_type": "flat",
            "legend": [],
            "text_items": [],
            "shape_items": [],
            "summary": "Summary.",
        }
        return httpx.Response(
            200, json={"choices": [{"message": {"content": json.dumps(content)}}]}
        )

    return httpx.MockTransport(handler)


def _client(tmp_path, status=200):
    settings = Settings(
        data_dir=str(tmp_path), provider_url="https://provider.test", api_key=KEY, model="m"
    )
    reader = HttpVisionReader(settings.provider_url, KEY, "m", transport=_provider(status))
    return TestClient(build_app(settings, reader=reader))


def _assert_clean(response) -> None:
    assert KEY not in response.text
    assert KEY not in str(response.headers)


def test_key_appears_in_no_page_script_response_or_log(tmp_path, caplog):
    with caplog.at_level(logging.DEBUG), _client(tmp_path) as client:
        for page in ("/", "/intro", "/settings", "/simulator"):
            response = client.get(page)
            assert response.status_code == 200
            _assert_clean(response)

        scripts = sorted(path.relative_to(STATIC) for path in STATIC.rglob("*") if path.is_file())
        assert len(scripts) == 9
        for script in scripts:
            response = client.get(f"/static/{script}")
            assert response.status_code == 200
            _assert_clean(response)

        upload = client.post(
            "/api/images",
            files={"file": ("a.png", BytesIO(_png()))},
            data={"cvd_type": "deutan", "severity": "1"},
        )
        _assert_clean(upload)
        image_id = upload.json()["image_id"]
        path = f"/api/images/{image_id}"
        profile = {"cvd_type": "deutan", "severity": 1}
        for response in (
            client.get(f"/workspace/{image_id}"),
            client.get(f"{path}/analysis"),
            client.post(f"{path}/analyze", json=profile),
            client.get(f"{path}/color", params={"x": 50, "y": 50, **profile}),
            client.post("/api/interpret", json={"image_id": image_id}),
            client.post("/api/ask", json={"image_id": image_id, "question": "Why?"}),
        ):
            _assert_clean(response)
    assert KEY not in caplog.text


def test_key_stays_out_of_a_failure_even_when_the_provider_echoes_it(tmp_path, caplog):
    with caplog.at_level(logging.DEBUG), _client(tmp_path, status=401) as client:
        upload = client.post(
            "/api/images",
            files={"file": ("a.png", BytesIO(_png()))},
            data={"cvd_type": "none"},
        )
        response = client.post("/api/interpret", json={"image_id": upload.json()["image_id"]})
    assert response.status_code == 503
    _assert_clean(response)
    assert KEY not in caplog.text


def test_settings_do_not_print_the_key():
    settings = Settings(api_key=KEY)
    assert KEY not in repr(settings)
    assert KEY not in str(settings)
