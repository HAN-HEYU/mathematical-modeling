from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class LinearModel:
    """Minimal linear model helper for early experiments."""

    weights: np.ndarray
    bias: float = 0.0

    def predict(self, x: np.ndarray) -> np.ndarray:
        features = np.asarray(x, dtype=float)
        return features @ self.weights + self.bias


def min_max_normalize(values: np.ndarray) -> np.ndarray:
    array = np.asarray(values, dtype=float)
    minimum = np.nanmin(array)
    maximum = np.nanmax(array)
    if np.isclose(maximum, minimum):
        return np.zeros_like(array, dtype=float)
    return (array - minimum) / (maximum - minimum)
