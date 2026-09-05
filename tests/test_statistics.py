import numpy as np
import pytest

from src.statistics import coefficient_of_variation, iqr_bounds, pearson_corr, z_score


def test_z_score_has_zero_mean_and_unit_population_deviation():
    result = z_score([1, 2, 3])
    assert np.mean(result) == pytest.approx(0.0)
    assert np.std(result) == pytest.approx(1.0)


def test_z_score_maps_constant_sample_to_zero():
    np.testing.assert_allclose(z_score([4, 4, 4]), [0, 0, 0])


def test_coefficient_of_variation_is_non_negative_ratio():
    assert coefficient_of_variation([1, 2, 3], ddof=0) == pytest.approx(
        np.std([1, 2, 3]) / 2.0
    )


def test_coefficient_of_variation_rejects_zero_mean():
    with pytest.raises(ValueError, match="zero mean"):
        coefficient_of_variation([-1, 0, 1])


def test_pearson_corr_detects_perfect_inverse_relation():
    assert pearson_corr([1, 2, 3], [6, 4, 2]) == pytest.approx(-1.0)


def test_pearson_corr_rejects_constant_sample():
    with pytest.raises(ValueError, match="constant"):
        pearson_corr([1, 1, 1], [1, 2, 3])


def test_iqr_bounds_uses_tukey_fences():
    lower, upper = iqr_bounds([0, 1, 2, 3, 4])
    assert lower == pytest.approx(-2.0)
    assert upper == pytest.approx(6.0)
