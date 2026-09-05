from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import numpy as np


Objective = Callable[[np.ndarray], float]


@dataclass
class RandomSearchResult:
    best_x: np.ndarray
    best_value: float
    evaluations: int


def random_search(
    objective: Objective,
    lower: np.ndarray,
    upper: np.ndarray,
    *,
    n_iter: int = 1_000,
    seed: int = 42,
) -> RandomSearchResult:
    """Simple bounded optimizer useful as a baseline before adding PSO/GA."""
    lower_bound = np.asarray(lower, dtype=float)
    upper_bound = np.asarray(upper, dtype=float)
    if lower_bound.shape != upper_bound.shape:
        raise ValueError("lower and upper must have the same shape")
    if np.any(lower_bound > upper_bound):
        raise ValueError("lower must be less than or equal to upper")

    rng = np.random.default_rng(seed)
    best_x = lower_bound.copy()
    best_value = float("inf")

    for _ in range(n_iter):
        candidate = rng.uniform(lower_bound, upper_bound)
        value = float(objective(candidate))
        if value < best_value:
            best_x = candidate
            best_value = value

    return RandomSearchResult(best_x=best_x, best_value=best_value, evaluations=n_iter)
