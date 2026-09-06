import pytest

from src.config import DEFAULT_CONFIG, PROJECT_ROOT, RuntimeConfig


def test_project_root_contains_repository_readme():
    assert (PROJECT_ROOT / "README.md").is_file()


def test_runtime_config_has_safe_defaults():
    assert DEFAULT_CONFIG.random_seed == 42
    assert DEFAULT_CONFIG.figure_dpi >= 300


def test_runtime_config_rejects_invalid_tolerance():
    with pytest.raises(ValueError, match="tolerance"):
        RuntimeConfig(tolerance=0.0)
