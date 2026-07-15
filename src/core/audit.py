"""Local append-only audit logging for AI-assisted operations."""

from __future__ import annotations

import hashlib
import json
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from filelock import FileLock


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()


class AuditLogger:
    def __init__(self, path: str | Path, log_full_content: bool | None = None) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if log_full_content is None:
            log_full_content = os.getenv("FINPILOT_LOG_FULL_AI_CONTENT", "false").lower() == "true"
        self.log_full_content = log_full_content
        self.lock = FileLock(str(self.path) + ".lock")

    def log_ai_call(
        self,
        *,
        provider: str,
        model: str,
        prompt: str,
        response: str,
        estimated_tokens: int,
        status: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        record: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "provider": provider,
            "model": model,
            "prompt_sha256": _sha256(prompt),
            "response_sha256": _sha256(response),
            "prompt_chars": len(prompt),
            "response_chars": len(response),
            "estimated_tokens": int(estimated_tokens),
            "status": status,
            "metadata": metadata or {},
        }
        if self.log_full_content:
            record["prompt"] = prompt
            record["response"] = response

        with self.lock:
            with self.path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(record, ensure_ascii=False) + "\n")
