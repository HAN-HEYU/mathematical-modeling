import pandas as pd
import pytest

from src.data_io import load_csv, load_excel, load_txt, save_csv, save_excel


def test_csv_round_trip_preserves_unicode(tmp_path):
    expected = pd.DataFrame({"方案": ["甲", "乙"], "得分": [1.5, 2.5]})
    output = save_csv(expected, tmp_path / "nested" / "result.csv")

    actual = load_csv(output, expected_rows=2)

    pd.testing.assert_frame_equal(actual, expected)


def test_excel_requires_explicit_header_and_checks_rows(tmp_path):
    source = tmp_path / "attachment.xlsx"
    pd.DataFrame([[1, 2], [3, 4]]).to_excel(source, index=False, header=False)

    actual = load_excel(source, header=None, expected_rows=2)

    pd.testing.assert_frame_equal(actual, pd.DataFrame([[1, 2], [3, 4]]))
    with pytest.raises(ValueError, match="expected 3 rows"):
        load_excel(source, header=None, expected_rows=3)


def test_multisheet_excel_round_trip(tmp_path):
    workbook = {
        "输入": pd.DataFrame({"x": [1, 2]}),
        "结果": pd.DataFrame({"y": [3, 4]}),
    }
    output = save_excel(workbook, tmp_path / "result.xlsx")

    actual = load_excel(output, header=0, sheet_name=None)

    assert set(actual) == {"输入", "结果"}
    pd.testing.assert_frame_equal(actual["输入"], workbook["输入"])


def test_load_txt_uses_whitespace_by_default(tmp_path):
    source = tmp_path / "attachment.txt"
    source.write_text("1 2\n3 4\n", encoding="utf-8")

    actual = load_txt(source, expected_rows=2)

    pd.testing.assert_frame_equal(actual, pd.DataFrame([[1, 2], [3, 4]]))
