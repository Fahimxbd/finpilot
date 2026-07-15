"""Configuration loading and environment overrides."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from importlib.resources import files
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class ServiceLimit:
    monthly_calls: int


@dataclass(frozen=True)
class LimitsConfig:
    max_monthly_api_calls: int = 500
    max_tokens_per_run: int = 8000
    near_limit_ratio: float = 0.8
    min_seconds_between_calls: float = 1.0
    queue_on_throttle: bool = True
    usage_file: str = ".finpilot/usage.json"
    audit_file: str = ".finpilot/ai_audit.jsonl"
    services: dict[str, ServiceLimit] = field(default_factory=dict)


def _positive_int(value: Any, name: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise ValueError(f"{name} must be greater than zero")
    return parsed


def load_limits(path: str | Path | None = None) -> LimitsConfig:
    configured_path = path or os.getenv("FINPILOT_LIMITS_FILE")
    config_path = Path(configured_path or "config/limits.yaml")
    raw: dict[str, Any] = {}
    if config_path.exists():
        config_text = config_path.read_text(encoding="utf-8")
    elif configured_path:
        config_text = ""
    else:
        config_text = files("core").joinpath("default_limits.yaml").read_text(encoding="utf-8")

    if config_text:
        loaded = yaml.safe_load(config_text) or {}
        if not isinstance(loaded, dict):
            raise ValueError("limits.yaml must contain a mapping")
        raw = loaded

    monthly = os.getenv("MAX_MONTHLY_API_CALLS") or raw.get("max_monthly_api_calls", 500)
    tokens = os.getenv("MAX_TOKENS_PER_RUN") or raw.get("max_tokens_per_run", 8000)
    ratio = float(raw.get("near_limit_ratio", 0.8))
    if not 0 < ratio < 1:
        raise ValueError("near_limit_ratio must be between 0 and 1")

    service_limits: dict[str, ServiceLimit] = {}
    for name, values in (raw.get("services") or {}).items():
        if not isinstance(values, dict):
            raise ValueError(f"services.{name} must be a mapping")
        service_limits[name] = ServiceLimit(
            monthly_calls=_positive_int(
                values.get("monthly_calls", monthly), f"services.{name}.monthly_calls"
            )
        )

    return LimitsConfig(
        max_monthly_api_calls=_positive_int(monthly, "max_monthly_api_calls"),
        max_tokens_per_run=_positive_int(tokens, "max_tokens_per_run"),
        near_limit_ratio=ratio,
        min_seconds_between_calls=max(0.0, float(raw.get("min_seconds_between_calls", 1.0))),
        queue_on_throttle=bool(raw.get("queue_on_throttle", True)),
        usage_file=os.getenv("FINPILOT_USAGE_FILE", raw.get("usage_file", ".finpilot/usage.json")),
        audit_file=os.getenv(
            "FINPILOT_AUDIT_FILE", raw.get("audit_file", ".finpilot/ai_audit.jsonl")
        ),
        services=service_limits,
    )
