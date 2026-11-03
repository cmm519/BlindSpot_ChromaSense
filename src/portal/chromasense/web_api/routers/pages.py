"""Server-rendered pages and their static files."""

import re
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, FastAPI, Query, Request
from fastapi import Path as PathParam
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

_WEB_UI = Path(__file__).resolve().parents[2] / "web_ui"
_IMAGE_ID = re.compile(r"[0-9a-f]{32}")

templates = Jinja2Templates(directory=_WEB_UI / "templates")
pages_router = APIRouter(default_response_class=HTMLResponse)


def add_pages(app: FastAPI) -> None:
    app.include_router(pages_router)
    app.mount("/static", StaticFiles(directory=_WEB_UI / "static"), name="static")


def _page(request: Request, name: str, image_id: str | None) -> HTMLResponse:
    valid_id = image_id if image_id and _IMAGE_ID.fullmatch(image_id) else None
    return templates.TemplateResponse(request, name, {"image_id": valid_id})


@pages_router.get("/")
def home(request: Request, image_id: Annotated[str | None, Query()] = None) -> HTMLResponse:
    return _page(request, "home.html", image_id)


@pages_router.get("/workspace/{image_id}")
def workspace(
    request: Request, image_id: Annotated[str, PathParam(pattern=r"^[0-9a-f]{32}$")]
) -> HTMLResponse:
    return _page(request, "workspace.html", image_id)


@pages_router.get("/simulator")
def simulator(request: Request, image_id: Annotated[str | None, Query()] = None) -> HTMLResponse:
    return _page(request, "simulator.html", image_id)


@pages_router.get("/settings")
def settings(request: Request, image_id: Annotated[str | None, Query()] = None) -> HTMLResponse:
    return _page(request, "settings.html", image_id)


@pages_router.get("/intro")
def intro(request: Request, image_id: Annotated[str | None, Query()] = None) -> HTMLResponse:
    return _page(request, "intro.html", image_id)
