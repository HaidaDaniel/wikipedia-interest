import json

import pytest

from wikipedia_interest.cli import main


@pytest.mark.parametrize(
    "argv",
    [
        ["analyze", "--granularity", "nope"],
        ["analyze", "--criterion", "random"],
        ["report"],
        ["unknown-command"],
        ["report", "--run"],
    ],
)
def test_argparse_errors_use_machine_readable_contract(argv, capsys):
    exit_code = main(argv)
    captured = capsys.readouterr()

    payload = json.loads(captured.out)
    assert exit_code == 2
    assert payload["status"] == "error"
    assert payload["error"]["code"] == "INVALID_REQUEST"
    assert payload["error"]["details"] == {}
    assert set(payload["error"]) == {"code", "message", "details"}
    assert payload["error"]["message"]
    assert "Traceback" not in captured.out
    assert "Traceback" not in captured.err
    assert "INVALID_REQUEST:" in captured.err
