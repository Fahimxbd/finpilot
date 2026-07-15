import pytest

from investor_tools.calculators import compound_growth, goal_plan, sip_future_value
from investor_tools.service import InvestorToolsService


def test_zero_rate_sip_is_total_contributions() -> None:
    result = sip_future_value(100, 0, 1, initial_principal=500)
    assert result["estimated_future_value"] == 1700
    assert result["estimated_growth"] == 0


def test_compound_growth() -> None:
    result = compound_growth(1000, 12, 1, compounds_per_year=12)
    assert result["estimated_future_value"] == pytest.approx(1126.83, abs=0.01)


def test_goal_plan_zero_rate() -> None:
    result = goal_plan(1200, years=1, annual_rate_percent=0)
    assert result["estimated_monthly_contribution_required"] == 100


def test_service_adds_disclaimer() -> None:
    output = InvestorToolsService().calculate_sip(100, 5, 2)
    assert "disclaimer" in output
    assert "advice" in output["disclaimer"]
