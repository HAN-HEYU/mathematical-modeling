from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from .config import DATA_DIR, FIGURES_DIR, PROJECT_ROOT, RESULTS_DIR


def ensure_dir(path: str | Path) -> Path:
    """Create a directory if needed and return it as a Path."""
    target = Path(path)
    target.mkdir(parents=True, exist_ok=True)
    return target


def project_path(*parts: str) -> Path:
    """Build a path below the repository root."""
    return PROJECT_ROOT.joinpath(*parts)


def sha256_file(path: str | Path) -> str:
    """Return the SHA-256 digest of a file without loading it all into memory."""
    digest = hashlib.sha256()
    with Path(path).open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def save_json(data: dict[str, Any], path: str | Path) -> Path:
    """Write a dictionary as readable UTF-8 JSON."""
    output_path = Path(path)
    ensure_dir(output_path.parent)
    output_path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return output_path


__all__ = [
    "DATA_DIR",
    "FIGURES_DIR",
    "PROJECT_ROOT",
    "RESULTS_DIR",
    "ensure_dir",
    "project_path",
    "save_json",
    "sha256_file",
]
