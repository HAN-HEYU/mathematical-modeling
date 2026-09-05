import numpy as np
import pytest

from src.numerical import (
    bisection,
    finite_difference,
    linear_interpolation,
    moving_average,
    trapezoidal_integral,
)


def test_bisection_finds_square_root():
    root = bisection(lambda value: value**2 - 2.0, 1.0, 2.0)
    assert root == pytest.approx(np.sqrt(2.0), abs=1e-8)


def test_bisection_requires_bracketed_root():
    with pytest.raises(ValueError, match="opposite signs"):
        bisection(lambda value: value**2 + 1.0, -1.0, 1.0)


@pytest.mark.parametrize("method", ["central", "forward", "backward"])
def test_finite_difference_approximates_derivative(method):
    derivative = finite_difference(lambda value: value**2, 3.0, method=method)
    assert derivative == pytest.approx(6.0, rel=1e-4)


def test_trapezoidal_integral_for_linear_samples():
    assert trapezoidal_integral([0, 1, 2], [0, 1, 2]) == pytest.approx(2.0)


def test_trapezoidal_integral_requires_increasing_locations():
    with pytest.raises(ValueError, match="strictly increasing"):
        trapezoidal_integral([0, 2, 1], [0, 2, 1])


def test_moving_average_uses_complete_windows():
    np.testing.assert_allclose(moving_average([1, 2, 3, 4], 2), [1.5, 2.5, 3.5])


def test_linear_interpolation_supports_arrays_and_extrapolation():
    np.testing.assert_allclose(
        linear_interpolation([0, 1, 2], [0, 2, 4], [0.5, 1.5]),
        [1.0, 3.0],
    )
    assert linear_interpolation(
        [0, 1, 2], [0, 2, 4], 3.0, extrapolate=True
    ) == pytest.approx(6.0)


def test_linear_interpolation_rejects_unrequested_extrapolation():
    with pytest.raises(ValueError, match="outside"):
        linear_interpolation([0, 1], [0, 2], 2.0)
