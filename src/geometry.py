"""Reusable Euclidean geometry helpers for mathematical modeling."""

from __future__ import annotations

import math

import numpy as np
from numpy.typing import ArrayLike, NDArray


FloatArray = NDArray[np.float64]


def _as_vector(value: ArrayLike, *, name: str) -> FloatArray:
    """Convert an array-like value to a finite, non-empty 1-D vector."""
    vector = np.asarray(value, dtype=float)
    if vector.ndim != 1 or vector.size == 0:
        raise ValueError(f"{name} must be a non-empty one-dimensional vector")
    if not np.all(np.isfinite(vector)):
        raise ValueError(f"{name} must contain only finite values")
    return vector


def _matching_vectors(*named_values: tuple[str, ArrayLike]) -> list[FloatArray]:
    """Validate vectors and ensure that they have a common dimension."""
    vectors = [_as_vector(value, name=name) for name, value in named_values]
    if len({vector.size for vector in vectors}) != 1:
        raise ValueError("all vectors must have the same dimension")
    return vectors


def unit_vector(vector: ArrayLike) -> FloatArray:
    """Return a vector with the same direction and Euclidean norm equal to one.

    Raises:
        ValueError: If ``vector`` is empty, non-finite, or has zero length.
    """
    values = _as_vector(vector, name="vector")
    norm = float(np.linalg.norm(values))
    if np.isclose(norm, 0.0):
        raise ValueError("a zero vector has no unit direction")
    return values / norm


def distance(point_a: ArrayLike, point_b: ArrayLike) -> float:
    """Return the Euclidean distance between two points of equal dimension."""
    a, b = _matching_vectors(("point_a", point_a), ("point_b", point_b))
    return float(np.linalg.norm(a - b))


def angle_between(vector_a: ArrayLike, vector_b: ArrayLike) -> float:
    """Return the smaller angle between two vectors in radians.

    The result lies in the closed interval ``[0, pi]``. Zero vectors are not
    accepted because their direction is undefined.
    """
    a, b = _matching_vectors(("vector_a", vector_a), ("vector_b", vector_b))
    cosine = float(np.clip(np.dot(unit_vector(a), unit_vector(b)), -1.0, 1.0))
    return float(math.acos(cosine))


def projection_on_line(
    point: ArrayLike,
    line_start: ArrayLike,
    line_end: ArrayLike,
) -> FloatArray:
    """Project a point orthogonally onto an infinite line.

    The line is defined by two distinct points. The returned point may lie
    outside the corresponding line segment.
    """
    p, start, end = _matching_vectors(
        ("point", point),
        ("line_start", line_start),
        ("line_end", line_end),
    )
    direction = end - start
    squared_length = float(np.dot(direction, direction))
    if np.isclose(squared_length, 0.0):
        raise ValueError("line_start and line_end must be distinct")
    parameter = float(np.dot(p - start, direction) / squared_length)
    return start + parameter * direction


def point_to_line_distance(
    point: ArrayLike,
    line_start: ArrayLike,
    line_end: ArrayLike,
) -> float:
    """Return the shortest distance from a point to an infinite line."""
    projection = projection_on_line(point, line_start, line_end)
    return distance(point, projection)


def point_to_segment_distance(
    point: ArrayLike,
    segment_start: ArrayLike,
    segment_end: ArrayLike,
) -> float:
    """Return the shortest distance from a point to a closed line segment.

    A zero-length segment is treated as a single point.
    """
    p, start, end = _matching_vectors(
        ("point", point),
        ("segment_start", segment_start),
        ("segment_end", segment_end),
    )
    direction = end - start
    squared_length = float(np.dot(direction, direction))
    if np.isclose(squared_length, 0.0):
        return distance(p, start)
    parameter = float(np.dot(p - start, direction) / squared_length)
    closest_point = start + np.clip(parameter, 0.0, 1.0) * direction
    return distance(p, closest_point)


def rotation_matrix_2d(angle_radians: float) -> FloatArray:
    """Return the 2-by-2 counterclockwise rotation matrix for an angle."""
    angle = float(angle_radians)
    if not math.isfinite(angle):
        raise ValueError("angle_radians must be finite")
    cosine = math.cos(angle)
    sine = math.sin(angle)
    return np.array([[cosine, -sine], [sine, cosine]], dtype=float)


def rotation_matrix_z(angle_radians: float) -> FloatArray:
    """Return the 3-by-3 matrix for rotation about the positive z-axis."""
    matrix = np.eye(3, dtype=float)
    matrix[:2, :2] = rotation_matrix_2d(angle_radians)
    return matrix


__all__ = [
    "angle_between",
    "distance",
    "point_to_line_distance",
    "point_to_segment_distance",
    "projection_on_line",
    "rotation_matrix_2d",
    "rotation_matrix_z",
    "unit_vector",
]
