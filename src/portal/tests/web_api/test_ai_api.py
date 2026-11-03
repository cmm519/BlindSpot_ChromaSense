"""Run the AI endpoints through the real wiring, with a stubbed vision reader."""

import json
from dataclasses import dataclass, field
from io import BytesIO

import httpx
import numpy as np
import pytest
from fastapi.testclient import TestClient
from PIL import Image, ImageDraw, ImageFont

from chromasense.ai_gateway.http_vision_reader import HttpVisionReader
from chromasense.core.errors import AiUnavailable
from chromasense.core.models import AiAnswer, AiRead, ItemSource, ShapeItem, TextItem, Verification
from chromasense.main.settings import Settings
from chromasense.main.wiring import build_app

KEY = "secret-key-value"
LOCAL_TEXT = "Quarterly"


def _png() -> bytes:
    image = Image.new("RGB", (640, 360), (255, 255, 255))
    draw = ImageDraw.Draw(image)
    draw.rectangle([40, 110, 240, 320], fill=(220, 30, 30))
    draw.ellipse([300, 120, 500, 320], fill=(30, 150, 30))
    draw.text((40, 30), LOCAL_TEXT, font=ImageFont.load_default(size=40), fill=(0, 0, 0))
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def _ai_text(position, text):
    return TextItem(f"ai-text-{position}", text, ItemSource.AI, Verification.UNVERIFIED)


@dataclass
class StubReader:
    read_result: AiRead | None = None
    answer: AiAnswer | None = None
    error: Exception | None = None
    reads: list = field(default_factory=list)
    asks: list = field(default_factory=list)

    def read(self, image, palette, image_type):
        self.reads.append((image, palette, image_type))
        if self.error:
            raise self.error
        return self.read_result

    def ask(self, image, palette, items, question):
        self.asks.append((image, palette, items, question))
        if self.error:
            raise self.error
        return self.answer


def _matching_read(cost=0.0) -> AiRead:
    return AiRead(
        chart_type="flat",
        legend=(),
        text_items=(_ai_text(1, LOCAL_TEXT.upper()), _ai_text(2, "Only AI")),
        shape_items=(
            ShapeItem(
                "ai-shape-1", "other", 99, "wrong name", ItemSource.AI, Verification.UNVERIFIED
            ),
        ),
        summary="A summary.",
        estimated_cost=cost,
    )


def _app(tmp_path, reader=None, **settings):
    return TestClient(build_app(Settings(data_dir=str(tmp_path), **settings), reader=reader))


def _upload(client) -> str:
    response = client.post(
        "/api/images", files={"file": ("a.png", BytesIO(_png()))}, data={"cvd_type": "none"}
    )
    assert response.status_code == 200
    return response.json()["image_id"]


def test_upload_makes_no_read_and_explain_makes_exactly_one(tmp_path):
    reader = StubReader(read_result=_matching_read())
    with _app(tmp_path, reader) as client:
        image_id = _upload(client)
        assert reader.reads == []
        assert client.post("/api/interpret", json={"image_id": image_id}).status_code == 200
        assert len(reader.reads) == 1


def test_matching_item_becomes_verified_and_each_item_has_a_state(tmp_path):
    reader = StubReader(read_result=_matching_read())
    with _app(tmp_path, reader) as client:
        image_id = _upload(client)
        analysis = client.get(f"/api/images/{image_id}/analysis").json()["analysis"]
        before = next(item for item in analysis["text"] if item["text"] == LOCAL_TEXT)
        assert (before["source"], before["verification"]) == ("local", "unverified")

        body = client.post("/api/interpret", json={"image_id": image_id}).json()

    items = {item["text"]: item for item in body["text_items"]}
    assert (items[LOCAL_TEXT]["source"], items[LOCAL_TEXT]["verification"]) == ("both", "verified")
    assert (items["Only AI"]["source"], items["Only AI"]["verification"]) == ("ai", "unverified")
    for group in ("text_items", "shape_items", "color_items"):
        assert all(item["verification"] in ("verified", "unverified") for item in body[group])
    assert body["summary"] == "A summary."


def test_wrong_ai_color_name_never_reaches_the_response_and_a_bad_id_is_unverified(tmp_path):
    reader = StubReader(read_result=_matching_read())
    with _app(tmp_path, reader) as client:
        response = client.post("/api/interpret", json={"image_id": _upload(client)})
    assert "wrong name" not in response.text
    colors = {item["item_id"]: item for item in response.json()["color_items"]}
    assert colors["color-unknown-99"]["verification"] == "unverified"
    assert colors["color-unknown-99"]["name"] is None


def test_unavailable_provider_returns_a_clear_503_and_other_features_still_work(tmp_path):
    reader = StubReader(error=AiUnavailable("The AI service is unavailable."))
    with _app(tmp_path, reader) as client:
        image_id = _upload(client)
        response = client.post("/api/interpret", json={"image_id": image_id})
        assert response.status_code == 503
        assert response.json()["error"]["message"] == "The AI service is unavailable."
        assert client.get(f"/api/images/{image_id}/analysis").status_code == 200
        assert (
            client.get(f"/api/images/{image_id}/render", params={"view": "original"}).status_code
            == 200
        )


def test_server_starts_and_upload_works_with_no_provider_configured(tmp_path):
    with _app(tmp_path) as client:
        image_id = _upload(client)
        response = client.post("/api/interpret", json={"image_id": image_id})
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "ai_unavailable"


@pytest.mark.parametrize(
    "body", [{}, {"image_id": "nope"}, {"image_id": "a" * 32, "extra": 1}], ids=str
)
def test_invalid_interpret_body_gets_a_422(tmp_path, body):
    with _app(tmp_path, StubReader()) as client:
        assert client.post("/api/interpret", json=body).status_code == 422


