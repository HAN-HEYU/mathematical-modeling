"""Project-wide paths and numerical defaults.

Keep competition-specific parameters in this module (or in a small module that
imports it) so experiments do not hide constants inside model code.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
EXTERNAL_DATA_DIR = DATA_DIR / "external"
RESULTS_DIR = PROJECT_ROOT / "results"
FIGURES_DIR = PROJECT_ROOT / "figures"
LOGS_DIR = RESULTS_DIR / "logs"

RANDOM_SEED = 42
DT = 0.01
TOL = 1e-6
MAX_ITER = 10_000
FIGURE_DPI = 300
FIGURE_SIZE = (6.3, 3.9)


@dataclass(frozen=True)
class RuntimeConfig:
    """Common runtime settings that should be recorded with every experiment."""

    random_seed: int = RANDOM_SEED
    tolerance: float = TOL
    max_iterations: int = MAX_ITER
    figure_dpi: int = FIGURE_DPI

    def __post_init__(self) -> None:
        if self.random_seed < 0:
            raise ValueError("random_seed must be non-negative")
        if self.tolerance <= 0:
            raise ValueError("tolerance must be positive")
        if self.max_iterations <= 0:
            raise ValueError("max_iterations must be positive")
        if self.figure_dpi < 300:
            raise ValueError("figure_dpi must be at least 300")


DEFAULT_CONFIG = RuntimeConfig()


__all__ = [
    "DATA_DIR",
    "DEFAULT_CONFIG",
    "DT",
    "EXTERNAL_DATA_DIR",
    "FIGURES_DIR",
    "FIGURE_DPI",
    "FIGURE_SIZE",
    "LOGS_DIR",
    "MAX_ITER",
    "PROCESSED_DATA_DIR",
    "PROJECT_ROOT",
    "RANDOM_SEED",
    "RAW_DATA_DIR",
    "RESULTS_DIR",
    "RuntimeConfig",
    "TOL",
]
