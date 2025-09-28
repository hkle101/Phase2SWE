import sys
import pytest
from cli import main

def test_main_no_args_prints_usage(capsys):
    sys.argv = ["cli.main"]  # no URL_FILE
    with pytest.raises(SystemExit):
        main.main()
    out = capsys.readouterr().out
    assert "Usage:" in out

def test_process_url_unknown_category():
    result = main.process_url("https://example.com/something")
    assert result["category"] == "UNKNOWN"