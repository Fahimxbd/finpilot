import json
from pathlib import Path

import pytest

from core.api_guard import APIGuard
from core.audit import AuditLogger
from core.llm_client import LocalOllamaClient
from core.settings import LimitsConfig, ServiceLimit


def config(tmp_path: Path) -> LimitsConfig:
    return LimitsConfig(
        max_monthly_api_calls=10,
        max_tokens_per_run=1000,
        near_limit_ratio=0.8,
        min_seconds_between_calls=0,
        queue_on_throttle=True,
        usage_file=str(tmp_path / "usage.json"),
        audit_file=str(tmp_path / "audit.jsonl"),
        services={"local_llm": ServiceLimit(monthly_calls=5)},
    )


def test_audit_logger_hashes_content_by_default(tmp_path: Path) -> None:
    path = tmp_path / "audit.jsonl"
    AuditLogger(path).log_ai_call(
        provider="test",
        model="model",
        prompt="sensitive prompt",
        response="sensitive response",
        estimated_tokens=8,
        status="success",
    )
    record = json.loads(path.read_text().splitlines()[0])
    assert "prompt_sha256" in record
    assert "response_sha256" in record
    assert "prompt" not in record
    assert "response" not in record


def test_local_ollama_client_is_disabled_by_default(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv("FINPILOT_ENABLE_LLM", raising=False)
    client = LocalOllamaClient(config=config(tmp_path), guard=APIGuard(config(tmp_path)))
    with pytest.raises(RuntimeError, match="disabled"):
        client.generate("hello")


def test_local_ollama_call_is_guarded_and_audited(tmp_path: Path, monkeypatch) -> None:
    class FakeResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict[str, object]:
            return {
                "response": '{"category":"income","confidence":0.8,"reason":"salary"}',
                "prompt_eval_count": 10,
                "eval_count": 12,
            }

    monkeypatch.setenv("FINPILOT_ENABLE_LLM", "true")
    monkeypatch.setattr("core.llm_client.requests.post", lambda *args, **kwargs: FakeResponse())
    limits = config(tmp_path)
    guard = APIGuard(limits)
    client = LocalOllamaClient(config=limits, guard=guard, model="test-model")
    response = client.generate("Classify salary", max_output_tokens=50)

    assert response.total_tokens == 22
    assert guard.snapshot()["run_tokens"] == 22
    audit = json.loads(Path(limits.audit_file).read_text().splitlines()[0])
    assert audit["status"] == "success"
    assert audit["model"] == "test-model"
