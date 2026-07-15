"""Local technical-indicator calculations. No trade recommendations are produced."""

from __future__ import annotations

import math
from typing import Any

import numpy as np
import pandas as pd

REQUIRED_COLUMNS = {"Open", "High", "Low", "Close", "Volume"}


def validate_ohlcv(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        raise ValueError("OHLCV data is empty")
    missing = REQUIRED_COLUMNS.difference(frame.columns)
    if missing:
        raise ValueError(f"OHLCV data is missing columns: {sorted(missing)}")
    clean = frame.copy()
    for column in REQUIRED_COLUMNS:
        clean[column] = pd.to_numeric(clean[column], errors="coerce")
    clean = clean.dropna(subset=["Close"]).sort_index()
    if len(clean) < 35:
        raise ValueError("At least 35 price rows are required for stable indicator output")
    return clean


def rsi(close: pd.Series, period: int = 14) -> pd.Series:
    delta = close.diff()
    gains = delta.clip(lower=0)
    losses = -delta.clip(upper=0)
    avg_gain = gains.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    avg_loss = losses.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    relative_strength = avg_gain / avg_loss.replace(0, np.nan)
    result = 100 - (100 / (1 + relative_strength))
    return result.fillna(100.0).clip(0, 100)


def macd(close: pd.Series) -> tuple[pd.Series, pd.Series, pd.Series]:
    ema_fast = close.ewm(span=12, adjust=False).mean()
    ema_slow = close.ewm(span=26, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=9, adjust=False).mean()
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram


def enrich_indicators(frame: pd.DataFrame) -> pd.DataFrame:
    data = validate_ohlcv(frame)
    data["SMA20"] = data["Close"].rolling(20).mean()
    data["SMA50"] = data["Close"].rolling(50).mean()
    data["EMA12"] = data["Close"].ewm(span=12, adjust=False).mean()
    data["EMA26"] = data["Close"].ewm(span=26, adjust=False).mean()
    data["RSI14"] = rsi(data["Close"], 14)
    data["MACD"], data["MACDSignal"], data["MACDHistogram"] = macd(data["Close"])
    returns = data["Close"].pct_change()
    data["Volatility20Annualized"] = returns.rolling(20).std() * math.sqrt(252)
    return data


def _number(value: Any, digits: int = 4) -> float | None:
    if value is None or pd.isna(value):
        return None
    return round(float(value), digits)


def latest_indicator_snapshot(frame: pd.DataFrame) -> dict[str, Any]:
    data = enrich_indicators(frame)
    latest = data.iloc[-1]
    previous = data.iloc[-2]
    close = float(latest["Close"])
    one_day_change = (close / float(previous["Close"]) - 1) * 100
    return {
        "as_of": str(data.index[-1]),
        "close": _number(close, 4),
        "one_day_change_percent": _number(one_day_change, 2),
        "sma20": _number(latest["SMA20"], 4),
        "sma50": _number(latest["SMA50"], 4),
        "ema12": _number(latest["EMA12"], 4),
        "ema26": _number(latest["EMA26"], 4),
        "rsi14": _number(latest["RSI14"], 2),
        "macd": _number(latest["MACD"], 4),
        "macd_signal": _number(latest["MACDSignal"], 4),
        "macd_histogram": _number(latest["MACDHistogram"], 4),
        "volatility20_annualized": _number(latest["Volatility20Annualized"], 4),
        "rows_analyzed": len(data),
    }


def plain_language_summary(snapshot: dict[str, Any]) -> list[str]:
    close = snapshot["close"]
    sma20 = snapshot["sma20"]
    sma50 = snapshot["sma50"]
    rsi_value = snapshot["rsi14"]
    macd_value = snapshot["macd"]
    signal = snapshot["macd_signal"]
    volatility = snapshot["volatility20_annualized"]

    notes: list[str] = []
    if sma20 is not None:
        position = "above" if close > sma20 else "below"
        notes.append(f"The latest close is {position} the 20-period moving average.")
    if sma20 is not None and sma50 is not None:
        relation = "above" if sma20 > sma50 else "below"
        notes.append(f"The 20-period average is {relation} the 50-period average.")
    if rsi_value is not None:
        if rsi_value >= 70:
            zone = "elevated"
        elif rsi_value <= 30:
            zone = "depressed"
        else:
            zone = "neutral"
        notes.append(f"RSI(14) is {rsi_value:.2f}, which is in a {zone} range.")
    if macd_value is not None and signal is not None:
        relation = "above" if macd_value > signal else "below"
        notes.append(f"MACD is {relation} its signal line.")
    if volatility is not None:
        notes.append(
            f"Recent annualized 20-period volatility is approximately {volatility * 100:.1f}%."
        )
    notes.append(
        "These observations describe historical price behavior; they do not predict returns."
    )
    return notes
