import numpy as np

from src.models import LinearModel, min_max_normalize
from src.optimization import minimize_continuous


def test_min_max_normalize_scales_to_unit_interval():
    result = min_max_normalize(np.array([2, 4, 6]))

    np.testing.assert_allclose(result, np.array([0.0, 0.5, 1.0]))


def test_linear_model_predicts_with_bias():
    model = LinearModel(weights=np.array([2.0, -1.0]), bias=0.5)

    result = model.predict(np.array([[3.0, 4.0]]))

    np.testing.assert_allclose(result, np.array([2.5]))


def test_continuous_optimizer_finds_bounded_quadratic_minimum():
    result = minimize_continuous(
        lambda values: float((values[0] - 2.0) ** 2),
        np.array([0.0]),
        bounds=[(-1.0, 4.0)],
    )

    assert result.success
    np.testing.assert_allclose(result.x, [2.0], atol=1e-5)
    assert result.objective < 1e-10
