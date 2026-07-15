import numpy as np
import pandas as pd

from trading_insights.indicators import (
    enrich_indicators,
    latest_indicator_snapshot,
    plain_language_summary,
)


def sample_prices(rows: int = 80) -> pd.DataFrame:
    close = np.linspace(100, 130, rows) + np.sin(np.arange(rows))
    return pd.DataFrame(
        {
            "Open": close - 0.5,
            "High": close + 1.0,
            "Low": close - 1.0,
            "Close": close,
            "Volume": np.arange(rows) + 1000,
        },
        index=pd.date_range("2025-01-01", periods=rows, freq="D"),
    )


def test_indicator_columns_are_created() -> None:
    enriched = enrich_indicators(sample_prices())
    for column in ["SMA20", "SMA50", "RSI14", "MACD", "MACDSignal", "Volatility20Annualized"]:
        assert column in enriched.columns


def test_snapshot_and_summary_are_descriptive() -> None:
    snapshot = latest_indicator_snapshot(sample_prices())
    notes = plain_language_summary(snapshot)
    assert 0 <= snapshot["rsi14"] <= 100
    assert snapshot["rows_analyzed"] == 80
    assert any("do not predict returns" in note for note in notes)
