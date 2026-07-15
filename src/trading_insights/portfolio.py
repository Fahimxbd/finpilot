"""Transparent portfolio concentration and exposure flags."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd


def _find_column(frame: pd.DataFrame, aliases: tuple[str, ...]) -> str | None:
    normalized = {str(column).strip().lower(): str(column) for column in frame.columns}
    for alias in aliases:
        if alias in normalized:
            return normalized[alias]
    return None


def analyze_portfolio(frame: pd.DataFrame) -> dict[str, Any]:
    if frame.empty:
        raise ValueError("Holdings data is empty")

    symbol_column = _find_column(frame, ("symbol", "ticker", "security", "name"))
    value_column = _find_column(frame, ("market_value", "market value", "value", "position_value"))
    asset_class_column = _find_column(frame, ("asset_class", "asset class", "category", "sector"))
    if not symbol_column or not value_column:
        raise ValueError("Holdings CSV needs symbol/ticker and market_value/value columns")

    holdings = pd.DataFrame(
        {
            "symbol": frame[symbol_column].fillna("UNKNOWN").astype(str).str.strip(),
            "market_value": pd.to_numeric(frame[value_column], errors="coerce"),
        }
    ).dropna(subset=["market_value"])
    if asset_class_column:
        holdings["asset_class"] = frame.loc[holdings.index, asset_class_column].fillna(
            "Unspecified"
        )

    gross_exposure = float(holdings["market_value"].abs().sum())
    net_exposure = float(holdings["market_value"].sum())
    if gross_exposure <= 0:
        raise ValueError("Gross portfolio exposure must be greater than zero")

    holdings["gross_weight"] = holdings["market_value"].abs() / gross_exposure
    holdings = holdings.sort_values("gross_weight", ascending=False).reset_index(drop=True)
    hhi = float((holdings["gross_weight"] ** 2).sum())
    top_one = float(holdings["gross_weight"].iloc[0])
    top_three = float(holdings["gross_weight"].head(3).sum())

    flags: list[dict[str, Any]] = []
    if top_one >= 0.25:
        flags.append(
            {
                "type": "single_position_concentration",
                "severity": "high" if top_one >= 0.40 else "moderate",
                "detail": f"Largest position represents {top_one:.1%} of gross exposure.",
            }
        )
    if top_three >= 0.60:
        flags.append(
            {
                "type": "top_three_concentration",
                "severity": "moderate",
                "detail": f"Top three positions represent {top_three:.1%} of gross exposure.",
            }
        )
    if (holdings["market_value"] < 0).any():
        short_weight = float(
            holdings.loc[holdings["market_value"] < 0, "market_value"].abs().sum() / gross_exposure
        )
        flags.append(
            {
                "type": "short_exposure",
                "severity": "informational",
                "detail": f"Short positions represent {short_weight:.1%} of gross exposure.",
            }
        )

    asset_class_summary: list[dict[str, Any]] = []
    if "asset_class" in holdings:
        grouped = (
            holdings.groupby("asset_class", dropna=False)["gross_weight"]
            .sum()
            .sort_values(ascending=False)
        )
        asset_class_summary = [
            {"asset_class": str(name), "gross_weight": round(float(weight), 6)}
            for name, weight in grouped.items()
        ]
        if not grouped.empty and float(grouped.iloc[0]) >= 0.70:
            flags.append(
                {
                    "type": "asset_class_concentration",
                    "severity": "moderate",
                    "detail": (
                        f"Largest asset-class/sector group represents {float(grouped.iloc[0]):.1%} "
                        "of gross exposure."
                    ),
                }
            )

    return {
        "position_count": int(len(holdings)),
        "gross_exposure": round(gross_exposure, 2),
        "net_exposure": round(net_exposure, 2),
        "largest_position_weight": round(top_one, 6),
        "top_three_weight": round(top_three, 6),
        "concentration_hhi": round(hhi, 6),
        "effective_position_count": round(1 / hhi, 2) if hhi else 0.0,
        "risk_flags": flags,
        "asset_class_summary": asset_class_summary,
        "top_positions": holdings.head(10).to_dict(orient="records"),
        "method": "Position-value concentration analysis; no forecast or recommendation.",
    }


def analyze_portfolio_csv(path: str | Path) -> dict[str, Any]:
    return analyze_portfolio(pd.read_csv(path))
