from src import q1


def test_q1_main_runs(capsys):
    q1.main()

    captured = capsys.readouterr()
    assert "Q1 workspace ready" in captured.out
