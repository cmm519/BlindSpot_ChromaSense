"""Keep temporary images on the filesystem, one folder per image."""

import json
import re
import shutil
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

import numpy as np
from numpy.typing import NDArray
from PIL import Image

from chromasense.core.models import (
    ColorItem,
    ImageAnalysis,
    ImageRecord,
    ItemSource,
    LegendEntry,
    ShapeItem,
    StoredImage,
    TextItem,
    Verification,
)
from color_engine.models import ImageType, Palette3, PaletteEntry, Region

_IMAGE_ID = re.compile(r"[0-9a-f]{32}")
_ORIGINAL = "original.bin"
_WORKING = "working.png"
_RECORD = "record.json"
_ANALYSIS = "analysis.json"
_TEMPORARY_PREFIX = ".tmp-"


class FilesystemImageStore:
    def __init__(self, data_dir: Path | str) -> None:
        self._images = Path(data_dir) / "images"
        self._images.mkdir(parents=True, exist_ok=True)

    def save(self, record: ImageRecord, original: bytes, working: NDArray) -> None:
        final = self._folder(record.image_id)
        if final is None:
            raise ValueError("image_id has the wrong form")
        temporary = self._images / f"{_TEMPORARY_PREFIX}{uuid4().hex}"
        temporary.mkdir()
        try:
            (temporary / _ORIGINAL).write_bytes(original)
            Image.fromarray(working).save(temporary / _WORKING, format="PNG", compress_level=1)
            (temporary / _RECORD).write_text(json.dumps(_record_to_dict(record)), encoding="utf-8")
            temporary.rename(final)
        except BaseException:
            shutil.rmtree(temporary, ignore_errors=True)
            raise

    def load(self, image_id: str) -> StoredImage | None:
        folder = self._folder(image_id)
        if folder is None or not folder.is_dir():
            return None
        record = _record_from_dict(json.loads((folder / _RECORD).read_text(encoding="utf-8")))
        with Image.open(folder / _WORKING) as image:
            working = np.array(image.convert("RGB"), dtype=np.uint8)
        analysis_path = folder / _ANALYSIS
        analysis = None
        if analysis_path.exists():
            analysis = _analysis_from_dict(json.loads(analysis_path.read_text(encoding="utf-8")))
        return StoredImage(record, (folder / _ORIGINAL).read_bytes(), working, analysis)

    def save_analysis(self, image_id: str, analysis: ImageAnalysis) -> None:
        folder = self._folder(image_id)
        if folder is None or not folder.is_dir():
            raise ValueError("no stored image has this ID")
        temporary = folder / f"{_TEMPORARY_PREFIX}{_ANALYSIS}"
        temporary.write_text(json.dumps(_analysis_to_dict(analysis)), encoding="utf-8")
        temporary.replace(folder / _ANALYSIS)

    def delete_expired(self, now: datetime) -> int:
        deleted = 0
        for folder in self._images.iterdir():
            if not _IMAGE_ID.fullmatch(folder.name):
                continue
            record_path = folder / _RECORD
            record = _record_from_dict(json.loads(record_path.read_text(encoding="utf-8")))
            if record.expires_at <= now:
                shutil.rmtree(folder)
                deleted += 1
        return deleted

    def _folder(self, image_id: str) -> Path | None:
        if not _IMAGE_ID.fullmatch(image_id):
            return None
        return self._images / image_id


def _record_to_dict(record: ImageRecord) -> dict[str, Any]:
    values = asdict(record)
    values["created_at"] = record.created_at.isoformat()
    values["expires_at"] = record.expires_at.isoformat()
    return values


def _record_from_dict(values: dict[str, Any]) -> ImageRecord:
    return ImageRecord(
        image_id=values["image_id"],
        image_hash=values["image_hash"],
        width=values["width"],
        height=values["height"],
        created_at=datetime.fromisoformat(values["created_at"]),
        expires_at=datetime.fromisoformat(values["expires_at"]),
    )


def _item_to_dict(item: Any) -> dict[str, Any]:
    values = asdict(item)
    values["source"] = item.source.value
    values["verification"] = item.verification.value
    return values


def _item_from_dict(item_type: type, values: dict[str, Any]) -> Any:
    return item_type(
        **{
            **values,
            "source": ItemSource(values["source"]),
            "verification": Verification(values["verification"]),
        }
    )


def _color_from_dict(values: dict[str, Any]) -> ColorItem:
    item = _item_from_dict(ColorItem, values)
    return ColorItem(
        **{
            **asdict(item),
            "rgb": tuple(values["rgb"]) if values["rgb"] is not None else None,
            "hsl": tuple(values["hsl"]) if values["hsl"] is not None else None,
            "source": item.source,
            "verification": item.verification,
        }
    )


def _analysis_to_dict(analysis: ImageAnalysis) -> dict[str, Any]:
    return {
        "palette": [asdict(entry) for entry in analysis.palette.entries],
        "regions": [asdict(region) for region in analysis.regions],
        "shapes": [_item_to_dict(item) for item in analysis.shapes],
        "text": [_item_to_dict(item) for item in analysis.text],
        "legend": [_item_to_dict(item) for item in analysis.legend],
        "image_type": analysis.image_type.value,
        "color_items": [_item_to_dict(item) for item in analysis.color_items],
        "summary": analysis.summary,
        "width": analysis.width,
        "height": analysis.height,
    }


def _analysis_from_dict(values: dict[str, Any]) -> ImageAnalysis:
    return ImageAnalysis(
        palette=Palette3(
            tuple(
                PaletteEntry(
                    id=entry["id"],
                    rgb=tuple(entry["rgb"]),
                    lab=tuple(entry["lab"]),
                    share=entry["share"],
                )
                for entry in values["palette"]
            )
        ),
        regions=tuple(Region(**region) for region in values["regions"]),
        shapes=tuple(_item_from_dict(ShapeItem, item) for item in values["shapes"]),
        text=tuple(_item_from_dict(TextItem, item) for item in values["text"]),
        legend=tuple(_item_from_dict(LegendEntry, item) for item in values["legend"]),
        image_type=ImageType(values["image_type"]),
        color_items=tuple(_color_from_dict(item) for item in values["color_items"]),
        summary=values["summary"],
        width=values["width"],
        height=values["height"],
    )
