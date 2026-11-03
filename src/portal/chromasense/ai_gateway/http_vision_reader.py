"""Call the third party vision model. This is the only module that talks to the provider."""

import base64
import json
from collections.abc import Sequence
from dataclasses import asdict
from enum import Enum
from importlib import resources
from io import BytesIO
from typing import Any

import httpx
from numpy.typing import NDArray
from PIL import Image

from chromasense.core.errors import AiUnavailable
from chromasense.core.models import (
    AiAnswer,
    AiRead,
    ItemSource,
    LegendEntry,
    ShapeItem,
    TextItem,
    Verification,
)
from color_engine.models import ImageType, Palette3

_TIMEOUT_SECONDS = 25.0
_UNAVAILABLE_MESSAGE = "The AI service is unavailable. Your other results are not affected."
_SHAPE_KINDS = {"circle", "rectangle", "triangle", "other"}
_ANSWER_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["text", "cited_item_ids"],
    "properties": {
        "text": {"type": "string"},
        "cited_item_ids": {"type": "array", "items": {"type": "string"}},
    },
}
_READ_INSTRUCTIONS = (
    "Read this image. Report the chart type, each legend entry with the palette ID of its color, "
    "each line of text, each distinct shape with its kind and the palette ID of its color, and a "
    "short summary of what the image shows. Use only palette IDs from the given palette. "
    "Answer with the requested JSON."
)
_ASK_INSTRUCTIONS = (
    "Answer the user's question about this image. Cite the ID of each given item that your answer "
    "relies on. Answer with the requested JSON."
)


class HttpVisionReader:
    def __init__(
        self,
        provider_url: str,
        api_key: str,
        model: str,
        cost_per_request: float = 0.0,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self._url = provider_url
        self._api_key = api_key
        self._model = model
        self._cost = cost_per_request
        self._transport = transport

    def read(self, image: NDArray, palette: Palette3, image_type: ImageType) -> AiRead:
        user_content = {"palette": _palette_json(palette), "image_type": image_type.value}
        schema = json.loads(
            resources.files("chromasense.ai_gateway").joinpath("read_schema.json").read_text()
        )
        content = self._post(_READ_INSTRUCTIONS, user_content, image, "image_read", schema)
        return self._parse_read(content)

    def ask(
        self, image: NDArray, palette: Palette3, items: Sequence[object], question: str
    ) -> AiAnswer:
        user_content = {
            "palette": _palette_json(palette),
            "items": [_item_json(item) for item in items],
            "question": question,
        }
        content = self._post(_ASK_INSTRUCTIONS, user_content, image, "answer", _ANSWER_SCHEMA)
        return self._parse_answer(content)

    def _post(
        self, instructions: str, user_content: dict, image: NDArray, name: str, schema: dict
    ) -> dict[str, Any]:
        if not (self._url and self._api_key and self._model):
            raise AiUnavailable(_UNAVAILABLE_MESSAGE)
        body = _build_provider_request(
            self._model, instructions, user_content, _png_base64(image), name, schema
        )
        headers = {"Authorization": f"Bearer {self._api_key}"}
        try:
            with httpx.Client(timeout=_TIMEOUT_SECONDS, transport=self._transport) as client:
                response = client.post(self._url, json=body, headers=headers)
            response.raise_for_status()
            return _parse_provider_response(response.json())
        except (httpx.HTTPError, ValueError, KeyError, IndexError, TypeError):
            # The original error is dropped, so that no request detail reaches a message or log.
            raise AiUnavailable(_UNAVAILABLE_MESSAGE) from None

    def _parse_read(self, content: dict[str, Any]) -> AiRead:
        try:
            return AiRead(
                chart_type=str(content["chart_type"]),
                legend=tuple(
                    LegendEntry(
                        item_id=f"ai-legend-{position}",
                        palette_id=_optional_int(entry.get("palette_id")),
                        text=str(entry["text"]),
                        source=ItemSource.AI,
                        verification=Verification.UNVERIFIED,
                    )
                    for position, entry in enumerate(content["legend"], start=1)
                ),
                text_items=tuple(
                    TextItem(
                        item_id=f"ai-text-{position}",
                        text=str(entry["text"]),
                        source=ItemSource.AI,
                        verification=Verification.UNVERIFIED,
                    )
                    for position, entry in enumerate(content["text_items"], start=1)
                ),
                shape_items=tuple(
                    ShapeItem(
                        item_id=f"ai-shape-{position}",
                        kind=entry["kind"] if entry["kind"] in _SHAPE_KINDS else "other",
                        palette_id=_optional_int(entry.get("palette_id")),
                        color_name=None,
                        source=ItemSource.AI,
                        verification=Verification.UNVERIFIED,
                    )
                    for position, entry in enumerate(content["shape_items"], start=1)
                ),
                summary=str(content["summary"]),
                estimated_cost=self._cost,
            )
        except (KeyError, TypeError, AttributeError):
            raise AiUnavailable(_UNAVAILABLE_MESSAGE) from None

    def _parse_answer(self, content: dict[str, Any]) -> AiAnswer:
        try:
            return AiAnswer(
                text=str(content["text"]),
                cited_item_ids=tuple(str(item) for item in content["cited_item_ids"]),
                estimated_cost=self._cost,
            )
        except (KeyError, TypeError):
            raise AiUnavailable(_UNAVAILABLE_MESSAGE) from None


def _build_provider_request(
    model: str,
    instructions: str,
    user_content: dict,
    image_base64: str,
    schema_name: str,
    schema: dict,
) -> dict[str, Any]:
    """Build the provider's request. Choosing a provider changes this function."""
    return {
        "model": model,
        "messages": [
            {"role": "system", "content": instructions},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": json.dumps(user_content)},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{image_base64}"},
                    },
                ],
            },
        ],
        "response_format": {
            "type": "json_schema",
            "json_schema": {"name": schema_name, "strict": True, "schema": schema},
        },
    }


def _parse_provider_response(payload: dict[str, Any]) -> dict[str, Any]:
    """Read the provider's response. Choosing a provider changes this function."""
    content = json.loads(payload["choices"][0]["message"]["content"])
    if not isinstance(content, dict):
        raise ValueError("the response is not a JSON object")
    return content


def _palette_json(palette: Palette3) -> list[dict[str, Any]]:
    return [
        {"id": entry.id, "hex": "#{:02X}{:02X}{:02X}".format(*entry.rgb)}
        for entry in palette.entries
    ]


def _item_json(item: object) -> dict[str, Any]:
    return {
        key: value.value if isinstance(value, Enum) else value
        for key, value in asdict(item).items()
        if value is not None
    }


def _png_base64(image: NDArray) -> str:
    buffer = BytesIO()
    Image.fromarray(image).save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("ascii")


def _optional_int(value: Any) -> int | None:
    return value if isinstance(value, int) and not isinstance(value, bool) else None
