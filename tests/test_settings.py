from pathlib import Path

from core.settings import load_limits


def test_load_limits_and_environment_overrides(tmp_path: Path, monkeypatch) -> None:
    path = tmp_path / "limits.yaml"
    path.write_text(
        """
max_monthly_api_calls: 12
max_tokens_per_run: 300
near_limit_ratio: 0.75
min_seconds_between_calls: 0
queue_on_throttle: false
usage_file: local.json
audit_file: audit.jsonl
services:
  market_data:
    monthly_calls: 4
""".strip()
    )
    monkeypatch.setenv("MAX_MONTHLY_API_CALLS", "20")
    monkeypatch.setenv("FINPILOT_USAGE_FILE", str(tmp_path / "override.json"))
    config = load_limits(path)
    assert config.max_monthly_api_calls == 20
    assert config.max_tokens_per_run == 300
    assert config.services["market_data"].monthly_calls == 4
    assert config.usage_file.endswith("override.json")


def test_packaged_default_limits_work_outside_repository(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("FINPILOT_LIMITS_FILE", raising=False)
    monkeypatch.delenv("MAX_MONTHLY_API_CALLS", raising=False)
    config = load_limits()
    assert config.max_monthly_api_calls == 500
    assert config.services["market_data"].monthly_calls == 200
