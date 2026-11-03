import base64
import json
from io import BytesIO

import httpx
import numpy as np
import pytest
from PIL import Image

from chromasense.ai_gateway.http_vision_reader import HttpVisionReader
from chromasense.core.errors import AiUnavailable
from chromasense.core.models import ItemSource, TextItem, Verification
from color_engine.models import ImageType, Palette3, PaletteEntry

URL = "https://provider.test/v1/chat/completions"
KEY = "secret-key-value"
MODEL = "vision-model"
PALETTE = Palette3((PaletteEntry(1, (255, 0, 0), (53.0, 80.0, 67.0), 1.0),))
IMAGE = np.full((4, 6, 3), (255, 0, 0), dtype=np.uint8)
READ_JSON = {
    "chart_type": "bar",
    "legend": [{"palette_id": 1, "text": "North", "color_name": "wrong name"}],
    "text_items": [{"text": "Title"}],
    "shape_items": [{"kind": "circle", "palette_id": 1, "color_name": "wrong name"}],
    "summary": "A chart.",
}


def _provider(content, status=200, captured=None):
    def handler(request):
        if captured is not None:
            captured.append(request)
        body = {"choices": [{"message": {"content": json.dumps(content)}}]}
        return httpx.Response(status, json=body)

    return httpx.MockTransport(handler)


def _reader(transport, url=URL, key=KEY, model=MODEL, cost=0.5):
    return HttpVisionReader(url, key, model, cost, transport=transport)


def test_request_has_the_image_palette_type_schema_and_bearer_token():
    captured = []
    read = _reader(_provider(READ_JSON, captured=captured)).read(IMAGE, PALETTE, ImageType.CHART)

    assert len(captured) == 1
    request = captured[0]
    assert str(request.url) == URL
    assert request.headers["authorization"] == f"Bearer {KEY}"
    body = json.loads(request.content)
    assert body["model"] == MODEL
    schema = body["response_format"]["json_schema"]["schema"]
    assert set(schema["required"]) == {
        "chart_type",
        "legend",
        "text_items",
        "shape_items",
        "summary",
    }
    content = body["messages"][1]["content"]
    sent = json.loads(content[0]["text"])
    assert sent == {"palette": [{"id": 1, "hex": "#FF0000"}], "image_type": "chart"}
    url = content[1]["image_url"]["url"]
    assert url.startswith("data:image/png;base64,")
    with Image.open(BytesIO(base64.b64decode(url.split(",", 1)[1]))) as sent_image:
        assert np.array_equal(np.array(sent_image), IMAGE)
    assert read.estimated_cost == 0.5


def test_read_signature_cannot_receive_local_results():
    import inspect

    assert list(inspect.signature(HttpVisionReader.read).parameters) == [
        "self",
        "image",
        "palette",
        "image_type",
    ]


def test_ai_color_names_are_parsed_and_discarded():
    read = _reader(_provider(READ_JSON)).read(IMAGE, PALETTE, ImageType.CHART)
    assert read.shape_items[0].color_name is None
    assert "wrong name" not in repr(read)
    assert read.legend[0].palette_id == 1
    assert {read.text_items[0].source, read.shape_items[0].source} == {ItemSource.AI}
    assert read.text_items[0].verification is Verification.UNVERIFIED


def test_unexpected_kind_becomes_other_and_a_bad_palette_id_becomes_missing():
    content = {
        **READ_JSON,
        "shape_items": [{"kind": "hexagon", "palette_id": "one"}],
        "legend": [{"text": "No ID"}],
    }
    read = _reader(_provider(content)).read(IMAGE, PALETTE, ImageType.CHART)
    assert read.shape_items[0].kind == "other"
    assert read.shape_items[0].palette_id is None
    assert read.legend[0].palette_id is None


def _raises_connect_error():
    def handler(request):
        raise httpx.ConnectError("could not connect", request=request)

    return httpx.MockTransport(handler)


def _raises_timeout():
    def handler(request):
        raise httpx.ReadTimeout("too slow", request=request)

    return httpx.MockTransport(handler)


@pytest.mark.parametrize(
    "transport",
    [
        _raises_connect_error(),
        _raises_timeout(),
        _provider(READ_JSON, status=500),
        _provider(READ_JSON, status=401),
        httpx.MockTransport(lambda request: httpx.Response(200, text="not json")),
        httpx.MockTransport(lambda request: httpx.Response(200, json={"unexpected": True})),
        _provider({"missing": "fields"}),
        _provider(["not", "an", "object"]),
    ],
    ids=[
        "connect",
        "timeout",
        "server-error",
        "unauthorized",
        "not-json",
        "wrong-shape",
        "missing-fields",
        "not-object",
    ],
)
def test_each_failure_raises_unavailable_with_no_key_in_the_message(transport):
    with pytest.raises(AiUnavailable) as caught:
        _reader(transport).read(IMAGE, PALETTE, ImageType.CHART)
    assert KEY not in str(caught.value)
    assert caught.value.__cause__ is None
    assert caught.value.__suppress_context__ is True


@pytest.mark.parametrize(
    ("url", "key", "model"),
    [("", KEY, MODEL), (URL, "", MODEL), (URL, KEY, "")],
    ids=["no-url", "no-key", "no-model"],
)
def test_missing_setting_raises_unavailable_with_no_request(url, key, model):
    captured = []
    with pytest.raises(AiUnavailable):
        _reader(_provider(READ_JSON, captured=captured), url, key, model).read(
            IMAGE, PALETTE, ImageType.CHART
        )
    assert captured == []


def test_ask_sends_the_image_palette_items_and_question_and_parses_citations():
    captured = []
    content = {"text": "It rises.", "cited_item_ids": ["text-1"]}
    item = TextItem("text-1", "Title", ItemSource.BOTH, Verification.VERIFIED)
    answer = _reader(_provider(content, captured=captured)).ask(
        IMAGE, PALETTE, [item], "What happens?"
    )

    assert (answer.text, answer.cited_item_ids, answer.estimated_cost) == (
        "It rises.",
        ("text-1",),
        0.5,
    )
    body = json.loads(captured[0].content)
    sent = json.loads(body["messages"][1]["content"][0]["text"])
    assert sent["question"] == "What happens?"
    assert sent["palette"] == [{"id": 1, "hex": "#FF0000"}]
    assert sent["items"][0] == {
        "item_id": "text-1",
        "text": "Title",
        "source": "both",
        "verification": "verified",
    }
    assert body["messages"][1]["content"][1]["image_url"]["url"].startswith("data:image/png")


def test_malformed_answer_raises_unavailable():
    with pytest.raises(AiUnavailable):
        _reader(_provider({"text": "no citations"})).ask(IMAGE, PALETTE, [], "Why?")
