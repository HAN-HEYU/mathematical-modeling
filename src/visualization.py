"""Reusable, publication-oriented plotting helpers for modeling reports."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from numpy.typing import ArrayLike

from .config import FIGURE_DPI, FIGURE_SIZE
from .utils import ensure_dir

try:
    from utils.plot_style import COLOR_SEQUENCE, apply_publication_style
except ImportError:  # pragma: no cover - only for unusual package installations
    COLOR_SEQUENCE = (
        "#0072B2",
        "#E69F00",
        "#009E73",
        "#D55E00",
        "#CC79A7",
        "#56B4E9",
    )

    def apply_publication_style(language: str = "zh", width: str = "report") -> dict:
        del language, width
        plt.rcParams.update({"axes.grid": False, "axes.unicode_minus": False})
        return {"font": "DejaVu Sans", "size_inches": FIGURE_SIZE}


def set_default_style(*, language: str = "zh") -> dict[str, Any]:
    """Apply a restrained, colorblind-safe report style and return its details."""
    return apply_publication_style(language=language, width="report")


def _paired_1d(x: ArrayLike, y: ArrayLike) -> tuple[np.ndarray, np.ndarray]:
    x_values = np.asarray(x, dtype=float)
    y_values = np.asarray(y, dtype=float)
    if x_values.ndim != 1 or y_values.ndim != 1 or x_values.size == 0:
        raise ValueError("x and y must be non-empty one-dimensional arrays")
    if x_values.shape != y_values.shape:
        raise ValueError("x and y must have the same shape")
    if not np.all(np.isfinite(x_values)) or not np.all(np.isfinite(y_values)):
        raise ValueError("x and y must contain only finite values")
    return x_values, y_values


def _labels(axis: Axes, *, xlabel: str, ylabel: str, title: str | None) -> None:
    axis.set_xlabel(xlabel)
    axis.set_ylabel(ylabel)
    if title:
        axis.set_title(title)


def save_figure(
    figure: Figure,
    path: str | Path,
    *,
    formats: Sequence[str] = ("png", "svg"),
    dpi: int = FIGURE_DPI,
    tight: bool = False,
    close: bool = False,
) -> dict[str, Path]:
    """Save a figure in one or more formats without changing final size by default.

    If ``path`` has a suffix, that suffix is the only output format. Otherwise
    ``formats`` are appended. Set ``tight=True`` only when exact physical size
    is not part of the figure contract.
    """
    if dpi < 300:
        raise ValueError("dpi must be at least 300 for report figures")
    target = Path(path)
    if target.suffix:
        requested = (target.suffix.lstrip(".").lower(),)
        stem = target.with_suffix("")
    else:
        requested = tuple(item.lower().lstrip(".") for item in formats)
        stem = target
    if not requested or any(item not in {"png", "svg", "pdf"} for item in requested):
        raise ValueError("formats must contain only png, svg, or pdf")

    ensure_dir(stem.parent)
    figure.set_layout_engine("constrained")
    outputs: dict[str, Path] = {}
    for format_name in requested:
        output = stem.with_suffix(f".{format_name}")
        save_kwargs: dict[str, Any] = {"bbox_inches": "tight" if tight else None}
        if format_name == "png":
            save_kwargs["dpi"] = dpi
        figure.savefig(output, **save_kwargs)
        outputs[format_name] = output
    if close:
        plt.close(figure)
    return outputs


def save_current_figure(path: str | Path, *, dpi: int = FIGURE_DPI) -> Path:
    """Backward-compatible wrapper that saves Matplotlib's current figure."""
    output = save_figure(plt.gcf(), path, dpi=dpi)
    return next(iter(output.values()))


