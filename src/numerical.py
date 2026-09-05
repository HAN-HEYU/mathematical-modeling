"""Small numerical-analysis routines with explicit validation."""

from __future__ import annotations

import math
from collections.abc import Callable
from typing import Literal, overload

import numpy as np
from numpy.typing import ArrayLike, NDArray


FloatArray = NDArray[np.float64]
DifferenceMethod = Literal["central", "forward", "backward"]


def _as_finite_1d(values: ArrayLike, *, name: str) -> FloatArray:
    array = np.asarray(values, dtype=float)
    if array.ndim != 1 or array.size == 0:
        raise ValueError(f"{name} must be a non-empty one-dimensional array")
    if not np.all(np.isfinite(array)):
        raise ValueError(f"{name} must contain only finite values")
    return array


def bisection(
    function: Callable[[float], float],
    lower: float,
    upper: float,
    *,
    tolerance: float = 1e-8,
    max_iterations: int = 100,
) -> float:
    """Find a root of a continuous scalar function by interval bisection.

    Args:
        function: Scalar function whose root is sought.
        lower: Lower endpoint of the initial interval.
        upper: Upper endpoint of the initial interval.
        tolerance: Maximum half-interval width before convergence.
        max_iterations: Positive upper bound on bisection steps.

    Raises:
        ValueError: If inputs are invalid or endpoints do not bracket a root.
        RuntimeError: If convergence is not reached within ``max_iterations``.
    """
    left = float(lower)
    right = float(upper)
    if not math.isfinite(left) or not math.isfinite(right) or left >= right:
        raise ValueError("lower and upper must be finite and satisfy lower < upper")
    if tolerance <= 0.0 or not math.isfinite(tolerance):
        raise ValueError("tolerance must be a positive finite number")
    if max_iterations <= 0:
        raise ValueError("max_iterations must be positive")

    left_value = float(function(left))
    right_value = float(function(right))
    if not math.isfinite(left_value) or not math.isfinite(right_value):
        raise ValueError("function values at interval endpoints must be finite")
    if left_value == 0.0:
        return left
    if right_value == 0.0:
        return right
    if np.signbit(left_value) == np.signbit(right_value):
        raise ValueError("function values at lower and upper must have opposite signs")

    for _ in range(max_iterations):
        midpoint = left + (right - left) / 2.0
        midpoint_value = float(function(midpoint))
        if not math.isfinite(midpoint_value):
            raise ValueError("function returned a non-finite value during bisection")
        if midpoint_value == 0.0 or (right - left) / 2.0 <= tolerance:
            return midpoint
        if np.signbit(left_value) != np.signbit(midpoint_value):
            right = midpoint
        else:
            left = midpoint
            left_value = midpoint_value

    raise RuntimeError("bisection did not converge within max_iterations")


def finite_difference(
    function: Callable[[float], float],
    x: float,
    *,
    step: float = 1e-5,
    method: DifferenceMethod = "central",
) -> float:
    """Approximate the first derivative of a scalar function at ``x``.

    ``method`` may be ``"central"`` (default), ``"forward"``, or
    ``"backward"``. Central differences are usually the most accurate choice
    for smooth functions when both neighboring evaluations are available.
    """
    point = float(x)
    increment = float(step)
    if not math.isfinite(point):
        raise ValueError("x must be finite")
    if not math.isfinite(increment) or increment <= 0.0:
        raise ValueError("step must be a positive finite number")

    if method == "central":
        result = (function(point + increment) - function(point - increment)) / (
            2.0 * increment
        )
    elif method == "forward":
        result = (function(point + increment) - function(point)) / increment
    elif method == "backward":
        result = (function(point) - function(point - increment)) / increment
    else:
        raise ValueError("method must be 'central', 'forward', or 'backward'")

    derivative = float(result)
    if not math.isfinite(derivative):
        raise ValueError("finite-difference evaluations must produce finite values")
    return derivative


def trapezoidal_integral(x: ArrayLike, y: ArrayLike) -> float:
    """Integrate sampled one-dimensional data with the trapezoidal rule.

    ``x`` must contain at least two strictly increasing sample locations, and
    ``y`` must contain one finite function value for each location.
    """
    locations = _as_finite_1d(x, name="x")
    values = _as_finite_1d(y, name="y")
    if locations.size != values.size:
        raise ValueError("x and y must have the same length")
    if locations.size < 2:
        raise ValueError("x and y must contain at least two samples")
    widths = np.diff(locations)
    if np.any(widths <= 0.0):
        raise ValueError("x must be strictly increasing")
    return float(np.sum(widths * (values[:-1] + values[1:]) / 2.0))


def moving_average(values: ArrayLike, window_size: int) -> FloatArray:
    """Return the unweighted moving average over complete windows.

    The output uses ``valid``-window semantics and therefore has length
    ``len(values) - window_size + 1``.
    """
    array = _as_finite_1d(values, name="values")
    if isinstance(window_size, bool) or not isinstance(window_size, (int, np.integer)):
        raise TypeError("window_size must be an integer")
    if window_size <= 0 or window_size > array.size:
        raise ValueError("window_size must be between 1 and len(values)")
    kernel = np.full(int(window_size), 1.0 / window_size, dtype=float)
    return np.convolve(array, kernel, mode="valid")


@overload
def linear_interpolation(
    x: ArrayLike,
    y: ArrayLike,
    x_new: float,
    *,
    extrapolate: bool = False,
) -> float: ...


@overload
def linear_interpolation(
    x: ArrayLike,
    y: ArrayLike,
    x_new: ArrayLike,
    *,
    extrapolate: bool = False,
) -> FloatArray: ...


def linear_interpolation(
    x: ArrayLike,
    y: ArrayLike,
    x_new: float | ArrayLike,
    *,
    extrapolate: bool = False,
) -> float | FloatArray:
    """Linearly interpolate one-dimensional samples at new locations.

    By default, query locations outside the sampled interval raise an error.
    Set ``extrapolate=True`` to extend the first or last line segment. A scalar
    query returns ``float``; an array-like query returns an ndarray.
    """
    locations = _as_finite_1d(x, name="x")
    values = _as_finite_1d(y, name="y")
    if locations.size != values.size:
        raise ValueError("x and y must have the same length")
    if locations.size < 2:
        raise ValueError("x and y must contain at least two samples")
    if np.any(np.diff(locations) <= 0.0):
        raise ValueError("x must be strictly increasing")

    queries = np.asarray(x_new, dtype=float)
    if not np.all(np.isfinite(queries)):
        raise ValueError("x_new must contain only finite values")
    outside = (queries < locations[0]) | (queries > locations[-1])
    if np.any(outside) and not extrapolate:
        raise ValueError("x_new lies outside the interpolation interval")

    result = np.asarray(np.interp(queries, locations, values), dtype=float)
    if extrapolate:
        left_slope = (values[1] - values[0]) / (locations[1] - locations[0])
        right_slope = (values[-1] - values[-2]) / (locations[-1] - locations[-2])
        result = np.where(
            queries < locations[0],
            values[0] + (queries - locations[0]) * left_slope,
            result,
        )
        result = np.where(
            queries > locations[-1],
            values[-1] + (queries - locations[-1]) * right_slope,
            result,
        )

    if queries.ndim == 0:
        return float(result)
    return result


__all__ = [
    "bisection",
    "finite_difference",
    "linear_interpolation",
    "moving_average",
    "trapezoidal_integral",
]
