"""Run the real wiring with a temporary data folder, and no AI provider configured."""

import time
from io import BytesIO
from pathlib import Path

import numpy as np
import pytest
from fastapi.testclient import TestClient
from PIL import Image, ImageDraw, ImageFont

from chromasense.main.settings import Settings
from chromasense.main.wiring import build_app


def _png(width=480, height=320) -> bytes:
    image = Image.new("RGB", (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(image)
    draw.rectangle([30, 90, 170, 250], fill=(220, 30, 30))
    draw.ellipse([220, 90, 380, 250], fill=(30, 150, 30))
    draw.text((30, 20), "Sample Graphic", font=ImageFont.load_default(size=30), fill=(0, 0, 0))
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def _upload(client, data: bytes, **form):
    form.setdefault("cvd_type", "none")
    return client.post("/api/images", files={"file": ("a.png", BytesIO(data))}, data=form)


@pytest.fixture
def client(tmp_path):
    settings = Settings(data_dir=str(tmp_path))
    with TestClient(build_app(settings)) as test_client:
        yield test_client


def test_default_retention_is_24_hours_and_blank_values_use_defaults():
    assert Settings().retention_hours == 24.0
    assert Settings.from_env({}).retention_hours == 24.0
    blank = Settings.from_env({"CHROMASENSE_RETENTION_HOURS": "", "CHROMASENSE_DATA_DIR": ""})
    assert (blank.retention_hours, blank.data_dir) == (24.0, "/data")


def test_settings_read_the_configuration_names():
    settings = Settings.from_env(
        {
            "CHROMASENSE_RETENTION_HOURS": "2",
            "CHROMASENSE_CONFUSION_THRESHOLD": "7.5",
            "CHROMASENSE_PURGE_INTERVAL_SECONDS": "30",
            "CHROMASENSE_DATA_DIR": "/elsewhere",
            "CHROMASENSE_API_KEY": "secret-value",
        }
    )
    assert settings.retention_hours == 2.0
    assert settings.confusion_threshold == 7.5
    assert settings.purge_interval_seconds == 30.0
    assert settings.data_dir == "/elsewhere"
    assert "secret-value" not in repr(settings)


def test_with_a_short_period_the_files_are_gone_from_the_server(tmp_path):
    settings = Settings(
        retention_hours=1 / 3600, purge_interval_seconds=0.2, data_dir=str(tmp_path)
    )
    with TestClient(build_app(settings)) as client:
        image_id = _upload(client, _png()).json()["image_id"]
        folder = Path(tmp_path) / "images" / image_id
        assert (folder / "original.bin").exists()
        deadline = time.monotonic() + 10
        while folder.exists() and time.monotonic() < deadline:
            time.sleep(0.1)
        assert not folder.exists()
        assert client.get(f"/api/images/{image_id}/analysis").status_code == 404


def test_upload_then_analysis_returns_each_result_with_no_provider(client):
    response = _upload(client, _png())
    assert response.status_code == 200
    image_id = response.json()["image_id"]
    analysis = client.get(f"/api/images/{image_id}/analysis").json()["analysis"]
    assert analysis["regions"]
    assert {shape["kind"] for shape in analysis["shapes"]} >= {"rectangle", "circle"}
    read = ["".join(item["text"].split()).casefold() for item in analysis["text"]]
    assert "samplegraphic" in read
    assert analysis["legend"] == []
    assert analysis["image_type"] == "flat_graphic"


def test_unknown_image_id_gets_a_client_error(client):
    assert client.get(f"/api/images/{'0' * 32}/analysis").status_code == 404


@pytest.mark.parametrize(
    "data",
    [b"this is a text file renamed as a PNG\n", "truncated"],
    ids=["text-as-png", "truncated-jpeg"],
)
def test_bad_files_get_a_message_and_nothing_is_stored(tmp_path, data):
    if data == "truncated":
        buffer = BytesIO()
        Image.new("RGB", (200, 200), (10, 200, 30)).save(buffer, format="JPEG")
        data = buffer.getvalue()[:300]
    with TestClient(build_app(Settings(data_dir=str(tmp_path)))) as client:
        response = _upload(client, data)
    assert response.status_code == 400
    assert response.json()["error"]["message"]
    assert list((Path(tmp_path) / "images").iterdir()) == []


@pytest.mark.parametrize("size", [(1, 1), (2, 40), (40, 2), (16, 16)])
def test_very_small_images_do_not_cause_a_server_error(client, size):
    buffer = BytesIO()
    Image.fromarray(np.full((size[1], size[0], 3), 120, dtype=np.uint8)).save(buffer, format="PNG")
    response = _upload(client, buffer.getvalue(), cvd_type="deutan", severity="1")
    assert response.status_code == 200


def test_views_color_export_and_profile_change_work_end_to_end(client):
    body = _upload(client, _png(), cvd_type="deutan", severity="1").json()
    assert body["enhancement_needed"] is True
    assert isinstance(body["remaining_pair_count"], int)
    path = f"/api/images/{body['image_id']}"
    profile = {"cvd_type": "deutan", "severity": 1}

    views = {
        view: client.get(f"{path}/render", params={"view": view, **profile})
        for view in ("original", "simulated", "enhanced", "overlay")
    }
    assert all(response.status_code == 200 for response in views.values())
    assert len({response.content for response in views.values()}) == 4

    color = client.get(f"{path}/color", params={"x": 100, "y": 170, **profile}).json()
    assert color["color"]["rgb"] == [220, 30, 30]
    assert color["simulated_hex"]
    assert client.get(f"{path}/color", params={"x": 9999, "y": 0}).status_code == 422

    export = client.get(f"{path}/export", params=profile)
    with Image.open(BytesIO(export.content)) as image:
        assert image.size == (480, 320)
    assert client.get(f"{path}/export").status_code == 409

    changed = client.post(f"{path}/analyze", json={"cvd_type": "tritan", "severity": 1})
    assert changed.status_code == 200
    assert changed.json()["pairs"] != body["pairs"]