def plot_line(
    x: ArrayLike,
    y: ArrayLike,
    *,
    xlabel: str = "x",
    ylabel: str = "y",
    label: str | None = None,
    title: str | None = None,
) -> tuple[Figure, Axes]:
    """Plot a continuous sequence as a line with sparse redundant markers."""
    x_values, y_values = _paired_1d(x, y)
    figure, axis = plt.subplots(figsize=FIGURE_SIZE, layout="constrained")
    marker = "o" if len(x_values) <= 25 else None
    axis.plot(
        x_values,
        y_values,
        label=label,
        color=COLOR_SEQUENCE[0],
        marker=marker,
        markevery=max(1, len(x_values) // 12) if marker else None,
    )
    _labels(axis, xlabel=xlabel, ylabel=ylabel, title=title)
    if label:
        axis.legend(frameon=False)
    return figure, axis


def plot_scatter(
    x: ArrayLike,
    y: ArrayLike,
    *,
    xlabel: str = "x",
    ylabel: str = "y",
    label: str | None = None,
    title: str | None = None,
) -> tuple[Figure, Axes]:
    """Plot a two-variable relationship with readable point edges."""
    x_values, y_values = _paired_1d(x, y)
    figure, axis = plt.subplots(figsize=FIGURE_SIZE, layout="constrained")
    axis.scatter(
        x_values,
        y_values,
        label=label,
        color=COLOR_SEQUENCE[0],
        edgecolor="black",
        linewidth=0.3,
        alpha=0.8 if len(x_values) <= 1000 else 0.25,
    )
    _labels(axis, xlabel=xlabel, ylabel=ylabel, title=title)
    if label:
        axis.legend(frameon=False)
    return figure, axis


def plot_fit(
    actual: ArrayLike,
    predicted: ArrayLike,
    *,
    unit: str = "",
    title: str | None = None,
) -> tuple[Figure, Axes]:
    """Compare observed and predicted values against the one-to-one line."""
    actual_values, predicted_values = _paired_1d(actual, predicted)
    figure, axis = plot_scatter(
        actual_values,
        predicted_values,
        xlabel=f"Observed{f' ({unit})' if unit else ''}",
        ylabel=f"Predicted{f' ({unit})' if unit else ''}",
        title=title,
    )
    lower = float(min(actual_values.min(), predicted_values.min()))
    upper = float(max(actual_values.max(), predicted_values.max()))
    axis.plot([lower, upper], [lower, upper], "--", color=COLOR_SEQUENCE[3], label="1:1")
    axis.legend(frameon=False)
    axis.set_aspect("equal", adjustable="box")
    return figure, axis


def plot_residuals(
    actual: ArrayLike,
    predicted: ArrayLike,
    *,
    xlabel: str = "Predicted",
    ylabel: str = "Residual (observed - predicted)",
) -> tuple[Figure, Axes]:
    """Plot residuals against predictions for model diagnostics."""
    actual_values, predicted_values = _paired_1d(actual, predicted)
    figure, axis = plot_scatter(
        predicted_values,
        actual_values - predicted_values,
        xlabel=xlabel,
        ylabel=ylabel,
    )
    axis.axhline(0.0, color=COLOR_SEQUENCE[3], linestyle="--", linewidth=0.9)
    return figure, axis


def plot_heatmap(
    matrix: ArrayLike,
    *,
    xlabels: Iterable[str] | None = None,
    ylabels: Iterable[str] | None = None,
    colorbar_label: str = "Value",
    center: float | None = None,
    annotate: bool | None = None,
) -> tuple[Figure, Axes]:
    """Plot a matrix with a perceptually uniform or zero-centered color map."""
    values = np.asarray(matrix, dtype=float)
    if values.ndim != 2 or values.size == 0 or not np.all(np.isfinite(values)):
        raise ValueError("matrix must be a non-empty finite two-dimensional array")
    figure, axis = plt.subplots(figsize=FIGURE_SIZE, layout="constrained")
    kwargs: dict[str, Any] = {"cmap": "viridis", "aspect": "auto"}
    if center is not None:
        from matplotlib.colors import TwoSlopeNorm

        minimum, maximum = float(values.min()), float(values.max())
        if not minimum < center < maximum:
            raise ValueError("center must lie strictly inside the data range")
        kwargs.update(cmap="RdBu_r", norm=TwoSlopeNorm(center, minimum, maximum))
    image = axis.imshow(values, **kwargs)
    colorbar = figure.colorbar(image, ax=axis)
    colorbar.set_label(colorbar_label)
    if xlabels is not None:
        labels = list(xlabels)
        if len(labels) != values.shape[1]:
            raise ValueError("xlabels length must match matrix columns")
        axis.set_xticks(np.arange(values.shape[1]), labels)
    if ylabels is not None:
        labels = list(ylabels)
        if len(labels) != values.shape[0]:
            raise ValueError("ylabels length must match matrix rows")
        axis.set_yticks(np.arange(values.shape[0]), labels)
    should_annotate = values.size <= 25 if annotate is None else annotate
    if should_annotate:
        threshold = float((values.min() + values.max()) / 2.0)
        for row in range(values.shape[0]):
            for column in range(values.shape[1]):
                color = "white" if values[row, column] < threshold else "#222222"
                axis.text(
                    column,
                    row,
                    f"{values[row, column]:.3g}",
                    ha="center",
                    va="center",
                    color=color,
                )
    return figure, axis


def plot_trajectory_2d(
    x: ArrayLike,
    y: ArrayLike,
    *,
    xlabel: str = "x",
    ylabel: str = "y",
    unit: str = "",
) -> tuple[Figure, Axes]:
    """Plot a planar trajectory with distinct start and end points."""
    figure, axis = plot_line(
        x,
        y,
        xlabel=f"{xlabel}{f' ({unit})' if unit else ''}",
        ylabel=f"{ylabel}{f' ({unit})' if unit else ''}",
    )
    x_values, y_values = _paired_1d(x, y)
    axis.scatter(x_values[0], y_values[0], color=COLOR_SEQUENCE[2], marker="o", label="Start")
    axis.scatter(x_values[-1], y_values[-1], color=COLOR_SEQUENCE[3], marker="X", label="End")
    axis.legend(frameon=False)
    axis.set_aspect("equal", adjustable="datalim")
    return figure, axis


def plot_trajectory_3d(
    x: ArrayLike,
    y: ArrayLike,
    z: ArrayLike,
    *,
    labels: tuple[str, str, str] = ("x", "y", "z"),
    unit: str = "",
) -> tuple[Figure, Axes]:
    """Plot a physical three-dimensional trajectory."""
    x_values, y_values = _paired_1d(x, y)
    z_values = np.asarray(z, dtype=float)
    if z_values.ndim != 1 or z_values.shape != x_values.shape or not np.all(
        np.isfinite(z_values)
    ):
        raise ValueError("z must be finite and have the same one-dimensional shape")
    figure = plt.figure(figsize=FIGURE_SIZE, layout="constrained")
    axis = figure.add_subplot(111, projection="3d")
    axis.plot(x_values, y_values, z_values, color=COLOR_SEQUENCE[0])
    axis.scatter(x_values[0], y_values[0], z_values[0], color=COLOR_SEQUENCE[2], label="Start")
    axis.scatter(
        x_values[-1], y_values[-1], z_values[-1],
        color=COLOR_SEQUENCE[3], marker="X", label="End"
    )
    suffix = f" ({unit})" if unit else ""
    axis.set_xlabel(labels[0] + suffix)
    axis.set_ylabel(labels[1] + suffix)
    axis.set_zlabel(labels[2] + suffix)
    axis.legend(frameon=False)
    return figure, axis


__all__ = [
    "plot_fit",
    "plot_heatmap",
    "plot_line",
    "plot_residuals",
    "plot_scatter",
    "plot_trajectory_2d",
    "plot_trajectory_3d",
    "save_current_figure",
    "save_figure",
    "set_default_style",
]
