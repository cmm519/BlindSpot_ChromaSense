"""REST endpoints for AI interpretation and questions."""

from fastapi import APIRouter, Request

from chromasense.core.use_cases.answer_question import AnswerQuestionRequest
from chromasense.core.use_cases.interpret_image import InterpretImageRequest
from chromasense.web_api.schemas import (
    AnswerResponseSchema,
    AskBody,
    InterpretationSchema,
    InterpretBody,
)

ai_router = APIRouter(prefix="/api")


def _client_address(request: Request) -> str:
    return request.client.host if request.client else "unknown"


@ai_router.post("/interpret")
def interpret(request: Request, body: InterpretBody) -> InterpretationSchema:
    result = request.app.state.use_cases.interpret_image.execute(
        InterpretImageRequest(body.image_id, request.state.session_id, _client_address(request))
    )
    return InterpretationSchema.model_validate(result)


@ai_router.post("/ask")
def ask(request: Request, body: AskBody) -> AnswerResponseSchema:
    result = request.app.state.use_cases.answer_question.execute(
        AnswerQuestionRequest(
            body.image_id, body.question, request.state.session_id, _client_address(request)
        )
    )
    return AnswerResponseSchema.model_validate(result)
