"""Array preprocessing helpers that preserve the input shape."""

from __future__ import annotations

import math

import numpy as np
from numpy.typing import ArrayLike, NDArray


FloatArray = NDArray[np.float64]


def _as_finite_array(data: ArrayLike) -> FloatArray:
    array = np.asarray(data, dtype=float)
    if array.size == 0:
        raise ValueError("data must not be empty")
    if not np.all(np.isfinite(array)):
        raise ValueError("data must contain only finite values")
    return array


def _validate_axis(axis: int | None, dimensions: int) -> None:
    if axis is None:
        return
    if isinstance(axis, bool) or not isinstance(axis, (int, np.integer)):
        raise TypeError("axis must be an integer or None")
    if not -dimensions <= axis < dimensions:
        raise ValueError("axis is out of bounds for data")


def standardize(
    data: ArrayLike,
    *,
    axis: int | None = 0,
    ddof: int = 0,
) -> FloatArray:
    """Center and scale data to zero mean and unit standard deviation.

    Statistics are computed along ``axis`` and the original shape is retained.
    With the default ``axis=0``, each column is standardized independently.
    Constant slices are mapped to zeros instead of producing NaN values.
    """
    array = _as_finite_array(data)
    _validate_axis(axis, array.ndim)
    if isinstance(ddof, bool) or not isinstance(ddof, (int, np.integer)):
        raise TypeError("ddof must be an integer")
    sample_count = array.size if axis is None else array.shape[axis]
    if ddof < 0 or ddof >= sample_count:
        raise ValueError("ddof must satisfy 0 <= ddof < sample count along axis")

    mean = np.mean(array, axis=axis, keepdims=True)
    deviation = np.std(array, axis=axis, ddof=ddof, keepdims=True)
    safe_deviation = np.where(np.isclose(deviation, 0.0), 1.0, deviation)
    return np.asarray((array - mean) / safe_deviation, dtype=float)


def minmax_normalize(
    data: ArrayLike,
    *,
    feature_range: tuple[float, float] = (0.0, 1.0),
    axis: int | None = 0,
) -> FloatArray:
    """Scale data linearly into ``feature_range`` along a selected axis.

    With the default ``axis=0``, each column is scaled independently. Constant
    slices are mapped to the lower endpoint of ``feature_range``.
    """
    array = _as_finite_array(data)
    _validate_axis(axis, array.ndim)
    lower, upper = map(float, feature_range)
    if not math.isfinite(lower) or not math.isfinite(upper) or lower >= upper:
        raise ValueError("feature_range must contain finite values with lower < upper")

    minimum = np.min(array, axis=axis, keepdims=True)
    maximum = np.max(array, axis=axis, keepdims=True)
    span = maximum - minimum
    safe_span = np.where(np.isclose(span, 0.0), 1.0, span)
    unit_scaled = (array - minimum) / safe_span
    return np.asarray(lower + unit_scaled * (upper - lower), dtype=float)


__all__ = ["minmax_normalize", "standardize"]
