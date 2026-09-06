from src.logging_utils import setup_logging


def test_setup_logging_writes_utf8_file(tmp_path):
    output = tmp_path / "run.log"
    logger = setup_logging("test-modeling-logger", log_file=output)

    logger.info("中文路径与结果")
    for handler in logger.handlers:
        handler.flush()

    assert "中文路径与结果" in output.read_text(encoding="utf-8")
