import numpy as np

from src.models import LinearModel, min_max_normalize


def test_min_max_normalize_scales_to_unit_interval():
    result = min_max_normalize(np.array([2, 4, 6]))

    np.testing.assert_allclose(result, np.array([0.0, 0.5, 1.0]))


def test_linear_model_predicts_with_bias():
    model = LinearModel(weights=np.array([2.0, -1.0]), bias=0.5)

    result = model.predict(np.array([[3.0, 4.0]]))

    np.testing.assert_allclose(result, np.array([2.5]))
