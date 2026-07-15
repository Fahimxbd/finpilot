"""Trading-insight orchestration. This package has no order-execution code."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from core.api_guard import APIGuard
from core.disclaimer import disclaimed
from trading_insights.data import YahooMarketDataProvider
from trading_insights.indicators import latest_indicator_snapshot, plain_language_summary
from trading_insights.portfolio import analyze_portfolio_csv
from trading_insights.sentiment import RSSNewsDigest


@dataclass
class TradingInsightsService:
    guard: APIGuard

    @disclaimed("trading")
    def analyze_symbol(
        self,
        symbol: str,
        *,
        period: str = "6mo",
        interval: str = "1d",
        include_news: bool = False,
        news_limit: int = 8,
    ) -> dict[str, Any]:
        provider = YahooMarketDataProvider(self.guard)
        frame = provider.history(symbol, period=period, interval=interval)
        snapshot = latest_indicator_snapshot(frame)
        result: dict[str, Any] = {
            "symbol": symbol.upper(),
            "period": period,
            "interval": interval,
            "indicator_snapshot": snapshot,
            "summary": plain_language_summary(snapshot),
            "execution_capability": "none/read-only",
        }
        if include_news:
            result["news_digest"] = RSSNewsDigest(self.guard).fetch(
                f"{symbol} stock company",
                limit=news_limit,
            )
        return result

    @disclaimed("portfolio")
    def analyze_portfolio_csv(self, path: str | Path) -> dict[str, Any]:
        result = analyze_portfolio_csv(path)
        result["execution_capability"] = "none/read-only"
        return result
