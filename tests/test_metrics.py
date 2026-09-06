import numpy as np
import pytest

from src.metrics import mae, mape, r2, relative_error, rmse


def test_common_metrics_match_hand_calculation():
    actual = [1.0, 2.0, 3.0]
    predicted = [1.0, 2.0, 4.0]

    assert mae(actual, predicted) == pytest.approx(1 / 3)
    assert rmse(actual, predicted) == pytest.approx(np.sqrt(1 / 3))
    assert mape(actual, predicted) == pytest.approx(100 / 9)
    assert r2(actual, predicted) == pytest.approx(0.5)
    np.testing.assert_allclose(relative_error(actual, predicted), [0, 0, 1 / 3])


def test_percentage_errors_make_zero_policy_explicit():
    with pytest.raises(ValueError, match="zero"):
        mape([0, 1], [1, 1])

    assert mape([0, 1], [1, 2], zero_policy="ignore") == pytest.approx(100.0)
    np.testing.assert_allclose(
        relative_error([0, 2], [1, 3], zero_policy="ignore"),
        [np.nan, 0.5],
        equal_nan=True,
    )


def test_r2_rejects_constant_actual_values():
    with pytest.raises(ValueError, match="constant"):
        r2([2, 2], [2, 3])
