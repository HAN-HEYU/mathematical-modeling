import numpy as np
import pytest

from src.preprocessing import minmax_normalize, standardize


def test_standardize_operates_column_by_column():
    result = standardize([[1, 10], [2, 20], [3, 30]])
    np.testing.assert_allclose(np.mean(result, axis=0), [0, 0], atol=1e-12)
    np.testing.assert_allclose(np.std(result, axis=0), [1, 1])


def test_standardize_maps_constant_columns_to_zero():
    np.testing.assert_allclose(standardize([[1, 4], [2, 4]]), [[-1, 0], [1, 0]])


def test_minmax_normalize_supports_custom_range():
    result = minmax_normalize([[1, 10], [3, 20]], feature_range=(-1, 1))
    np.testing.assert_allclose(result, [[-1, -1], [1, 1]])


def test_minmax_normalize_maps_constant_slice_to_lower_bound():
    np.testing.assert_allclose(
        minmax_normalize([4, 4, 4], feature_range=(2, 5)),
        [2, 2, 2],
    )


def test_minmax_normalize_rejects_invalid_range():
    with pytest.raises(ValueError, match="lower < upper"):
        minmax_normalize([1, 2], feature_range=(1, 1))
