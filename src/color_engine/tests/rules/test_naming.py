import csv
import socket
from importlib import resources

import pytest

from color_engine.models import ColorInfo, CvdProfile, CvdType
from color_engine.rules.naming import ColorNamer

FAMILIES = {
    "red",
    "orange",
    "yellow",
    "green",
    "blue",
    "purple",
    "pink",
    "brown",
    "black",
    "white",
    "gray",
}


def _rows():
    source = resources.files("color_engine").joinpath("data/named_colors.csv")
    with source.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _rgb(hex_value):
    return tuple(int(hex_value[i : i + 2], 16) for i in (1, 3, 5))


def test_every_dataset_color_returns_its_own_name_with_no_network(monkeypatch):
    def refuse(*args, **kwargs):
        raise AssertionError("naming must not open a network connection")

    monkeypatch.setattr(socket.socket, "connect", refuse)
    namer = ColorNamer()
    for row in _rows():
        assert namer.describe(_rgb(row["hex"])).name == row["name"]


def test_dataset_has_merged_duplicates_and_known_families():
    rows = _rows()
    hex_values = [row["hex"] for row in rows]
    names = {row["name"] for row in rows}
    assert len(hex_values) == len(set(hex_values))
    assert {"cyan", "magenta", "gray"} <= names
    assert not {"aqua", "fuchsia", "grey"} & names
    assert {row["family"] for row in rows} == FAMILIES


@pytest.mark.parametrize(
    ("rgb", "expected"),
    [
        ((255, 0, 0), ColorInfo("red", "#FF0000", (255, 0, 0), (0, 100, 50), "red")),
        ((0, 128, 0), ColorInfo("green", "#008000", (0, 128, 0), (120, 100, 25), "green")),
        ((128, 128, 128), ColorInfo("gray", "#808080", (128, 128, 128), (0, 0, 50), "gray")),
        ((255, 255, 255), ColorInfo("white", "#FFFFFF", (255, 255, 255), (0, 0, 100), "white")),
        ((0, 0, 0), ColorInfo("black", "#000000", (0, 0, 0), (0, 0, 0), "black")),
    ],
)
def test_describe_returns_correct_values(rgb, expected):
    assert ColorNamer().describe(rgb) == expected


def test_nearby_color_takes_the_nearest_name_and_keeps_its_own_values():
    info = ColorNamer().describe((254, 1, 2))
    assert (info.name, info.family) == ("red", "red")
    assert (info.hex, info.rgb) == ("#FE0102", (254, 1, 2))


def test_hue_near_360_wraps_to_zero():
    assert ColorNamer().describe((255, 0, 1)).hsl[0] == 0


@pytest.mark.parametrize("rgb", [(256, 0, 0), (0, -1, 0)])
def test_out_of_range_channel_is_rejected(rgb):
    with pytest.raises(ValueError):
        ColorNamer().describe(rgb)


@pytest.mark.parametrize("severity", [-0.1, 1.1])
def test_profile_rejects_out_of_range_severity(severity):
    with pytest.raises(ValueError):
        CvdProfile(CvdType.DEUTAN, severity)
