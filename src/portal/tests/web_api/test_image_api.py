import logging
import re
from dataclasses import dataclass
from io import BytesIO

import pytest
from fastapi.testclient import TestClient

from chromasense.core.errors import (
    ImageNotFound,
    InvalidCoordinates,
    InvalidImage,
    NoEnhancementForProfile,
)
from chromasense.core.models import (
    ColorItem,
    ImageAnalysis,
    ItemSource,
    PatternGroup,
    ShapeItem,
    TextItem,
    Verification,
)
from chromasense.web_api.app import UseCases, create_app
from chromasense.web_api.routers.images import MAX_UPLOAD_BYTES, images_router
from chromasense.web_api.session import COOKIE_NAME
from color_engine.models import (
    ColorInfo,
    ConfusablePair,
    CvdType,
    ImageType,
    Palette3,
    PaletteEntry,
    Region,
)

IMAGE_ID = "a" * 32
PNG_BYTES = b"\x89PNG fake"
PATH = f"/api/images/{IMAGE_ID}"
ANALYSIS = ImageAnalysis(
    palette=Palette3((PaletteEntry(1, (255, 0, 0), (53.0, 80.0, 67.0), 1.0),)),
    regions=(Region(1, 1, 0, 0, 10, 10, 100, 4.5, 4.5),),
    shapes=(
        ShapeItem(
            "shape-1", "circle", 1, "red", ItemSource.LOCAL, Verification.UNVERIFIED, 0, 0, 10, 10
        ),
    ),
    text=(TextItem("text-1", "Hello", ItemSource.LOCAL, Verification.UNVERIFIED, 1, 2, 3, 4),),
    legend=(),
    image_type=ImageType.CHART,
    color_items=(
        ColorItem(
            "color-1",
            1,
            "red",
            "#FF0000",
            (255, 0, 0),
            (0, 100, 50),
            "red",
            ItemSource.LOCAL,
            Verification.VERIFIED,
            1.0,
        ),
    ),
    summary="Chart with 1 color.",
    width=10,
    height=10,
)
PAIR = ConfusablePair(1, 2, 70.0, 3.0)


@dataclass
class Result:
    image_id: str = IMAGE_ID
    analysis: ImageAnalysis = ANALYSIS
    pairs: tuple = (PAIR,)
    groups: tuple = (PatternGroup(1, (1, 2), "hatching"),)
    remaining_pair_count: int | None = 0
    enhancement_needed: bool = True
    png: bytes = PNG_BYTES
    color: ColorInfo = ColorInfo("red", "#FF0000", (255, 0, 0), (0, 100, 50), "red")
    simulated_rgb: tuple | None = (120, 120, 0)
    simulated_hex: str | None = "#787800"


class FakeUseCase:
    def __init__(self, error: Exception | None = None) -> None:
        self.requests = []
        self.error = error

    def execute(self, request):
        self.requests.append(request)
        if self.error is not None:
            raise self.error
        return Result()


def _client(**overrides):
    fakes = {
        name: overrides.get(name, FakeUseCase())
        for name in (
            "process_upload",
            "get_analysis",
            "reanalyze_for_profile",
            "render_view",
            "identify_color",
            "export_image",
        )
    }
    return TestClient(create_app(UseCases(**fakes)), raise_server_exceptions=True), fakes


def _upload(client, data=b"image", **form):
    form.setdefault("cvd_type", "none")
    return client.post("/api/images", files={"file": ("a.png", BytesIO(data))}, data=form)


def test_upload_maps_the_result_to_json():
    client, fakes = _client()
    response = _upload(client, cvd_type="deutan", severity="0.5")
    assert response.status_code == 200
    body = response.json()
    assert body["image_id"] == IMAGE_ID
    assert body["analysis"]["image_type"] == "chart"
    assert body["analysis"]["text"][0]["source"] == "local"
    assert body["analysis"]["text"][0]["verification"] == "unverified"
    assert body["analysis"]["color_items"][0]["verification"] == "verified"
    assert body["pairs"][0]["simulated_distance"] == 3.0
    assert body["groups"] == [{"group_id": 1, "palette_ids": [1, 2], "pattern": "hatching"}]
    assert (body["analysis"]["width"], body["analysis"]["height"]) == (10, 10)
    request = fakes["process_upload"].requests[0]
    assert request.profile.type is CvdType.DEUTAN
    assert request.profile.severity == 0.5