def test_unknown_image_gets_a_404(tmp_path):
    with _app(tmp_path, StubReader()) as client:
        assert client.post("/api/interpret", json={"image_id": "0" * 32}).status_code == 404


def test_second_explain_returns_the_same_result_without_a_new_read(tmp_path):
    reader = StubReader(read_result=_matching_read())
    with _app(tmp_path, reader) as client:
        image_id = _upload(client)
        first = client.post("/api/interpret", json={"image_id": image_id}).json()
        second = client.post("/api/interpret", json={"image_id": image_id}).json()
    assert first == second
    assert len(reader.reads) == 1


def _other_png(seed: int) -> bytes:
    pixels = np.full((60, 60, 3), seed, dtype=np.uint8)
    buffer = BytesIO()
    Image.fromarray(pixels).save(buffer, format="PNG")
    return buffer.getvalue()


def _upload_bytes(client, data) -> str:
    return client.post(
        "/api/images", files={"file": ("a.png", BytesIO(data))}, data={"cvd_type": "none"}
    ).json()["image_id"]


def test_requests_past_the_session_limit_get_a_429_and_no_read(tmp_path):
    reader = StubReader(read_result=_matching_read())
    with _app(tmp_path, reader, rate_limit_session=1) as client:
        first = _upload_bytes(client, _other_png(10))
        second = _upload_bytes(client, _other_png(20))
        assert client.post("/api/interpret", json={"image_id": first}).status_code == 200
        response = client.post("/api/interpret", json={"image_id": second})
    assert response.status_code == 429
    assert len(reader.reads) == 1


def test_requests_past_the_ip_limit_from_new_sessions_get_a_429_and_no_read(tmp_path):
    reader = StubReader(read_result=_matching_read())
    with _app(tmp_path, reader, rate_limit_ip=1) as client:
        first = _upload_bytes(client, _other_png(10))
        second = _upload_bytes(client, _other_png(20))
        assert client.post("/api/interpret", json={"image_id": first}).status_code == 200
        client.cookies.clear()
        response = client.post("/api/interpret", json={"image_id": second})
    assert response.status_code == 429
    assert len(reader.reads) == 1


def test_request_past_the_spend_cap_says_ai_is_temporarily_unavailable(tmp_path):
    reader = StubReader(read_result=_matching_read(cost=1.0))
    with _app(tmp_path, reader, spend_cap=1.0) as client:
        first = _upload_bytes(client, _other_png(10))
        second = _upload_bytes(client, _other_png(20))
        assert client.post("/api/interpret", json={"image_id": first}).status_code == 200
        response = client.post("/api/interpret", json={"image_id": second})
    assert response.status_code == 503
    assert response.json()["error"]["message"] == "AI is temporarily unavailable"
    assert len(reader.reads) == 1


def test_question_before_explain_gets_a_409_and_after_explain_gets_an_answer(tmp_path):
    reader = StubReader(
        read_result=_matching_read(),
        answer=AiAnswer("It shows sales.", ("text-1",), 0.0),
    )
    with _app(tmp_path, reader) as client:
        image_id = _upload(client)
        early = client.post("/api/ask", json={"image_id": image_id, "question": "What?"})
        assert early.status_code == 409
        assert reader.asks == []

        client.post("/api/interpret", json={"image_id": image_id})
        answer = client.post("/api/ask", json={"image_id": image_id, "question": "What?"})
    assert answer.status_code == 200
    assert answer.json() == {
        "text": "It shows sales.",
        "cited_item_ids": ["text-1"],
        "verification": "verified",
    }
    assert np.array_equal(reader.asks[0][0], reader.reads[0][0])
    assert reader.asks[0][1] == reader.reads[0][1]


@pytest.mark.parametrize(
    "question", ["", "   ", "x" * 1001, None, 5], ids=["empty", "blank", "long", "null", "number"]
)
def test_invalid_question_gets_a_422(tmp_path, question):
    with _app(tmp_path, StubReader()) as client:
        body = {"image_id": "a" * 32, "question": question}
        assert client.post("/api/ask", json=body).status_code == 422


def test_full_gateway_request_holds_none_of_the_local_results_and_no_key_leaks(tmp_path, caplog):
    captured = []

    def provider(request):
        captured.append(request)
        content = {
            "chart_type": "flat",
            "legend": [],
            "text_items": [{"text": LOCAL_TEXT}],
            "shape_items": [],
            "summary": "Summary.",
        }
        return httpx.Response(
            200, json={"choices": [{"message": {"content": json.dumps(content)}}]}
        )

    reader = HttpVisionReader(
        "https://provider.test/v1", KEY, "model", transport=httpx.MockTransport(provider)
    )
    with _app(tmp_path, reader) as client:
        image_id = _upload(client)
        assert captured == []
        analysis = client.get(f"/api/images/{image_id}/analysis").json()["analysis"]
        assert analysis["text"]
        response = client.post("/api/interpret", json={"image_id": image_id})

    assert len(captured) == 1
    body = json.loads(captured[0].content)
    message = body["messages"][1]["content"][0]["text"] + body["messages"][0]["content"]
    for item in analysis["text"]:
        assert item["text"] not in message
    assert (
        "shapes" not in message
        and "regions" not in message
        and "legend entries" not in (json.loads(body["messages"][1]["content"][0]["text"]))
    )
    assert set(json.loads(body["messages"][1]["content"][0]["text"])) == {"palette", "image_type"}
    assert KEY not in response.text
    assert KEY not in caplog.text
