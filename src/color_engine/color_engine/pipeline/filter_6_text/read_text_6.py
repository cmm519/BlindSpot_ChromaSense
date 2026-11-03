"""Filter 6: read English text locally, one piece per line, in reading order."""

from functools import cache
from threading import Lock

import cv2
import numpy as np
from numpy.typing import NDArray
from rapidocr_onnxruntime import RapidOCR

from color_engine.models import TextPiece, TextSet6

_MIN_CONFIDENCE = 0.60
_STRAY_SPLIT_MARKS = ":;,.' "
_MAX_WORD_GAP_IN_HEIGHTS = 0.8
_MAX_OVERLAP_IN_HEIGHTS = 0.5
_MAX_LINE_OFFSET_IN_HEIGHTS = 0.5
_engine_lock = Lock()


@cache
def _engine() -> RapidOCR:
    return RapidOCR()


def read_text_6(pixels: NDArray) -> TextSet6:
    bgr = cv2.cvtColor(np.asarray(pixels, dtype=np.uint8), cv2.COLOR_RGB2BGR)
    with _engine_lock:
        lines, _ = _engine()(bgr)
    pieces = [_to_piece(*line) for line in lines or () if _keep(line)]
    return TextSet6(_join_split_lines(pieces))


def _keep(line: tuple) -> bool:
    return float(line[2]) >= _MIN_CONFIDENCE and bool(line[1].strip())


def _to_piece(box: list, text: str, confidence: float) -> TextPiece:
    corners = np.asarray(box, dtype=np.float64)
    left, top = np.floor(corners.min(axis=0))
    right, bottom = np.ceil(corners.max(axis=0))
    return TextPiece(
        text=text.strip(),
        x=int(left),
        y=int(top),
        width=int(right - left),
        height=int(bottom - top),
        confidence=float(confidence),
    )


def _join_split_lines(pieces: list[TextPiece]) -> tuple[TextPiece, ...]:
    """Rejoin a line that the engine split at a word gap, because one piece is one line."""
    joined: list[TextPiece] = []
    for piece in pieces:
        for position, earlier in enumerate(joined):
            if _continues_line(earlier, piece):
                joined[position] = _merge(earlier, piece)
                break
        else:
            joined.append(piece)
    return tuple(joined)


def _continues_line(left: TextPiece, right: TextPiece) -> bool:
    height = max(left.height, right.height)
    gap = right.x - (left.x + left.width)
    offset = abs((left.y + left.height / 2) - (right.y + right.height / 2))
    return (
        -_MAX_OVERLAP_IN_HEIGHTS * height <= gap <= _MAX_WORD_GAP_IN_HEIGHTS * height
        and offset <= _MAX_LINE_OFFSET_IN_HEIGHTS * height
    )


def _merge(left: TextPiece, right: TextPiece) -> TextPiece:
    top = min(left.y, right.y)
    bottom = max(left.y + left.height, right.y + right.height)
    return TextPiece(
        text=f"{left.text} {right.text.lstrip(_STRAY_SPLIT_MARKS)}",
        x=left.x,
        y=top,
        width=right.x + right.width - left.x,
        height=bottom - top,
        confidence=min(left.confidence, right.confidence),
    )
