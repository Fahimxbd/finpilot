"""Read-only market data adapters."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
import yfinance as yf

from core.api_guard import APIGuard


@dataclass
class YahooMarketDataProvider:
    guard: APIGuard

    def history(self, symbol: str, period: str = "6mo", interval: str = "1d") -> pd.DataFrame:
        symbol = symbol.strip().upper()
        if not symbol or len(symbol) > 20:
            raise ValueError("A valid ticker symbol is required")

        with self.guard.budget("market_data"):
            frame = yf.download(
                symbol,
                period=period,
                interval=interval,
                auto_adjust=False,
                progress=False,
                threads=False,
                timeout=15,
            )
            if frame.empty:
                raise ValueError(f"No market data returned for {symbol}")
            if isinstance(frame.columns, pd.MultiIndex):
                if symbol in frame.columns.get_level_values(-1):
                    frame = frame.xs(symbol, axis=1, level=-1)
                else:
                    frame.columns = frame.columns.get_level_values(0)
        return frame
