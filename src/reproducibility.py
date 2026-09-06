"""Create a machine-readable manifest for reproducible experiments."""

from __future__ import annotations

import importlib.metadata
import platform
import sys
from collections.abc import Mapping, Sequence
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .config import RANDOM_SEED, RESULTS_DIR
from .utils import save_json, sha256_file


def build_manifest(
    *,
    inputs: Sequence[str | Path] = (),
    parameters: Mapping[str, Any] | None = None,
    command: str,
    packages: Sequence[str] = ("numpy", "pandas", "scipy", "matplotlib"),
    seed: int = RANDOM_SEED,
) -> dict[str, Any]:
    """Collect input hashes, environment versions, parameters, and command."""
    if not command.strip():
        raise ValueError("command must not be empty")
    input_records = []
    for item in inputs:
        path = Path(item).resolve()
        if not path.is_file():
            raise FileNotFoundError(f"input file does not exist: {path}")
        input_records.append(
            {"path": str(path), "sha256": sha256_file(path), "bytes": path.stat().st_size}
        )

    versions: dict[str, str] = {}
    for package in packages:
        try:
            versions[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            versions[package] = "not-installed"

    return {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "command": command,
        "seed": int(seed),
        "parameters": dict(parameters or {}),
        "inputs": input_records,
        "environment": {
            "python": sys.version.split()[0],
            "platform": platform.platform(),
            "packages": versions,
        },
    }


def save_manifest(
    manifest: Mapping[str, Any],
    path: str | Path = RESULTS_DIR / "复现清单.json",
) -> Path:
    """Save a manifest as UTF-8 JSON."""
    return save_json(dict(manifest), path)


__all__ = ["build_manifest", "save_manifest"]
