import importlib
import json
import socket
from pathlib import Path

import numpy as np
import pytest
from PIL import Image, ImageDraw, ImageFont

from color_engine.models import TextPiece, TextSet6
from color_engine.pipeline.filter_6_text.read_text_6 import read_text_6

filter_module = importlib.import_module("color_engine.pipeline.filter_6_text.read_text_6")
LABELED = Path(__file__).parent.parent / "data" / "labeled"
LINES = [("Annual Report", 40, 30), ("Revenue by Region", 40, 110), ("Prepared in March", 40, 190)]


def _known_graphic(ink=(0, 0, 0), paper=(255, 255, 255)) -> np.ndarray:
    image = Image.new("RGB", (640, 260), paper)
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default(size=36)
    for text, x, y in LINES:
        draw.text((x, y), text, font=font, fill=ink)
    return np.array(image)


def _normalize(text: str) -> str:
    return " ".join(text.casefold().split())


def test_lists_each_piece_of_text_with_location_in_reading_order_with_no_network(monkeypatch):
    def refuse(*args, **kwargs):
        raise AssertionError("text recognition must not open a network connection")

    monkeypatch.setattr(socket.socket, "connect", refuse)
    result = read_text_6(_known_graphic())

    assert isinstance(result, TextSet6)
    assert [_normalize(piece.text) for piece in result.items] == [
        _normalize(line[0]) for line in LINES
    ]
    for piece, (_, x, y) in zip(result.items, LINES, strict=True):
        assert isinstance(piece, TextPiece)
        assert piece.x == pytest.approx(x, abs=12)
        assert piece.y == pytest.approx(y, abs=14)
        assert piece.width > 100
        assert 15 < piece.height < 70
        assert 0.6 <= piece.confidence <= 1.0


def test_colored_text_on_a_colored_background_is_read():
    result = read_text_6(_known_graphic(ink=(255, 255, 255), paper=(30, 90, 170)))
    read = [_normalize(piece.text) for piece in result.items]
    assert len(read) == len(LINES)
    assert read[0] == "annual report"
    assert read[1].startswith("revenue by") and read[1].endswith("region")
    assert read[2] == "prepared in march"


def test_image_with_no_text_returns_an_empty_result():
    assert read_text_6(np.full((200, 200, 3), 240, dtype=np.uint8)).items == ()


def test_low_confidence_lines_are_dropped(monkeypatch):
    box = [[1, 2], [50, 2], [50, 20], [1, 20]]
    answer = [[box, "keep", 0.9], [box, "drop", 0.4], [box, "  ", 0.9]]
    monkeypatch.setattr(filter_module, "_engine", lambda: lambda image: (answer, None))
    items = read_text_6(np.zeros((30, 60, 3), dtype=np.uint8)).items
    assert [piece.text for piece in items] == ["keep"]
    assert (items[0].x, items[0].y, items[0].width, items[0].height) == (1, 2, 49, 18)


def test_line_split_at_a_word_gap_is_rejoined_and_distant_labels_stay_separate(monkeypatch):
    def box(left, right):
        return [[left, 10], [right, 10], [right, 30], [left, 30]]

    answer = [
        [box(0, 60), "Revenue", 0.9],
        [box(70, 150), "by Region", 0.8],
        [box(300, 330), "Q1", 0.9],
    ]
    monkeypatch.setattr(filter_module, "_engine", lambda: lambda image: (answer, None))
    items = read_text_6(np.zeros((40, 400, 3), dtype=np.uint8)).items
    assert [piece.text for piece in items] == ["Revenue by Region", "Q1"]
    assert (items[0].x, items[0].width, items[0].confidence) == (0, 150, 0.8)


def test_overlapping_split_pieces_join_and_lose_a_stray_mark_at_the_split(monkeypatch):
    def box(left, right):
        return [[left, 10], [right, 10], [right, 40], [left, 40]]

    answer = [[box(44, 187), "Revenue", 1.0], [box(182, 358), ": by Region", 0.92]]
    monkeypatch.setattr(filter_module, "_engine", lambda: lambda image: (answer, None))
    items = read_text_6(np.zeros((50, 400, 3), dtype=np.uint8)).items
    assert [piece.text for piece in items] == ["Revenue by Region"]


def test_missing_engine_raises_and_does_not_return_an_empty_result(monkeypatch):
    def missing():
        raise FileNotFoundError("engine model is missing")

    monkeypatch.setattr(filter_module, "_engine", missing)
    with pytest.raises(FileNotFoundError):
        read_text_6(np.zeros((30, 60, 3), dtype=np.uint8))


def test_local_text_is_at_least_80_percent_correct_on_the_labeled_set():
    labels = json.loads((LABELED / "labels.json").read_text())["images"]
    expected = found = 0
    for label in labels:
        if not label["text"]:
            continue
        pixels = np.array(Image.open(LABELED / label["file"]).convert("RGB"))
        pool = [_normalize(piece.text) for piece in read_text_6(pixels).items]
        for text in map(_normalize, label["text"]):
            expected += 1
            if text in pool:
                found += 1
                pool.remove(text)
    assert expected >= 50
    assert found / expected >= 0.80
