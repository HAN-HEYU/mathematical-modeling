import matplotlib.pyplot as plt
import numpy as np

from src.sensitivity import one_factor_sensitivity, plot_sensitivity


def test_one_factor_sensitivity_varies_only_one_parameter():
    result = one_factor_sensitivity(
        lambda a, b: 2 * a + b,
        {"a": 10.0, "b": 5.0},
        relative_changes=(-0.1, 0.0, 0.1),
    )

    assert len(result) == 6
    assert set(result["parameter"]) == {"a", "b"}
    baseline_rows = result[np.isclose(result["parameter_change"], 0.0)]
    assert np.allclose(baseline_rows["output"], 25.0)
    assert np.allclose(baseline_rows["output_change"], 0.0)


def test_plot_sensitivity_returns_labeled_axes():
    result = one_factor_sensitivity(lambda a: a**2, {"a": 2.0})

    figure, axis = plot_sensitivity(result)

    assert axis.get_xlabel() == "Parameter change (%)"
    assert len(axis.lines) >= 3
    plt.close(figure)
