import pandas as pd

from trading_insights.portfolio import analyze_portfolio


def test_portfolio_concentration_flags() -> None:
    frame = pd.DataFrame(
        {
            "ticker": ["AAA", "BBB", "CCC"],
            "value": [700, 200, 100],
            "sector": ["Tech", "Tech", "Bonds"],
        }
    )
    result = analyze_portfolio(frame)
    flag_types = {flag["type"] for flag in result["risk_flags"]}
    assert result["largest_position_weight"] == 0.7
    assert "single_position_concentration" in flag_types
    assert "asset_class_concentration" in flag_types
