from src import q1


def test_q1_main_runs(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(q1, "RESULTS_DIR", tmp_path / "results")
    monkeypatch.setattr(q1, "FIGURES_DIR", tmp_path / "figures")
    monkeypatch.setattr(q1, "question_logger", lambda question: _Logger())

    result = q1.main()

    captured = capsys.readouterr()
    assert "Q1 workspace ready" in captured.out
    assert result == {"question": "q1", "status": "template_ready"}
    assert (tmp_path / "results" / "q1" / "result.json").is_file()


class _Logger:
    def info(self, *args, **kwargs):
        pass
