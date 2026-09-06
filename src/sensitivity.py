"""One-factor-at-a-time sensitivity analysis helpers."""

from __future__ import annotations

import math
from collections.abc import Callable, Mapping, Sequence
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


ScalarModel = Callable[..., float]


def one_factor_sensitivity(
    model: ScalarModel,
    baseline_parameters: Mapping[str, float],
    *,
    relative_changes: Sequence[float] = (-0.10, -0.05, 0.0, 0.05, 0.10),
    parameters: Sequence[str] | None = None,
) -> pd.DataFrame:
    """Vary one parameter at a time and return a tidy sensitivity table.

    ``relative_changes`` are ratios, so ``0.05`` means a 5% increase. The
    model is called as ``model(**parameters)`` and must return a finite scalar.
    """
    if not callable(model):
        raise TypeError("model must be callable")
    if not baseline_parameters:
        raise ValueError("baseline_parameters must not be empty")

    baseline = {name: float(value) for name, value in baseline_parameters.items()}
    if any(not name for name in baseline):
        raise ValueError("parameter names must be non-empty")
    if any(not math.isfinite(value) for value in baseline.values()):
        raise ValueError("baseline parameters must be finite")

    selected = list(parameters) if parameters is not None else list(baseline)
    if not selected or len(set(selected)) != len(selected):
        raise ValueError("parameters must contain unique names")
    missing = [name for name in selected if name not in baseline]
    if missing:
        raise KeyError(f"unknown parameters: {missing}")
    if any(np.isclose(baseline[name], 0.0) for name in selected):
        raise ValueError("multiplicative sensitivity requires non-zero baselines")

    changes = np.asarray(relative_changes, dtype=float)
    if changes.ndim != 1 or changes.size == 0 or not np.all(np.isfinite(changes)):
        raise ValueError("relative_changes must be a non-empty finite sequence")

    baseline_output = float(model(**baseline))
    if not math.isfinite(baseline_output):
        raise ValueError("model must return a finite scalar")

    rows: list[dict[str, Any]] = []
    for name in selected:
        for change in changes:
            varied = baseline.copy()
            varied[name] = baseline[name] * (1.0 + float(change))
            output = float(model(**varied))
            if not math.isfinite(output):
                raise ValueError(f"model returned a non-finite value for {name}")
            output_change = (
                np.nan
                if np.isclose(baseline_output, 0.0)
                else (output - baseline_output) / baseline_output
            )
            rows.append(
                {
                    "parameter": name,
                    "parameter_change": float(change),
                    "parameter_value": varied[name],
                    "output": output,
                    "output_change": float(output_change),
                    "baseline_output": baseline_output,
                }
            )
    return pd.DataFrame(rows)


def plot_sensitivity(
    results: pd.DataFrame,
    *,
    xlabel: str = "Parameter change (%)",
    ylabel: str = "Output change (%)",
) -> tuple[plt.Figure, plt.Axes]:
    """Plot a tidy table returned by :func:`one_factor_sensitivity`."""
    required = {"parameter", "parameter_change", "output_change"}
    if not required.issubset(results.columns):
        raise ValueError(f"results must contain columns: {sorted(required)}")
    if results.empty:
        raise ValueError("results must not be empty")

    fig, axis = plt.subplots(figsize=(6.3, 3.9), layout="constrained")
    line_styles = ("-", "--", "-.", ":")
    markers = ("o", "s", "^", "D", "v", "P")
    for index, (name, group) in enumerate(results.groupby("parameter", sort=False)):
        ordered = group.sort_values("parameter_change")
        axis.plot(
            ordered["parameter_change"] * 100.0,
            ordered["output_change"] * 100.0,
            label=str(name),
            linestyle=line_styles[index % len(line_styles)],
            marker=markers[index % len(markers)],
            markevery=max(1, len(ordered) // 8),
        )
    axis.axhline(0.0, color="#6B7280", linewidth=0.8)
    axis.axvline(0.0, color="#6B7280", linewidth=0.8)
    axis.set_xlabel(xlabel)
    axis.set_ylabel(ylabel)
    axis.legend(frameon=False)
    return fig, axis


__all__ = ["one_factor_sensitivity", "plot_sensitivity"]
