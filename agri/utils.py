from __future__ import annotations

from typing import Tuple

import numpy as np


def normalize_array(arr: np.ndarray) -> np.ndarray:
    arr = arr.astype("float32")
    min_v = float(arr.min())
    max_v = float(arr.max())
    if max_v - min_v < 1e-6:
        return np.zeros_like(arr)
    return (arr - min_v) / (max_v - min_v)


