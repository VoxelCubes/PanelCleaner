from pathlib import Path
import pcleaner.ocr.parsers as op
from tests.helpers import mock_file_path

from tests.mock_files import ocr_output


def test_parse_good_csv():
    file_path = mock_file_path("good_detected_text.csv", ocr_output)

    results, errors = op.parse_ocr_data(file_path)

    assert not errors
    assert len(results) == 1
    first_result = results[0]
    assert len(first_result.removed_box_data) == 2
    assert first_result.path == Path("img1.jpg")
    assert first_result.removed_box_data[0][1].area == 20_000


def test_parse_good_txt():
    file_path = mock_file_path("good_detected_text.txt", ocr_output)

    results, errors = op.parse_ocr_data(file_path)

    assert not errors
    assert len(results) == 2
    first_result = results[0]
    assert len(first_result.removed_box_data) == 2
    assert first_result.path == Path("page1.jpg")
    second_result = results[1]
    assert len(second_result.removed_box_data) == 3
    assert second_result.path == Path("page2.jpg")


def test_file_type_auto_detection_csv():
    file_path = mock_file_path("good_detected_text.csv", ocr_output)

    results, errors = op.parse_ocr_data(file_path)
    auto_results, auto_errors = op.parse_csv(file_path)

    assert results == auto_results
    assert errors == auto_errors


def test_file_type_auto_detection_txt():
    file_path = mock_file_path("good_detected_text.txt", ocr_output)

    results, errors = op.parse_ocr_data(file_path)
    auto_results, auto_errors = op.parse_plain_text(file_path)

    assert results == auto_results
    assert errors == auto_errors
