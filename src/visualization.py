from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt

from .utils import ensure_dir


def save_current_figure(path: str | Path, *, dpi: int = 300) -> Path:
    output_path = Path(path)
    ensure_dir(output_path.parent)
    plt.tight_layout()
    plt.savefig(output_path, dpi=dpi, bbox_inches="tight")
    return output_path


def set_default_style() -> None:
    plt.rcParams.update(
        {
            "figure.dpi": 120,
            "savefig.dpi": 300,
            "axes.grid": True,
            "grid.alpha": 0.25,
            "font.size": 10,
        }
    )
