"""REST endpoints for images. Each one checks shape, calls one use case, and maps the result."""

from typing import Annotated

from fastapi import APIRouter, File, Form, Path, Query, Request, Response, UploadFile

from chromasense.core.use_cases.export_image import ExportImageRequest
from chromasense.core.use_cases.get_analysis import GetAnalysisRequest
from chromasense.core.use_cases.identify_color import IdentifyColorRequest
from chromasense.core.use_cases.process_upload import ProcessUploadRequest
from chromasense.core.use_cases.reanalyze_for_profile import ReanalyzeRequest
from chromasense.core.use_cases.render_view import RenderViewRequest
from chromasense.web_api.schemas import (
    AnalysisResponseSchema,
    ColorResponseSchema,
    CvdTypeName,
    ProfileBody,
    ReanalyzeResponseSchema,
    UnitInterval,
    UploadResponseSchema,
    UploadTooLarge,
    ViewName,
    analysis_schema,
    color_schema,
    group_schemas,
    pair_schemas,
    to_profile,
)

MAX_UPLOAD_BYTES = 10 * 1024 * 1024
_ID_PATTERN = r"^[0-9a-f]{32}$"

images_router = APIRouter(prefix="/api/images")

ImageIdPath = Annotated[str, Path(pattern=_ID_PATTERN)]
CvdTypeQuery = Annotated[CvdTypeName, Query()]
SeverityQuery = Annotated[UnitInterval | None, Query()]
StrengthQuery = Annotated[UnitInterval, Query()]


@images_router.post("")
def upload_image(
    request: Request,
    file: Annotated[UploadFile, File()],
    cvd_type: Annotated[CvdTypeName, Form()],
    severity: Annotated[UnitInterval | None, Form()] = None,
) -> UploadResponseSchema:
    profile = to_profile(cvd_type, severity)
    data = file.file.read(MAX_UPLOAD_BYTES + 1)
    if len(data) > MAX_UPLOAD_BYTES:
        raise UploadTooLarge("The image is larger than the 10 MB limit")
    result = request.app.state.use_cases.process_upload.execute(ProcessUploadRequest(data, profile))
    return UploadResponseSchema(
        image_id=result.image_id,
        analysis=analysis_schema(result.analysis),
        pairs=pair_schemas(result.pairs),
        groups=group_schemas(result.groups),
        remaining_pair_count=result.remaining_pair_count,
        enhancement_needed=result.enhancement_needed,
    )


@images_router.post("/{image_id}/analyze")
def analyze_image(
    request: Request, image_id: ImageIdPath, body: ProfileBody
) -> ReanalyzeResponseSchema:
    profile = to_profile(body.cvd_type, body.severity)
    use_case = request.app.state.use_cases.reanalyze_for_profile
    result = use_case.execute(ReanalyzeRequest(image_id, profile))
    return ReanalyzeResponseSchema(
        image_id=result.image_id,
        pairs=pair_schemas(result.pairs),
        groups=group_schemas(result.groups),
        remaining_pair_count=result.remaining_pair_count,
        enhancement_needed=result.enhancement_needed,
    )


@images_router.get("/{image_id}/render")
def render_image(
    request: Request,
    image_id: ImageIdPath,
    view: Annotated[ViewName, Query()],
    cvd_type: CvdTypeQuery = "none",
    severity: SeverityQuery = None,
    strength: StrengthQuery = 1.0,
) -> Response:
    profile = to_profile(cvd_type, severity)
    result = request.app.state.use_cases.render_view.execute(
        RenderViewRequest(image_id, view, profile, strength)
    )
    return Response(result.png, media_type="image/png")


@images_router.get("/{image_id}/analysis")
def get_analysis(request: Request, image_id: ImageIdPath) -> AnalysisResponseSchema:
    result = request.app.state.use_cases.get_analysis.execute(GetAnalysisRequest(image_id))
    return AnalysisResponseSchema(
        image_id=result.image_id, analysis=analysis_schema(result.analysis)
    )


@images_router.get("/{image_id}/color")
def get_color(
    request: Request,
    image_id: ImageIdPath,
    x: Annotated[int, Query(ge=0)],
    y: Annotated[int, Query(ge=0)],
    cvd_type: CvdTypeQuery = "none",
    severity: SeverityQuery = None,
) -> ColorResponseSchema:
    profile = to_profile(cvd_type, severity)
    result = request.app.state.use_cases.identify_color.execute(
        IdentifyColorRequest(image_id, x, y, profile)
    )
    return ColorResponseSchema(
        color=color_schema(result.color),
        simulated_rgb=result.simulated_rgb,
        simulated_hex=result.simulated_hex,
    )


@images_router.get("/{image_id}/export")
def export_image(
    request: Request,
    image_id: ImageIdPath,
    cvd_type: CvdTypeQuery = "none",
    severity: SeverityQuery = None,
    strength: StrengthQuery = 1.0,
) -> Response:
    profile = to_profile(cvd_type, severity)
    result = request.app.state.use_cases.export_image.execute(
        ExportImageRequest(image_id, profile, strength)
    )
    headers = {"Content-Disposition": f'attachment; filename="chromasense-{image_id}.png"'}
    return Response(result.png, media_type="image/png", headers=headers)
