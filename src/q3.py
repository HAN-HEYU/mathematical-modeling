from __future__ import annotations

from pathlib import Path
from typing import Any

from .config import FIGURES_DIR, RESULTS_DIR
from .logging_utils import question_logger
from .utils import ensure_dir, save_json

QUESTION = "q3"

def load_inputs() -> dict[str, Any]:
    """Load and validate Q3 attachments."""
    return {}

def build_model(inputs: dict[str, Any]) -> Any:
    """Build the Q3 model."""
    del inputs
    return None

def solve(model: Any, inputs: dict[str, Any]) -> dict[str, Any]:
    """Solve Q3 and return serializable result data."""
    del model, inputs
    return {"question": QUESTION, "status": "template_ready"}

def validate(result: dict[str, Any]) -> None:
    """Check Q3 constraints, units, bounds, and numerical sanity."""
    if result.get("status") != "template_ready":
        raise ValueError("replace this template validation with model checks")

def save_results(result: dict[str, Any]) -> Path:
    """Save Q3 results."""
    return save_json(result, RESULTS_DIR / QUESTION / "result.json")

def plot_results(result: dict[str, Any]) -> Path:
    """Create Q3 figures here after defining a figure contract."""
    del result
    return ensure_dir(FIGURES_DIR / QUESTION)


def main() -> dict[str, Any]:
    """Run the complete Q3 template pipeline."""
    logger = question_logger(QUESTION)
    inputs = load_inputs()
    model = build_model(inputs)
    result = solve(model, inputs)
    validate(result)
    output = save_results(result)
    figure_dir = plot_results(result)
    logger.info("saved result to %s; figures go to %s", output, figure_dir)
    output_dir = ensure_dir(RESULTS_DIR / QUESTION)
    print(f"Q3 workspace ready: {output_dir}")
    return result


if __name__ == "__main__":
    main()
