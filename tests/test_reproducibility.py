import json

from src.reproducibility import build_manifest, save_manifest


def test_manifest_records_input_hash_command_and_packages(tmp_path):
    source = tmp_path / "input.csv"
    source.write_text("x\n1\n", encoding="utf-8")

    manifest = build_manifest(
        inputs=[source],
        parameters={"alpha": 0.1},
        command="python -m src.q1",
        packages=["numpy", "package-that-does-not-exist"],
    )
    output = save_manifest(manifest, tmp_path / "复现清单.json")

    saved = json.loads(output.read_text(encoding="utf-8"))
    assert saved["command"] == "python -m src.q1"
    assert len(saved["inputs"][0]["sha256"]) == 64
    assert saved["environment"]["packages"]["package-that-does-not-exist"] == "not-installed"
