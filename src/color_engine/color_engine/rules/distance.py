"""CIEDE2000 color difference."""

import numpy as np
from numpy.typing import NDArray
from skimage.color import deltaE_ciede2000


def ciede2000(lab_a: NDArray, lab_b: NDArray) -> NDArray[np.float64]:
    """Return the CIEDE2000 distance between CIELAB arrays whose last axis holds L, a, and b.

    The two arrays only need shapes that broadcast, so one color can be compared with many.
    """
    first, second = np.broadcast_arrays(
        np.asarray(lab_a, dtype=np.float64), np.asarray(lab_b, dtype=np.float64)
    )
    return np.asarray(deltaE_ciede2000(first, second))
