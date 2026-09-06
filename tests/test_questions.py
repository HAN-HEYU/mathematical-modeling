import importlib

import pytest


class _Logger:
    def info(self, *args, **kwargs):
        pass


@pytest.mark.parametrize("question", ["q1", "q2", "q3", "q4", "q5"])
def test_question_templates_run_in_isolated_output_dirs(question, tmp_path, monkeypatch):
    module = importlib.import_module(f"src.{question}")
    monkeypatch.setattr(module, "RESULTS_DIR", tmp_path / "results")
    monkeypatch.setattr(module, "FIGURES_DIR", tmp_path / "figures")
    monkeypatch.setattr(module, "question_logger", lambda name: _Logger())

    result = module.main()

    assert result == {"question": question, "status": "template_ready"}
    assert (tmp_path / "results" / question / "result.json").is_file()
    assert (tmp_path / "figures" / question).is_dir()
