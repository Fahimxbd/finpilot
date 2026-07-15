import json

from finpilot_cli import main


def test_sip_cli_outputs_json_and_disclaimer(tmp_path, monkeypatch, capsys) -> None:
    monkeypatch.setenv("FINPILOT_USAGE_FILE", str(tmp_path / "usage.json"))
    status = main(
        [
            "sip",
            "--monthly",
            "100",
            "--annual-rate",
            "0",
            "--years",
            "1",
        ]
    )
    assert status == 0
    output = json.loads(capsys.readouterr().out)
    assert output["data"]["estimated_future_value"] == 1200
    assert "disclaimer" in output
