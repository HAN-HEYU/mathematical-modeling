from __future__ import annotations

import math
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any

import numpy as np
from scipy.optimize import minimize


Objective = Callable[[np.ndarray], float]


@dataclass(frozen=True)
class RandomSearchResult:
    best_x: np.ndarray
    best_value: float
    evaluations: int


@dataclass(frozen=True)
class ContinuousOptimizationResult:
    """Normalized result from SciPy continuous optimization."""

    x: np.ndarray
    objective: float
    success: bool
    message: str
    iterations: int | None
    evaluations: int | None


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
    if lower_bound.shape != upper_bound.shape or lower_bound.ndim != 1:
        raise ValueError("lower and upper must be one-dimensional with the same shape")
    if lower_bound.size == 0 or not np.all(np.isfinite(lower_bound)) or not np.all(
        np.isfinite(upper_bound)
    ):
        raise ValueError("bounds must be non-empty and finite")
    if np.any(lower_bound > upper_bound):
        raise ValueError("lower must be less than or equal to upper")
    if isinstance(n_iter, bool) or not isinstance(n_iter, (int, np.integer)):
        raise TypeError("n_iter must be an integer")
    if n_iter <= 0:
        raise ValueError("n_iter must be positive")

    rng = np.random.default_rng(seed)
    best_x = lower_bound.copy()
    best_value = float("inf")

    for _ in range(n_iter):
        candidate = rng.uniform(lower_bound, upper_bound)
        value = float(objective(candidate))
        if not math.isfinite(value):
            raise ValueError("objective must return a finite scalar")
        if value < best_value:
            best_x = candidate
            best_value = value

    return RandomSearchResult(best_x=best_x, best_value=best_value, evaluations=n_iter)


def minimize_continuous(
    objective: Objective,
    initial: np.ndarray,
    *,
    bounds: Sequence[tuple[float | None, float | None]] | None = None,
    method: str = "L-BFGS-B",
    maximize: bool = False,
    options: Mapping[str, Any] | None = None,
) -> ContinuousOptimizationResult:
    """Minimize or maximize a bounded continuous scalar objective with SciPy."""
    if not callable(objective):
        raise TypeError("objective must be callable")
    initial_array = np.asarray(initial, dtype=float)
    if initial_array.ndim != 1 or initial_array.size == 0:
        raise ValueError("initial must be a non-empty one-dimensional vector")
    if not np.all(np.isfinite(initial_array)):
        raise ValueError("initial must contain only finite values")
    if bounds is not None and len(bounds) != initial_array.size:
        raise ValueError("bounds length must match initial")
    if bounds is not None:
        for lower, upper in bounds:
            if lower is not None and not math.isfinite(float(lower)):
                raise ValueError("finite lower bounds are required")
            if upper is not None and not math.isfinite(float(upper)):
                raise ValueError("finite upper bounds are required")
            if lower is not None and upper is not None and lower > upper:
                raise ValueError("each lower bound must not exceed its upper bound")

    def wrapped(candidate: np.ndarray) -> float:
        value = float(objective(np.asarray(candidate, dtype=float)))
        if not math.isfinite(value):
            raise ValueError("objective must return a finite scalar")
        return -value if maximize else value

    result = minimize(
        wrapped,
        initial_array,
        method=method,
        bounds=bounds,
        options=dict(options or {}),
    )
    objective_value = float(-result.fun if maximize else result.fun)
    return ContinuousOptimizationResult(
        x=np.asarray(result.x, dtype=float),
        objective=objective_value,
        success=bool(result.success),
        message=str(result.message),
        iterations=int(result.nit) if hasattr(result, "nit") else None,
        evaluations=int(result.nfev) if hasattr(result, "nfev") else None,
    )


__all__ = [
    "ContinuousOptimizationResult",
    "RandomSearchResult",
    "minimize_continuous",
    "random_search",
]