def test_analysis_endpoint_returns_each_stored_result():
    client, fakes = _client()
    body = client.get(f"{PATH}/analysis").json()["analysis"]
    assert body["regions"][0]["area"] == 100
    assert body["shapes"][0]["kind"] == "circle"
    assert body["text"][0]["text"] == "Hello"
    assert body["legend"] == []
    assert body["image_type"] == "chart"
    assert fakes["get_analysis"].requests[0].image_id == IMAGE_ID


def test_analyze_endpoint_carries_the_profile():
    client, fakes = _client()
    response = client.post(f"{PATH}/analyze", json={"cvd_type": "tritan", "severity": 1})
    assert response.status_code == 200
    assert response.json()["enhancement_needed"] is True
    assert fakes["reanalyze_for_profile"].requests[0].profile.type is CvdType.TRITAN


def test_render_returns_a_png_and_carries_view_profile_and_strength():
    client, fakes = _client()
    response = client.get(
        f"{PATH}/render",
        params={"view": "enhanced", "cvd_type": "deutan", "severity": 1, "strength": 0.25},
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    assert response.content == PNG_BYTES
    request = fakes["render_view"].requests[0]
    assert (request.view, request.strength) == ("enhanced", 0.25)


def test_color_returns_values_and_the_simulated_color():
    client, fakes = _client()
    body = client.get(
        f"{PATH}/color", params={"x": 3, "y": 4, "cvd_type": "protan", "severity": 1}
    ).json()
    assert body["color"]["name"] == "red"
    assert body["color"]["hex"] == "#FF0000"
    assert body["simulated_hex"] == "#787800"
    assert (fakes["identify_color"].requests[0].x, fakes["identify_color"].requests[0].y) == (3, 4)


def test_export_downloads_a_png_attachment():
    client, _ = _client()
    response = client.get(f"{PATH}/export", params={"cvd_type": "deutan", "severity": 1})
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    assert "attachment" in response.headers["content-disposition"]


@pytest.mark.parametrize(
    ("method", "url"),
    [
        ("get", "/api/images/not-an-id/analysis"),
        ("get", "/api/images/%2e%2e%2fsecret/analysis"),
        ("get", f"/api/images/{'A' * 32}/analysis"),
        ("get", f"/api/images/{'a' * 31}/analysis"),
        ("get", f"/api/images/{'a' * 32}%0A/analysis"),
        ("get", "/api/images/not-an-id/render?view=original"),
        ("get", "/api/images/not-an-id/color?x=0&y=0"),
        ("get", "/api/images/not-an-id/export?cvd_type=deutan&severity=1"),
    ],
)
def test_invalid_id_gets_a_client_error_and_reaches_no_use_case(method, url):
    client, fakes = _client()
    response = getattr(client, method)(url)
    assert 400 <= response.status_code < 500
    assert all(fake.requests == [] for fake in fakes.values())


@pytest.mark.parametrize(
    "params",
    [
        {"view": "original", "cvd_type": "purple"},
        {"view": "original", "cvd_type": "deutan"},
        {"view": "original", "cvd_type": "deutan", "severity": 2},
        {"view": "original", "cvd_type": "deutan", "severity": -0.1},
        {"view": "original", "cvd_type": "deutan", "severity": "nan"},
        {"view": "original", "cvd_type": "deutan", "severity": "inf"},
        {"view": "original", "cvd_type": "deutan", "severity": "abc"},
        {"view": "original", "cvd_type": "none", "severity": 0.5},
        {"view": "sideways"},
        {},
        {"view": "enhanced", "cvd_type": "deutan", "severity": 1, "strength": 1.5},
        {"view": "enhanced", "cvd_type": "deutan", "severity": 1, "strength": "nan"},
    ],
)
def test_invalid_render_values_get_a_structured_422(params):
    client, fakes = _client()
    response = client.get(f"{PATH}/render", params=params)
    assert response.status_code == 422
    assert set(response.json()["error"]) == {"code", "message"}
    assert fakes["render_view"].requests == []


@pytest.mark.parametrize(
    "params",
    [
        {"x": -1, "y": 0},
        {"x": 0, "y": -1},
        {"x": "a", "y": 0},
        {"x": 1.5, "y": 0},
        {"x": 0},
        {"y": 0},
        {},
    ],
)
def test_invalid_coordinates_get_a_422(params):
    client, fakes = _client()
    assert client.get(f"{PATH}/color", params=params).status_code == 422
    assert fakes["identify_color"].requests == []


@pytest.mark.parametrize(
    "form",
    [
        {"cvd_type": "purple"},
        {"cvd_type": "deutan"},
        {"cvd_type": "deutan", "severity": "9"},
        {"cvd_type": "none", "severity": "0.5"},
    ],
)
def test_invalid_upload_profile_gets_a_422(form):
    client, fakes = _client()
    assert _upload(client, **form).status_code == 422
    assert fakes["process_upload"].requests == []


def test_upload_with_no_file_or_no_profile_gets_a_422():
    client, _ = _client()
    assert client.post("/api/images", data={"cvd_type": "none"}).status_code == 422
    files = {"file": ("a.png", BytesIO(b"x"))}
    assert client.post("/api/images", files=files).status_code == 422


def test_analyze_with_a_bad_body_gets_a_422():
    client, _ = _client()
    assert client.post(f"{PATH}/analyze", json={"cvd_type": "x"}).status_code == 422
    assert client.post(f"{PATH}/analyze", content=b"not json").status_code == 422
    assert client.post(f"{PATH}/analyze", json={"cvd_type": "deutan"}).status_code == 422


def test_upload_of_exactly_ten_megabytes_is_accepted():
    client, fakes = _client()
    assert _upload(client, data=b"x" * MAX_UPLOAD_BYTES).status_code == 200
    assert len(fakes["process_upload"].requests[0].data) == 10 * 1024 * 1024


def test_upload_over_ten_megabytes_is_rejected_with_a_message():
    client, fakes = _client()
    response = _upload(client, data=b"x" * (MAX_UPLOAD_BYTES + 1))
    assert response.status_code == 413
    assert "10 MB" in response.json()["error"]["message"]
    assert fakes["process_upload"].requests == []


@pytest.mark.parametrize(
    ("use_case", "error", "status", "code"),
    [
        ("process_upload", InvalidImage("bad file"), 400, "invalid_image"),
        ("get_analysis", ImageNotFound("missing"), 404, "image_not_found"),
        ("identify_color", InvalidCoordinates("outside"), 422, "invalid_coordinates"),
        ("export_image", NoEnhancementForProfile("no cvd"), 409, "no_enhancement_for_profile"),
    ],
)
def test_core_errors_map_to_statuses(use_case, error, status, code):
    client, _ = _client(**{use_case: FakeUseCase(error)})
    calls = {
        "process_upload": lambda: _upload(client),
        "get_analysis": lambda: client.get(f"{PATH}/analysis"),
        "identify_color": lambda: client.get(f"{PATH}/color", params={"x": 0, "y": 0}),
        "export_image": lambda: client.get(f"{PATH}/export"),
    }
    response = calls[use_case]()
    assert response.status_code == status
    assert response.json()["error"]["code"] == code
    assert response.json()["error"]["message"] == str(error)


def test_new_client_gets_an_anonymous_http_only_cookie_and_keeps_it():
    client, _ = _client()
    first = client.get(f"{PATH}/analysis")
    cookie = first.headers["set-cookie"]
    assert cookie.startswith(f"{COOKIE_NAME}=")
    assert "httponly" in cookie.casefold()
    assert "samesite=lax" in cookie.casefold()
    assert "secure" not in cookie.casefold()
    assert "set-cookie" not in client.get(f"{PATH}/analysis").headers


def test_no_endpoint_requires_a_sign_in():
    client, _ = _client()
    for response in (
        _upload(client),
        client.get(f"{PATH}/analysis"),
        client.get(f"{PATH}/render", params={"view": "original"}),
        client.get(f"{PATH}/color", params={"x": 0, "y": 0}),
    ):
        assert response.status_code not in (401, 403)


def test_a_malformed_cookie_is_replaced():
    client, _ = _client()
    client.cookies.set(COOKIE_NAME, "bad value!")
    assert COOKIE_NAME in client.get(f"{PATH}/analysis").headers["set-cookie"]


def test_each_request_logs_method_template_status_and_session_and_no_header(caplog):
    client, _ = _client()
    with caplog.at_level(logging.INFO, logger="chromasense.access"):
        client.get(f"{PATH}/analysis", headers={"X-Secret": "do-not-log"})
    message = caplog.records[-1].getMessage()
    assert re.fullmatch(r"GET /api/images/\{image_id\}/analysis 200 session=\S+", message)
    assert "do-not-log" not in caplog.text
    assert IMAGE_ID not in message


def test_only_the_endpoints_in_the_srs_table_exist():
    routes = {(method, route.path) for route in images_router.routes for method in route.methods}
    assert routes == {
        ("POST", "/api/images"),
        ("POST", "/api/images/{image_id}/analyze"),
        ("GET", "/api/images/{image_id}/render"),
        ("GET", "/api/images/{image_id}/analysis"),
        ("GET", "/api/images/{image_id}/color"),
        ("GET", "/api/images/{image_id}/export"),
    }
