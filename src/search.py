"""Deterministic exhaustive search over discrete parameter grids."""

from __future__ import annotations

import math
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from itertools import product
from typing import Any


@dataclass(frozen=True)
class GridSearchTrial:
    """One parameter combination and its objective score."""

    parameters: dict[str, Any]
    score: float


@dataclass(frozen=True)
class GridSearchResult:
    """Best grid-search candidate together with every evaluated trial."""

    best_parameters: dict[str, Any]
    best_score: float
    trials: tuple[GridSearchTrial, ...]


def grid_search(
    objective: Callable[..., float],
    parameter_grid: Mapping[str, Iterable[Any]],
    *,
    maximize: bool = False,
) -> GridSearchResult:
    """Evaluate the Cartesian product of a discrete parameter grid.

    Args:
        objective: Function called as ``objective(**parameters)``. It must return
            a finite scalar score.
        parameter_grid: Mapping from parameter names to non-empty candidate
            iterables. Mapping insertion order defines deterministic trial order.
        maximize: Select the largest score when true; otherwise select the
            smallest score.

    Returns:
        A result containing the best candidate and all trials. Score ties retain
        the first parameter combination encountered.
    """
    if not callable(objective):
        raise TypeError("objective must be callable")
    if not isinstance(parameter_grid, Mapping) or not parameter_grid:
        raise ValueError("parameter_grid must be a non-empty mapping")

    names = tuple(parameter_grid.keys())
    if any(not isinstance(name, str) or not name for name in names):
        raise ValueError("parameter names must be non-empty strings")
    candidate_values = tuple(tuple(parameter_grid[name]) for name in names)
    if any(len(values) == 0 for values in candidate_values):
        raise ValueError("every parameter must provide at least one candidate")

    trials: list[GridSearchTrial] = []
    best_trial: GridSearchTrial | None = None
    for combination in product(*candidate_values):
        parameters = dict(zip(names, combination, strict=True))
        score = float(objective(**parameters))
        if not math.isfinite(score):
            raise ValueError("objective must return a finite scalar score")
        trial = GridSearchTrial(parameters=parameters, score=score)
        trials.append(trial)
        if best_trial is None:
            best_trial = trial
        elif maximize and score > best_trial.score:
            best_trial = trial
        elif not maximize and score < best_trial.score:
            best_trial = trial

    if best_trial is None:  # Defensive: non-empty grids always produce a trial.
        raise RuntimeError("parameter grid produced no combinations")
    return GridSearchResult(
        best_parameters=best_trial.parameters.copy(),
        best_score=best_trial.score,
        trials=tuple(trials),
    )


__all__ = ["GridSearchResult", "GridSearchTrial", "grid_search"]
