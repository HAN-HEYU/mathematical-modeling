"""Descriptive statistics helpers for one-dimensional numeric samples."""

from __future__ import annotations

import math

import numpy as np
from numpy.typing import ArrayLike, NDArray


FloatArray = NDArray[np.float64]


def _as_sample(values: ArrayLike, *, name: str = "values") -> FloatArray:
    sample = np.asarray(values, dtype=float)
    if sample.ndim != 1 or sample.size == 0:
        raise ValueError(f"{name} must be a non-empty one-dimensional sample")
    if not np.all(np.isfinite(sample)):
        raise ValueError(f"{name} must contain only finite values")
    return sample


def _validate_ddof(ddof: int, sample_size: int) -> None:
    if isinstance(ddof, bool) or not isinstance(ddof, (int, np.integer)):
        raise TypeError("ddof must be an integer")
    if ddof < 0 or ddof >= sample_size:
        raise ValueError("ddof must satisfy 0 <= ddof < sample size")


def z_score(values: ArrayLike, *, ddof: int = 0) -> FloatArray:
    """Return z-scores for a finite one-dimensional sample.

    A constant sample is mapped to zeros. ``ddof=0`` uses the population
    standard deviation; use ``ddof=1`` for the sample standard deviation.
    """
    sample = _as_sample(values)
    _validate_ddof(ddof, sample.size)
    standard_deviation = float(np.std(sample, ddof=ddof))
    if np.isclose(standard_deviation, 0.0):
        return np.zeros_like(sample, dtype=float)
    return (sample - np.mean(sample)) / standard_deviation


def coefficient_of_variation(values: ArrayLike, *, ddof: int = 1) -> float:
    """Return standard deviation divided by the absolute arithmetic mean.

    The result is a non-negative ratio, not a percentage. The coefficient is
    undefined for samples whose mean is numerically zero.
    """
    sample = _as_sample(values)
    _validate_ddof(ddof, sample.size)
    mean = float(np.mean(sample))
    if np.isclose(mean, 0.0):
        raise ValueError("coefficient of variation is undefined for a zero mean")
    return float(np.std(sample, ddof=ddof) / abs(mean))


def pearson_corr(x: ArrayLike, y: ArrayLike) -> float:
    """Return the Pearson product-moment correlation of two samples.

    Both samples must have equal length, contain at least two observations,
    and have non-zero variance.
    """
    first = _as_sample(x, name="x")
    second = _as_sample(y, name="y")
    if first.size != second.size:
        raise ValueError("x and y must have the same length")
    if first.size < 2:
        raise ValueError("x and y must contain at least two observations")
    if np.isclose(np.std(first), 0.0) or np.isclose(np.std(second), 0.0):
        raise ValueError("Pearson correlation is undefined for a constant sample")
    correlation = float(np.corrcoef(first, second)[0, 1])
    return float(np.clip(correlation, -1.0, 1.0))


def iqr_bounds(values: ArrayLike, *, multiplier: float = 1.5) -> tuple[float, float]:
    """Return Tukey lower and upper outlier fences for a numeric sample.

    The fences are ``Q1 - multiplier * IQR`` and
    ``Q3 + multiplier * IQR``. The common Tukey value is 1.5.
    """
    sample = _as_sample(values)
    factor = float(multiplier)
    if not math.isfinite(factor) or factor < 0.0:
        raise ValueError("multiplier must be a finite non-negative number")
    first_quartile, third_quartile = np.percentile(sample, [25.0, 75.0])
    interquartile_range = third_quartile - first_quartile
    lower = first_quartile - factor * interquartile_range
    upper = third_quartile + factor * interquartile_range
    return float(lower), float(upper)


__all__ = [
    "coefficient_of_variation",
    "iqr_bounds",
    "pearson_corr",
    "z_score",
]
