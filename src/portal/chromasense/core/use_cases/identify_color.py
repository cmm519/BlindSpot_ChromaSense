"""Return the color at a point of the working copy."""

from dataclasses import dataclass

import numpy as np

from chromasense.core.errors import ImageNotFound, InvalidCoordinates
from chromasense.core.ports import ImageStore
from color_engine.models import ColorInfo, CvdProfile, CvdType
from color_engine.rules.naming import ColorNamer
from color_engine.rules.simulation import simulate


@dataclass(frozen=True)
class IdentifyColorRequest:
    image_id: str
    x: int
    y: int
    profile: CvdProfile


@dataclass(frozen=True)
class IdentifyColorResponse:
    color: ColorInfo
    simulated_rgb: tuple[int, int, int] | None
    simulated_hex: str | None


class IdentifyColor:
    def __init__(self, store: ImageStore) -> None:
        self._store = store

    def execute(self, request: IdentifyColorRequest) -> IdentifyColorResponse:
        stored = self._store.load(request.image_id)
        if stored is None:
            raise ImageNotFound(f"No image has the ID {request.image_id}")
        height, width = stored.working.shape[:2]
        if not (0 <= request.x < width and 0 <= request.y < height):
            raise InvalidCoordinates(f"The point must be inside the {width} by {height} image")

        rgb = tuple(int(channel) for channel in stored.working[request.y, request.x])
        color = ColorNamer().describe(rgb)
        if request.profile.type is CvdType.NONE:
            return IdentifyColorResponse(color, None, None)

        pixel = np.array([[rgb]], dtype=np.uint8)
        simulated = tuple(int(channel) for channel in simulate(pixel, request.profile)[0, 0])
        return IdentifyColorResponse(color, simulated, ColorNamer().describe(simulated).hex)
