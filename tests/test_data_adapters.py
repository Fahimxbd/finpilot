from pathlib import Path
from types import SimpleNamespace

import pandas as pd
import pytest

from core.api_guard import APIGuard
from core.settings import LimitsConfig, ServiceLimit
from trading_insights.data import YahooMarketDataProvider
from trading_insights.sentiment import RSSNewsDigest


def guard(tmp_path: Path) -> APIGuard:
    return APIGuard(
        LimitsConfig(
            max_monthly_api_calls=10,
            max_tokens_per_run=100,
            near_limit_ratio=0.8,
            min_seconds_between_calls=0,
            queue_on_throttle=True,
            usage_file=str(tmp_path / "usage.json"),
            audit_file=str(tmp_path / "audit.jsonl"),
            services={
                "market_data": ServiceLimit(monthly_calls=5),
                "rss_news": ServiceLimit(monthly_calls=5),
            },
        )
    )


def ohlcv() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "Open": [1.0, 2.0],
            "High": [2.0, 3.0],
            "Low": [0.5, 1.5],
            "Close": [1.5, 2.5],
            "Volume": [100, 200],
        }
    )


def test_yahoo_provider_uses_guard_and_returns_frame(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr("trading_insights.data.yf.download", lambda *args, **kwargs: ohlcv())
    api_guard = guard(tmp_path)
    result = YahooMarketDataProvider(api_guard).history("abc")
    assert list(result["Close"]) == [1.5, 2.5]
    month = api_guard.current_month()
    assert api_guard.snapshot()["usage"]["months"][month]["calls"] == 1


def test_empty_market_result_rolls_back_budget(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr("trading_insights.data.yf.download", lambda *args, **kwargs: pd.DataFrame())
    api_guard = guard(tmp_path)
    with pytest.raises(ValueError):
        YahooMarketDataProvider(api_guard).history("abc")
    month = api_guard.current_month()
    assert api_guard.snapshot()["usage"]["months"][month]["calls"] == 0


def test_rss_digest_with_mocked_feed(tmp_path, monkeypatch) -> None:
    parsed = SimpleNamespace(
        bozo=False,
        entries=[
            {"title": "Company reports strong profit growth", "link": "x", "published": "today"},
            {"title": "Company faces lawsuit risk", "link": "y", "published": "today"},
        ],
    )
    monkeypatch.setattr("trading_insights.sentiment.feedparser.parse", lambda url: parsed)
    result = RSSNewsDigest(guard(tmp_path)).fetch("ABC", limit=2)
    assert result["headline_count"] == 2
    assert result["headlines"][0]["sentiment"] == "positive"
    assert result["headlines"][1]["sentiment"] == "negative"
