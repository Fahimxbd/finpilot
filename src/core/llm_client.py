"""Optional local LLM client using Ollama's HTTP API."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

import requests

from core.api_guard import APIGuard
from core.audit import AuditLogger
from core.disclaimer import MASTER_DISCLAIMER
from core.settings import LimitsConfig, load_limits


def estimate_tokens(text: str) -> int:
    """Conservative dependency-free estimate suitable for budget reservation."""
    return max(1, (len(text) + 3) // 4)


@dataclass(frozen=True)
class LLMResponse:
    text: str
    prompt_tokens: int
    completion_tokens: int
    model: str
    disclaimer: str = MASTER_DISCLAIMER

    @property
    def total_tokens(self) -> int:
        return self.prompt_tokens + self.completion_tokens


class LocalOllamaClient:
    def __init__(
        self,
        *,
        guard: APIGuard | None = None,
        config: LimitsConfig | None = None,
        base_url: str | None = None,
        model: str | None = None,
        timeout_seconds: int | None = None,
    ) -> None:
        self.config = config or load_limits()
        self.guard = guard or APIGuard(self.config)
        self.base_url = (base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")).rstrip(
            "/"
        )
        self.model = model or os.getenv("OLLAMA_MODEL", "gemma3:4b")
        self.timeout_seconds = timeout_seconds or int(os.getenv("OLLAMA_TIMEOUT_SECONDS", "120"))
        self.audit = AuditLogger(self.config.audit_file)

    def generate(
        self, prompt: str, *, max_output_tokens: int = 600, system: str = ""
    ) -> LLMResponse:
        if os.getenv("FINPILOT_ENABLE_LLM", "false").lower() != "true":
            raise RuntimeError(
                "Local LLM is disabled. Set FINPILOT_ENABLE_LLM=true to enable Ollama."
            )

        reserved = estimate_tokens(prompt + system) + max_output_tokens
        reservation = self.guard.reserve("local_llm", reserved)
        response_text = ""
        status = "error"
        actual_total = reserved
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "system": system,
                    "stream": False,
                    "options": {"num_predict": max_output_tokens, "temperature": 0.1},
                },
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
            payload: dict[str, Any] = response.json()
            response_text = str(payload.get("response", "")).strip()
            prompt_tokens = int(
                payload.get("prompt_eval_count") or estimate_tokens(prompt + system)
            )
            completion_tokens = int(payload.get("eval_count") or estimate_tokens(response_text))
            actual_total = prompt_tokens + completion_tokens
            self.guard.reconcile_tokens(reservation, actual_total)
            status = "success"
            return LLMResponse(response_text, prompt_tokens, completion_tokens, self.model)
        except Exception:
            self.guard.rollback(reservation)
            actual_total = 0
            raise
        finally:
            self.audit.log_ai_call(
                provider="ollama-local",
                model=self.model,
                prompt=prompt,
                response=response_text,
                estimated_tokens=actual_total,
                status=status,
                metadata={"base_url": self.base_url},
            )
