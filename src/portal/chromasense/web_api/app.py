"""App factory: routers, session cookie, request log, and the mapping of errors to responses."""

import logging
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException

from chromasense.core.errors import (
    AiRateLimited,
    AiSpendCapReached,
    AiUnavailable,
    CoreError,
    ImageNotFound,
    InvalidCoordinates,
    InvalidImage,
    NoEnhancementForProfile,
    NotInterpreted,
)
from chromasense.web_api.routers.ai import ai_router
from chromasense.web_api.routers.images import images_router
from chromasense.web_api.routers.pages import add_pages
from chromasense.web_api.schemas import InvalidProfile, UploadTooLarge
from chromasense.web_api.session import session_id_from, set_session_cookie

access_log = logging.getLogger("chromasense.access")

_CORE_ERRORS: dict[type[CoreError], tuple[int, str]] = {
    InvalidImage: (400, "invalid_image"),
    InvalidCoordinates: (422, "invalid_coordinates"),
    ImageNotFound: (404, "image_not_found"),
    NoEnhancementForProfile: (409, "no_enhancement_for_profile"),
    NotInterpreted: (409, "not_interpreted"),
    AiUnavailable: (503, "ai_unavailable"),
    AiRateLimited: (429, "ai_rate_limited"),
    AiSpendCapReached: (503, "ai_spend_cap_reached"),
}


@dataclass(frozen=True)
class UseCases:
    process_upload: Any
    get_analysis: Any
    reanalyze_for_profile: Any
    render_view: Any
    identify_color: Any
    export_image: Any
    interpret_image: Any = None
    answer_question: Any = None


def create_app(use_cases: UseCases, lifespan: Callable | None = None) -> FastAPI:
    app = FastAPI(
        title="ChromaSense", docs_url=None, redoc_url=None, openapi_url=None, lifespan=lifespan
    )
    app.state.use_cases = use_cases
    app.include_router(images_router)
    app.include_router(ai_router)
    add_pages(app)
    _add_error_handlers(app)
    _add_session_and_log(app)
    return app


def _error(status: int, code: str, message: str) -> JSONResponse:
    return JSONResponse({"error": {"code": code, "message": message}}, status_code=status)


def _add_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(CoreError)
    def handle_core_error(_: Request, error: CoreError) -> JSONResponse:
        status, code = _CORE_ERRORS[type(error)]
        return _error(status, code, str(error))

    @app.exception_handler(RequestValidationError)
    def handle_validation(_: Request, error: RequestValidationError) -> JSONResponse:
        fields = sorted({str(item["loc"][-1]) for item in error.errors()})
        return _error(422, "invalid_request", f"These values are not valid: {', '.join(fields)}")

    @app.exception_handler(InvalidProfile)
    def handle_profile(_: Request, error: InvalidProfile) -> JSONResponse:
        return _error(422, "invalid_request", str(error))

    @app.exception_handler(UploadTooLarge)
    def handle_too_large(_: Request, error: UploadTooLarge) -> JSONResponse:
        return _error(413, "upload_too_large", str(error))

    @app.exception_handler(HTTPException)
    def handle_http(_: Request, error: HTTPException) -> JSONResponse:
        return _error(error.status_code, "http_error", str(error.detail))


def _add_session_and_log(app: FastAPI) -> None:
    @app.middleware("http")
    async def session_and_log(request: Request, call_next):
        session_id, is_new = session_id_from(request)
        request.state.session_id = session_id
        response = await call_next(request)
        if is_new:
            set_session_cookie(response, session_id)
        route = request.scope.get("route")
        template = getattr(route, "path", "unmatched")
        access_log.info(
            "%s %s %s session=%s", request.method, template, response.status_code, session_id
        )
        return response
