"""Mandatory disclaimer helpers for all financial outputs."""

from __future__ import annotations

from collections.abc import Callable
from functools import wraps
from typing import Any, ParamSpec, TypeVar

P = ParamSpec("P")
R = TypeVar("R")

MASTER_DISCLAIMER = (
    "FinPilot does not provide financial, investment, tax, or legal advice. "
    "It is an educational automation tool. Consult a licensed professional "
    "before making financial decisions."
)

TRADING_DISCLAIMER = (
    "Informational only; this is not a buy/sell recommendation and FinPilot cannot execute trades."
)


def disclaimer_for(context: str = "general") -> str:
    context = context.lower().strip()
    if context in {"trading", "market", "portfolio"}:
        return f"{MASTER_DISCLAIMER} {TRADING_DISCLAIMER}"
    return MASTER_DISCLAIMER


def attach_disclaimer(payload: Any, context: str = "general") -> dict[str, Any]:
    """Wrap any payload in a stable envelope containing a mandatory disclaimer."""
    return {
        "data": payload,
        "disclaimer": disclaimer_for(context),
    }


def disclaimed(context: str = "general") -> Callable[[Callable[P, R]], Callable[P, dict[str, Any]]]:
    """Decorator that makes omission of the disclaimer difficult at service boundaries."""

    def decorator(func: Callable[P, R]) -> Callable[P, dict[str, Any]]:
        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> dict[str, Any]:
            return attach_disclaimer(func(*args, **kwargs), context=context)

        return wrapper

    return decorator
