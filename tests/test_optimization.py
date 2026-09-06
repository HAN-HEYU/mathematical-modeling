import numpy as np
import pytest

from src.optimization import minimize_continuous, random_search


def test_random_search_is_reproducible():
    objective = lambda values: float(np.sum((values - 0.5) ** 2))

    first = random_search(objective, np.zeros(2), np.ones(2), n_iter=50, seed=7)
    second = random_search(objective, np.zeros(2), np.ones(2), n_iter=50, seed=7)

    np.testing.assert_allclose(first.best_x, second.best_x)
    assert first.best_value == second.best_value


def test_random_search_rejects_non_finite_objective():
    with pytest.raises(ValueError, match="finite"):
        random_search(lambda values: float("nan"), np.zeros(1), np.ones(1), n_iter=1)


def test_continuous_optimizer_supports_maximization():
    result = minimize_continuous(
        lambda values: float(-(values[0] - 1.5) ** 2 + 4.0),
        np.array([0.0]),
        bounds=[(-2.0, 3.0)],
        maximize=True,
    )

    assert result.success
    np.testing.assert_allclose(result.x, [1.5], atol=1e-5)
    assert result.objective == pytest.approx(4.0)


def test_continuous_optimizer_validates_bounds():
    with pytest.raises(ValueError, match="lower bound"):
        minimize_continuous(lambda values: float(values[0]), np.array([0.0]), bounds=[(2, 1)])
