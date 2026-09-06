import matplotlib.pyplot as plt
from PIL import Image

from src.config import FIGURE_SIZE
from src.visualization import (
    plot_fit,
    plot_heatmap,
    plot_line,
    plot_residuals,
    plot_scatter,
    plot_trajectory_2d,
    plot_trajectory_3d,
    save_figure,
)


def test_all_plot_helpers_return_figures():
    figures = [
        plot_line([0, 1], [0, 1])[0],
        plot_scatter([0, 1], [1, 0])[0],
        plot_fit([1, 2], [1.1, 1.9])[0],
        plot_residuals([1, 2], [1.1, 1.9])[0],
        plot_heatmap([[-1, 0], [0, 1]], center=0)[0],
        plot_trajectory_2d([0, 1], [0, 1])[0],
        plot_trajectory_3d([0, 1], [0, 1], [0, 1])[0],
    ]

    assert len(figures) == 7
    for figure in figures:
        plt.close(figure)


def test_save_figure_exports_exact_size_png_and_svg(tmp_path):
    figure, _ = plot_line([0, 1, 2], [0, 1, 4])

    outputs = save_figure(figure, tmp_path / "figure", dpi=300, close=True)

    assert set(outputs) == {"png", "svg"}
    assert all(path.is_file() for path in outputs.values())
    with Image.open(outputs["png"]) as image:
        assert image.size == (round(FIGURE_SIZE[0] * 300), round(FIGURE_SIZE[1] * 300))
