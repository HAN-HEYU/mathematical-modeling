import math

import numpy as np
import pytest

from src.geometry import (
    angle_between,
    distance,
    point_to_line_distance,
    point_to_segment_distance,
    projection_on_line,
    rotation_matrix_2d,
    rotation_matrix_z,
    unit_vector,
)


def test_unit_vector_and_distance():
    np.testing.assert_allclose(unit_vector([3, 4]), [0.6, 0.8])
    assert distance([0, 0], [3, 4]) == pytest.approx(5.0)


def test_unit_vector_rejects_zero_vector():
    with pytest.raises(ValueError, match="zero vector"):
        unit_vector([0, 0])


def test_angle_between_orthogonal_vectors():
    assert angle_between([1, 0], [0, 1]) == pytest.approx(math.pi / 2)


def test_projection_and_point_to_line_distance():
    projection = projection_on_line([2, 3], [0, 0], [4, 0])
    np.testing.assert_allclose(projection, [2, 0])
    assert point_to_line_distance([2, 3], [0, 0], [4, 0]) == pytest.approx(3.0)


def test_point_to_segment_distance_clamps_to_endpoint():
    assert point_to_segment_distance([3, 4], [0, 0], [2, 0]) == pytest.approx(
        math.sqrt(17)
    )


def test_point_to_segment_distance_handles_zero_length_segment():
    assert point_to_segment_distance([3, 4], [0, 0], [0, 0]) == pytest.approx(5.0)


def test_rotation_matrices_rotate_counterclockwise():
    np.testing.assert_allclose(
        rotation_matrix_2d(math.pi / 2) @ np.array([1.0, 0.0]),
        [0.0, 1.0],
        atol=1e-12,
    )
    np.testing.assert_allclose(
        rotation_matrix_z(math.pi / 2) @ np.array([1.0, 0.0, 2.0]),
        [0.0, 1.0, 2.0],
        atol=1e-12,
    )
