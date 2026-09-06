import json
import os
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_environment_check_script_reports_selected_features():
    completed = subprocess.run(
        [
            sys.executable,
            "scripts/check_env.py",
            "--features",
            "data",
            "visualization",
            "excel",
            "optimization",
        ],
        cwd=PROJECT_ROOT,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        env={**os.environ, "PYTHONUTF8": "1"},
    )

    report = json.loads(completed.stdout)
    assert report["ok"] is True
    assert report["features"] == ["data", "visualization", "excel", "optimization"]


def test_repro_manifest_script_stays_inside_project(tmp_path):
    input_file = tmp_path / "input.csv"
    input_file.write_text("x\n1\n", encoding="utf-8")
    output = tmp_path / "project" / "results" / "manifest.json"
    completed = subprocess.run(
        [
            sys.executable,
            str(PROJECT_ROOT / "scripts" / "repro_manifest.py"),
            "--project-root",
            str(tmp_path / "project"),
            "--input",
            str(input_file),
            "--seed",
            "42",
            "--command",
            "python -m src.q1",
            "--output",
            "results/manifest.json",
        ],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        env={**os.environ, "PYTHONUTF8": "1"},
    )

    assert str(output) in completed.stdout
    assert json.loads(output.read_text(encoding="utf-8"))["random_seed"] == 42


def test_repro_manifest_rejects_output_outside_project(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    outside = tmp_path / "outside.json"

    completed = subprocess.run(
        [
            sys.executable,
            str(PROJECT_ROOT / "scripts" / "repro_manifest.py"),
            "--project-root",
            str(project),
            "--seed",
            "42",
            "--command",
            "python -m src.q1",
            "--output",
            "../outside.json",
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        env={**os.environ, "PYTHONUTF8": "1"},
    )

    assert completed.returncode != 0
    assert "输出路径必须位于 PROJECT_ROOT 内部" in completed.stderr
    assert not outside.exists()
