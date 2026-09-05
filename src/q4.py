from __future__ import annotations

from .utils import RESULTS_DIR, ensure_dir


def main() -> None:
    output_dir = ensure_dir(RESULTS_DIR / "final")
    print(f"Q4 workspace ready: {output_dir}")


if __name__ == "__main__":
    main()
