"""Hard API-call and token-budget enforcement with local JSON accounting."""

from __future__ import annotations

import json
import logging
import os
import threading
import time
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from functools import wraps
from pathlib import Path
from typing import Any, ParamSpec, TypeVar

from filelock import FileLock

from core.settings import LimitsConfig, load_limits

LOGGER = logging.getLogger("finpilot.api_guard")
P = ParamSpec("P")
R = TypeVar("R")


class BudgetExceededError(RuntimeError):
    """Raised when an API call would exceed a configured hard limit."""


class ThrottleRequiredError(RuntimeError):
    """Raised when queueing is disabled and a call is attempted too quickly."""


@dataclass
class Reservation:
    service: str
    estimated_tokens: int
    month: str
    run_id: str
    created_at: str


class APIGuard:
    """Coordinates call budgets, per-run token budgets, throttling, and usage persistence."""

    def __init__(self, config: LimitsConfig | None = None, run_id: str | None = None) -> None:
        self.config = config or load_limits()
        self.usage_path = Path(self.config.usage_file)
        self.usage_path.parent.mkdir(parents=True, exist_ok=True)
        self.lock = FileLock(str(self.usage_path) + ".lock")
        self.run_id = run_id or f"run-{datetime.now(UTC).strftime('%Y%m%dT%H%M%S')}-{os.getpid()}"
        self._run_tokens = 0
        self._thread_lock = threading.RLock()
        self._last_call_at = 0.0

    @staticmethod
    def current_month() -> str:
        return datetime.now(UTC).strftime("%Y-%m")

    def _empty_usage(self) -> dict[str, Any]:
        return {"months": {}}

    def _load_usage_unlocked(self) -> dict[str, Any]:
        if not self.usage_path.exists():
            return self._empty_usage()
        try:
            data = json.loads(self.usage_path.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else self._empty_usage()
        except (json.JSONDecodeError, OSError):
            LOGGER.warning("Usage file was unreadable; preserving it and starting a clean ledger")
            if self.usage_path.exists():
                backup = self.usage_path.with_suffix(self.usage_path.suffix + ".corrupt")
                self.usage_path.replace(backup)
            return self._empty_usage()

    def _save_usage_unlocked(self, data: dict[str, Any]) -> None:
        temp = self.usage_path.with_suffix(self.usage_path.suffix + ".tmp")
        temp.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")
        temp.replace(self.usage_path)

    def _month_bucket(self, data: dict[str, Any], month: str) -> dict[str, Any]:
        months = data.setdefault("months", {})
        return months.setdefault(month, {"calls": 0, "tokens": 0, "services": {}})

    def _service_bucket(self, month_bucket: dict[str, Any], service: str) -> dict[str, int]:
        return month_bucket.setdefault("services", {}).setdefault(
            service, {"calls": 0, "tokens": 0}
        )

    def _enforce_throttle(self) -> None:
        wait = self.config.min_seconds_between_calls - (time.monotonic() - self._last_call_at)
        if wait <= 0:
            return
        if not self.config.queue_on_throttle:
            raise ThrottleRequiredError(f"Call throttled; retry after {wait:.2f} seconds")
        LOGGER.info("Throttling API call for %.2f seconds", wait)
        time.sleep(wait)

    def reserve(self, service: str, estimated_tokens: int = 0) -> Reservation:
        if estimated_tokens < 0:
            raise ValueError("estimated_tokens cannot be negative")

        with self._thread_lock:
            if self._run_tokens + estimated_tokens > self.config.max_tokens_per_run:
                raise BudgetExceededError(
                    f"Run token cap exceeded: {self._run_tokens + estimated_tokens} > "
                    f"{self.config.max_tokens_per_run}"
                )
            self._enforce_throttle()
            month = self.current_month()
            with self.lock:
                data = self._load_usage_unlocked()
                month_bucket = self._month_bucket(data, month)
                service_bucket = self._service_bucket(month_bucket, service)

                if int(month_bucket["calls"]) + 1 > self.config.max_monthly_api_calls:
                    raise BudgetExceededError("Monthly API call cap reached")

                service_limit = self.config.services.get(service)
                if service_limit and int(service_bucket["calls"]) + 1 > service_limit.monthly_calls:
                    raise BudgetExceededError(f"Monthly call cap reached for service '{service}'")

                month_bucket["calls"] = int(month_bucket["calls"]) + 1
                month_bucket["tokens"] = int(month_bucket.get("tokens", 0)) + estimated_tokens
                service_bucket["calls"] = int(service_bucket["calls"]) + 1
                service_bucket["tokens"] = int(service_bucket.get("tokens", 0)) + estimated_tokens
                self._save_usage_unlocked(data)

            self._run_tokens += estimated_tokens
            self._last_call_at = time.monotonic()
            self._warn_if_near_limit(month_bucket)
            return Reservation(
                service=service,
                estimated_tokens=estimated_tokens,
                month=month,
                run_id=self.run_id,
                created_at=datetime.now(UTC).isoformat(),
            )

    def reconcile_tokens(self, reservation: Reservation, actual_tokens: int) -> None:
        """Replace a reserved estimate with actual usage without allowing overspend."""
        if actual_tokens < 0:
            raise ValueError("actual_tokens cannot be negative")
        delta = actual_tokens - reservation.estimated_tokens
        if delta == 0:
            return
        with self._thread_lock:
            if delta > 0 and self._run_tokens + delta > self.config.max_tokens_per_run:
                raise BudgetExceededError("Actual token usage would exceed the per-run cap")
            with self.lock:
                data = self._load_usage_unlocked()
                month_bucket = self._month_bucket(data, reservation.month)
                service_bucket = self._service_bucket(month_bucket, reservation.service)
                month_bucket["tokens"] = max(0, int(month_bucket.get("tokens", 0)) + delta)
                service_bucket["tokens"] = max(0, int(service_bucket.get("tokens", 0)) + delta)
                self._save_usage_unlocked(data)
            self._run_tokens = max(0, self._run_tokens + delta)

    def rollback(self, reservation: Reservation) -> None:
        """Undo a failed call reservation so transient failures do not consume the call budget."""
        with self._thread_lock, self.lock:
            data = self._load_usage_unlocked()
            month_bucket = self._month_bucket(data, reservation.month)
            service_bucket = self._service_bucket(month_bucket, reservation.service)
            month_bucket["calls"] = max(0, int(month_bucket.get("calls", 0)) - 1)
            month_bucket["tokens"] = max(
                0, int(month_bucket.get("tokens", 0)) - reservation.estimated_tokens
            )
            service_bucket["calls"] = max(0, int(service_bucket.get("calls", 0)) - 1)
            service_bucket["tokens"] = max(
                0, int(service_bucket.get("tokens", 0)) - reservation.estimated_tokens
            )
            self._save_usage_unlocked(data)
            self._run_tokens = max(0, self._run_tokens - reservation.estimated_tokens)

    @contextmanager
    def budget(self, service: str, estimated_tokens: int = 0) -> Iterator[Reservation]:
        reservation = self.reserve(service, estimated_tokens)
        try:
            yield reservation
        except Exception:
            self.rollback(reservation)
            raise

    def guarded(
        self,
        service: str,
        estimated_tokens: int | Callable[..., int] = 0,
    ) -> Callable[[Callable[P, R]], Callable[P, R]]:
        def decorator(func: Callable[P, R]) -> Callable[P, R]:
            @wraps(func)
            def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
                estimate = (
                    estimated_tokens(*args, **kwargs)
                    if callable(estimated_tokens)
                    else estimated_tokens
                )
                with self.budget(service, int(estimate)):
                    return func(*args, **kwargs)

            return wrapper

        return decorator

    def snapshot(self) -> dict[str, Any]:
        with self.lock:
            data = self._load_usage_unlocked()
        return {
            "run_id": self.run_id,
            "run_tokens": self._run_tokens,
            "config": asdict(self.config),
            "usage": data,
        }

    def _warn_if_near_limit(self, month_bucket: dict[str, Any]) -> None:
        calls = int(month_bucket.get("calls", 0))
        if calls >= self.config.max_monthly_api_calls * self.config.near_limit_ratio:
            LOGGER.warning(
                "API usage is near the monthly hard cap: %s/%s",
                calls,
                self.config.max_monthly_api_calls,
            )
        if self._run_tokens >= self.config.max_tokens_per_run * self.config.near_limit_ratio:
            LOGGER.warning(
                "Token usage is near the per-run hard cap: %s/%s",
                self._run_tokens,
                self.config.max_tokens_per_run,
            )
