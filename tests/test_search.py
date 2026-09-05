import pytest

from src.search import grid_search


def test_grid_search_minimizes_over_cartesian_product():
    result = grid_search(
        lambda x, y: (x - 2) ** 2 + (y + 1) ** 2,
        {"x": [0, 1, 2], "y": [-1, 0]},
    )

    assert result.best_parameters == {"x": 2, "y": -1}
    assert result.best_score == pytest.approx(0.0)
    assert len(result.trials) == 6


def test_grid_search_can_maximize():
    result = grid_search(lambda value: value, {"value": [1, 3, 2]}, maximize=True)
    assert result.best_parameters == {"value": 3}
    assert result.best_score == pytest.approx(3.0)


def test_grid_search_rejects_empty_candidate_list():
    with pytest.raises(ValueError, match="at least one candidate"):
        grid_search(lambda value: value, {"value": []})


def test_grid_search_rejects_non_finite_score():
    with pytest.raises(ValueError, match="finite"):
        grid_search(lambda value: float("nan"), {"value": [1]})
