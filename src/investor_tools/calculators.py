"""Deterministic educational calculators. Rates are user-provided assumptions."""

from __future__ import annotations

from typing import Any


def _validate_non_negative(value: float, name: str) -> float:
    value = float(value)
    if value < 0:
        raise ValueError(f"{name} cannot be negative")
    return value


def compound_growth(
    principal: float,
    annual_rate_percent: float,
    years: float,
    compounds_per_year: int = 12,
) -> dict[str, Any]:
    principal = _validate_non_negative(principal, "principal")
    years = _validate_non_negative(years, "years")
    compounds_per_year = int(compounds_per_year)
    if compounds_per_year <= 0:
        raise ValueError("compounds_per_year must be greater than zero")
    rate = float(annual_rate_percent) / 100
    future_value = principal * (1 + rate / compounds_per_year) ** (compounds_per_year * years)
    return {
        "principal": round(principal, 2),
        "annual_rate_percent": float(annual_rate_percent),
        "years": years,
        "compounds_per_year": compounds_per_year,
        "estimated_future_value": round(future_value, 2),
        "estimated_growth": round(future_value - principal, 2),
        "assumption": "Constant user-provided rate; taxes, fees, and market volatility are excluded.",
    }


def sip_future_value(
    monthly_contribution: float,
    annual_rate_percent: float,
    years: float,
    initial_principal: float = 0.0,
    contribution_timing: str = "end",
) -> dict[str, Any]:
    contribution = _validate_non_negative(monthly_contribution, "monthly_contribution")
    initial = _validate_non_negative(initial_principal, "initial_principal")
    years = _validate_non_negative(years, "years")
    months = int(round(years * 12))
    monthly_rate = float(annual_rate_percent) / 100 / 12
    if contribution_timing not in {"beginning", "end"}:
        raise ValueError("contribution_timing must be 'beginning' or 'end'")

    initial_future = initial * (1 + monthly_rate) ** months
    if months == 0:
        contribution_future = 0.0
    elif monthly_rate == 0:
        contribution_future = contribution * months
    else:
        contribution_future = contribution * (((1 + monthly_rate) ** months - 1) / monthly_rate)
        if contribution_timing == "beginning":
            contribution_future *= 1 + monthly_rate

    future_value = initial_future + contribution_future
    total_contributed = initial + contribution * months
    return {
        "monthly_contribution": round(contribution, 2),
        "initial_principal": round(initial, 2),
        "annual_rate_percent": float(annual_rate_percent),
        "years": years,
        "months": months,
        "contribution_timing": contribution_timing,
        "total_contributed": round(total_contributed, 2),
        "estimated_future_value": round(future_value, 2),
        "estimated_growth": round(future_value - total_contributed, 2),
        "assumption": "Constant user-provided return; taxes, fees, inflation, and volatility are excluded.",
    }


def goal_plan(
    target_amount: float,
    years: float,
    annual_rate_percent: float,
    current_savings: float = 0.0,
    annual_inflation_percent: float = 0.0,
) -> dict[str, Any]:
    target = _validate_non_negative(target_amount, "target_amount")
    years = _validate_non_negative(years, "years")
    current = _validate_non_negative(current_savings, "current_savings")
    inflation = float(annual_inflation_percent) / 100
    if inflation <= -1:
        raise ValueError("annual_inflation_percent must be greater than -100")

    inflation_adjusted_target = target * (1 + inflation) ** years
    months = int(round(years * 12))
    monthly_rate = float(annual_rate_percent) / 100 / 12
    current_future = current * (1 + monthly_rate) ** months
    gap = max(0.0, inflation_adjusted_target - current_future)

    if months == 0:
        monthly_required = gap
    elif monthly_rate == 0:
        monthly_required = gap / months
    else:
        annuity_factor = ((1 + monthly_rate) ** months - 1) / monthly_rate
        monthly_required = gap / annuity_factor

    return {
        "target_amount_today": round(target, 2),
        "inflation_adjusted_target": round(inflation_adjusted_target, 2),
        "current_savings": round(current, 2),
        "years": years,
        "annual_rate_percent": float(annual_rate_percent),
        "annual_inflation_percent": float(annual_inflation_percent),
        "estimated_monthly_contribution_required": round(monthly_required, 2),
        "goal_already_funded": gap == 0,
        "assumption": "Illustrative projection only; returns and inflation are not guaranteed.",
    }
