from __future__ import annotations

from .utils import RESULTS_DIR, ensure_dir


def main() -> None:
    output_dir = ensure_dir(RESULTS_DIR / "q2")
    print(f"Q2 workspace ready: {output_dir}")


if __name__ == "__main__":
    main()
