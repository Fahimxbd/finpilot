from pathlib import Path

import pytest

from core.api_guard import APIGuard, BudgetExceededError
from core.settings import LimitsConfig, ServiceLimit


def config(tmp_path: Path, *, calls: int = 2, tokens: int = 20) -> LimitsConfig:
    return LimitsConfig(
        max_monthly_api_calls=calls,
        max_tokens_per_run=tokens,
        near_limit_ratio=0.8,
        min_seconds_between_calls=0,
        queue_on_throttle=True,
        usage_file=str(tmp_path / "usage.json"),
        audit_file=str(tmp_path / "audit.jsonl"),
        services={"test": ServiceLimit(monthly_calls=calls)},
    )


def test_blocks_monthly_call_cap(tmp_path: Path) -> None:
    guard = APIGuard(config(tmp_path, calls=1))
    guard.reserve("test")
    with pytest.raises(BudgetExceededError):
        guard.reserve("test")


def test_blocks_per_run_token_cap(tmp_path: Path) -> None:
    guard = APIGuard(config(tmp_path, tokens=5))
    guard.reserve("test", estimated_tokens=4)
    with pytest.raises(BudgetExceededError):
        guard.reserve("test", estimated_tokens=2)


def test_failed_context_rolls_back_call_and_tokens(tmp_path: Path) -> None:
    guard = APIGuard(config(tmp_path, calls=1, tokens=10))
    with pytest.raises(RuntimeError):
        with guard.budget("test", estimated_tokens=4):
            raise RuntimeError("network failure")

    snapshot = guard.snapshot()
    month = guard.current_month()
    assert snapshot["run_tokens"] == 0
    assert snapshot["usage"]["months"][month]["calls"] == 0

    guard.reserve("test", estimated_tokens=4)


def test_reconciles_estimate_to_actual(tmp_path: Path) -> None:
    guard = APIGuard(config(tmp_path, tokens=10))
    reservation = guard.reserve("test", estimated_tokens=6)
    guard.reconcile_tokens(reservation, actual_tokens=3)
    assert guard.snapshot()["run_tokens"] == 3
