from unittest.mock import patch
import pcleaner.gui.log_parser as lp
from tests.helpers import read_mock_file


def test_parse_good():
    # Test with good_pcleaner.log
    logfile = read_mock_file("good_pcleaner.log")
    # mock the get_username function to return "testvm"
    with patch("pcleaner.gui.log_parser.get_username", return_value="testvm"):
        sessions = lp.parse_log_file(logfile)

    assert len(sessions) == lp.MAX_SESSIONS
    assert sessions[19].criticals == 0
    assert sessions[19].errors == 0
    assert sessions[1].criticals == 3
    assert sessions[1].errors == 0
    assert sessions[1].corrupted is False
