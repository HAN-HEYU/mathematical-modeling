"""Common regression and numerical-error metrics with explicit validation."""

from __future__ import annotations

from typing import Literal

import numpy as np
from numpy.typing import ArrayLike, NDArray


FloatArray = NDArray[np.float64]
ZeroPolicy = Literal["raise", "ignore"]


def _paired_arrays(actual: ArrayLike, predicted: ArrayLike) -> tuple[FloatArray, FloatArray]:
    first = np.asarray(actual, dtype=float)
    second = np.asarray(predicted, dtype=float)
    if first.shape != second.shape or first.size == 0:
        raise ValueError("actual and predicted must have the same non-empty shape")
    if not np.all(np.isfinite(first)) or not np.all(np.isfinite(second)):
        raise ValueError("actual and predicted must contain only finite values")
    return first, second


def rmse(actual: ArrayLike, predicted: ArrayLike) -> float:
    """Return root mean squared error."""
    first, second = _paired_arrays(actual, predicted)
    return float(np.sqrt(np.mean(np.square(second - first))))


def mae(actual: ArrayLike, predicted: ArrayLike) -> float:
    """Return mean absolute error."""
    first, second = _paired_arrays(actual, predicted)
    return float(np.mean(np.abs(second - first)))


def mape(
    actual: ArrayLike,
    predicted: ArrayLike,
    *,
    zero_policy: ZeroPolicy = "raise",
) -> float:
    """Return mean absolute percentage error as a percentage.

    Zero actual values make percentage error undefined. Use
    ``zero_policy='ignore'`` only when excluding them is scientifically valid.
    """
    first, second = _paired_arrays(actual, predicted)
    nonzero = ~np.isclose(first, 0.0)
    if not np.all(nonzero):
        if zero_policy == "raise":
            raise ValueError("MAPE is undefined when actual contains zero")
        if zero_policy != "ignore":
            raise ValueError("zero_policy must be 'raise' or 'ignore'")
        if not np.any(nonzero):
            raise ValueError("MAPE has no non-zero actual values to evaluate")
        first, second = first[nonzero], second[nonzero]
    elif zero_policy not in {"raise", "ignore"}:
        raise ValueError("zero_policy must be 'raise' or 'ignore'")
    return float(np.mean(np.abs((second - first) / first)) * 100.0)


def r2(actual: ArrayLike, predicted: ArrayLike) -> float:
    """Return the coefficient of determination."""
    first, second = _paired_arrays(actual, predicted)
    total = float(np.sum(np.square(first - np.mean(first))))
    if np.isclose(total, 0.0):
        raise ValueError("R2 is undefined for constant actual values")
    residual = float(np.sum(np.square(first - second)))
    return 1.0 - residual / total


def relative_error(
    actual: ArrayLike,
    predicted: ArrayLike,
    *,
    zero_policy: ZeroPolicy = "raise",
) -> FloatArray:
    """Return elementwise absolute relative error as a ratio."""
    first, second = _paired_arrays(actual, predicted)
    nonzero = ~np.isclose(first, 0.0)
    if not np.all(nonzero):
        if zero_policy == "raise":
            raise ValueError("relative error is undefined when actual contains zero")
        if zero_policy != "ignore":
            raise ValueError("zero_policy must be 'raise' or 'ignore'")
        output = np.full(first.shape, np.nan, dtype=float)
        output[nonzero] = np.abs((second[nonzero] - first[nonzero]) / first[nonzero])
        return output
    if zero_policy not in {"raise", "ignore"}:
        raise ValueError("zero_policy must be 'raise' or 'ignore'")
    return np.asarray(np.abs((second - first) / first), dtype=float)


__all__ = ["mae", "mape", "r2", "relative_error", "rmse"]
