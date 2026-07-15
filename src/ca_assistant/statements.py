"""Basic financial-statement comparison without accounting conclusions."""

from __future__ import annotations

from typing import Any

import pandas as pd


def summarize_statement(frame: pd.DataFrame, change_flag_percent: float = 25.0) -> dict[str, Any]:
    if frame.empty:
        raise ValueError("Statement data is empty")
    normalized = {str(column).strip().lower(): str(column) for column in frame.columns}
    required = ("line_item", "current_period", "prior_period")
    if not all(column in normalized for column in required):
        raise ValueError(
            "Statement CSV requires line_item, current_period, and prior_period columns"
        )

    result = pd.DataFrame(
        {
            "line_item": frame[normalized["line_item"]].fillna("Unspecified").astype(str),
            "current_period": pd.to_numeric(frame[normalized["current_period"]], errors="coerce"),
            "prior_period": pd.to_numeric(frame[normalized["prior_period"]], errors="coerce"),
        }
    )
    result["absolute_change"] = result["current_period"] - result["prior_period"]
    denominator = result["prior_period"].abs().replace(0, pd.NA)
    result["percent_change"] = (result["absolute_change"] / denominator * 100).astype("Float64")
    result["review_flag"] = ""

    for index, row in result.iterrows():
        flags: list[str] = []
        if pd.isna(row["current_period"]) or pd.isna(row["prior_period"]):
            flags.append("missing numeric value")
        elif float(row["current_period"]) * float(row["prior_period"]) < 0:
            flags.append("sign change")
        if (
            pd.notna(row["percent_change"])
            and abs(float(row["percent_change"])) >= change_flag_percent
        ):
            flags.append(f"change at or above {change_flag_percent:.1f}%")
        result.at[index, "review_flag"] = "; ".join(flags)

    return {
        "rows": result.to_dict(orient="records"),
        "line_item_count": int(len(result)),
        "flagged_line_items": int((result["review_flag"].str.len() > 0).sum()),
        "method": (
            "Period-over-period arithmetic comparison only; no assurance, audit opinion, "
            "valuation, or accounting-policy conclusion."
        ),
    }
