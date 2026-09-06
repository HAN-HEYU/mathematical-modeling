"""Reliable tabular data input/output for competition attachments.

Excel callers must state whether the first row is a header. This prevents a
real observation from being silently consumed as column names.
"""

from __future__ import annotations

import os
import tempfile
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import pandas as pd


PathLike = str | os.PathLike[str]


def ensure_dir(path: PathLike) -> Path:
    """Create ``path`` and its parents, then return it as a ``Path``."""
    target = Path(path).expanduser()
    target.mkdir(parents=True, exist_ok=True)
    return target


def _require_file(path: PathLike) -> Path:
    source = Path(path).expanduser()
    if not source.is_file():
        raise FileNotFoundError(f"input file does not exist: {source}")
    return source


def _check_expected_rows(frame: pd.DataFrame, expected_rows: int | None) -> None:
    if expected_rows is None:
        return
    if expected_rows < 0:
        raise ValueError("expected_rows must be non-negative")
    if len(frame) != expected_rows:
        raise ValueError(f"expected {expected_rows} rows, found {len(frame)}")


def load_excel(
    path: PathLike,
    *,
    header: int | None,
    sheet_name: str | int | list[str | int] | None = 0,
    expected_rows: int | None = None,
    **kwargs: Any,
) -> pd.DataFrame | dict[str, pd.DataFrame]:
    """Read an XLSX file with an explicit header decision.

    Pass ``header=0`` when row one contains column names and ``header=None``
    when row one is data. ``expected_rows`` is supported for a single sheet.
    """
    source = _require_file(path)
    result = pd.read_excel(source, sheet_name=sheet_name, header=header, **kwargs)
    if isinstance(result, dict):
        if expected_rows is not None:
            raise ValueError("expected_rows is only supported for one sheet")
        return result
    _check_expected_rows(result, expected_rows)
    return result


def load_csv(
    path: PathLike,
    *,
    header: int | None = 0,
    encoding: str = "utf-8-sig",
    expected_rows: int | None = None,
    **kwargs: Any,
) -> pd.DataFrame:
    """Read a CSV file and optionally enforce its data-row count."""
    frame = pd.read_csv(_require_file(path), header=header, encoding=encoding, **kwargs)
    _check_expected_rows(frame, expected_rows)
    return frame


def load_txt(
    path: PathLike,
    *,
    sep: str | None = None,
    header: int | None = None,
    encoding: str = "utf-8-sig",
    expected_rows: int | None = None,
    **kwargs: Any,
) -> pd.DataFrame:
    """Read a delimited text attachment; whitespace is inferred by default."""
    if sep is None:
        kwargs.setdefault("sep", r"\s+")
    else:
        kwargs["sep"] = sep
    frame = pd.read_csv(
        _require_file(path), header=header, encoding=encoding, **kwargs
    )
    _check_expected_rows(frame, expected_rows)
    return frame


def _atomic_target(path: PathLike) -> tuple[Path, Path]:
    target = Path(path).expanduser()
    ensure_dir(target.parent)
    descriptor, temporary_name = tempfile.mkstemp(
        dir=target.parent,
        prefix=f".{target.stem}-",
        suffix=target.suffix,
    )
    os.close(descriptor)
    return target, Path(temporary_name)


def save_csv(
    frame: pd.DataFrame,
    path: PathLike,
    *,
    index: bool = False,
    encoding: str = "utf-8-sig",
    **kwargs: Any,
) -> Path:
    """Atomically save a DataFrame as CSV."""
    target, temporary = _atomic_target(path)
    try:
        frame.to_csv(temporary, index=index, encoding=encoding, **kwargs)
        temporary.replace(target)
    finally:
        temporary.unlink(missing_ok=True)
    return target


def save_excel(
    data: pd.DataFrame | Mapping[str, pd.DataFrame],
    path: PathLike,
    *,
    index: bool = False,
    **kwargs: Any,
) -> Path:
    """Atomically save one DataFrame or a mapping of sheet names to frames."""
    target, temporary = _atomic_target(path)
    try:
        if isinstance(data, pd.DataFrame):
            data.to_excel(temporary, index=index, **kwargs)
        elif isinstance(data, Mapping) and data:
            with pd.ExcelWriter(temporary, engine="openpyxl") as writer:
                for sheet_name, frame in data.items():
                    if not isinstance(frame, pd.DataFrame):
                        raise TypeError("every workbook value must be a DataFrame")
                    frame.to_excel(writer, sheet_name=str(sheet_name), index=index)
        else:
            raise TypeError("data must be a DataFrame or a non-empty sheet mapping")
        temporary.replace(target)
    finally:
        temporary.unlink(missing_ok=True)
    return target


__all__ = [
    "ensure_dir",
    "load_csv",
    "load_excel",
    "load_txt",
    "save_csv",
    "save_excel",
]
