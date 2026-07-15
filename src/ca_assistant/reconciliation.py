"""Reconciliation notes and anomaly flags for human review."""

from __future__ import annotations

from typing import Any

import pandas as pd


def flag_anomalies(frame: pd.DataFrame) -> pd.DataFrame:
    required = {"description", "amount", "category", "confidence"}
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(f"Categorized data is missing columns: {sorted(missing)}")

    result = frame.copy()
    result["anomaly_reasons"] = ""
    absolute_amounts = result["amount"].abs()
    non_zero = absolute_amounts[absolute_amounts > 0]
    median = float(non_zero.median()) if not non_zero.empty else 0.0
    high_value_threshold = max(
        median * 5, float(non_zero.quantile(0.95)) if len(non_zero) >= 5 else 0.0
    )

    reasons: list[list[str]] = [[] for _ in range(len(result))]
    duplicate_subset = [
        column for column in ("date", "description", "amount") if column in result.columns
    ]
    duplicate_mask = (
        result.duplicated(subset=duplicate_subset, keep=False)
        if duplicate_subset
        else pd.Series(False, index=result.index)
    )

    for position, (_, row) in enumerate(result.iterrows()):
        if not str(row.get("description", "")).strip():
            reasons[position].append("missing description")
        if bool(duplicate_mask.iloc[position]):
            reasons[position].append("possible duplicate")
        if high_value_threshold > 0 and abs(float(row["amount"])) >= high_value_threshold:
            reasons[position].append("unusually high value")
        if str(row["category"]) == "uncategorized":
            reasons[position].append("uncategorized")
        if float(row["confidence"]) < 0.75:
            reasons[position].append("low classification confidence")
        if "date" in result.columns and pd.isna(row.get("date")):
            reasons[position].append("missing or invalid date")

    result["anomaly_reasons"] = ["; ".join(items) for items in reasons]
    result["needs_human_review"] = result["anomaly_reasons"].str.len() > 0
    return result


def reconciliation_summary(frame: pd.DataFrame) -> dict[str, Any]:
    reviewed = flag_anomalies(frame)
    inflow = float(reviewed.loc[reviewed["amount"] > 0, "amount"].sum())
    outflow = float(-reviewed.loc[reviewed["amount"] < 0, "amount"].sum())
    categories = (
        reviewed.groupby("category", dropna=False)["amount"]
        .agg(transaction_count="count", net_amount="sum")
        .reset_index()
        .to_dict(orient="records")
    )
    return {
        "transaction_count": int(len(reviewed)),
        "total_inflow": round(inflow, 2),
        "total_outflow": round(outflow, 2),
        "net_cash_movement": round(inflow - outflow, 2),
        "transactions_needing_review": int(reviewed["needs_human_review"].sum()),
        "category_summary": categories,
        "reconciliation_notes": [
            "Confirm the opening and closing balances against the source statement.",
            "Review all duplicate, high-value, uncategorized, and low-confidence rows.",
            "Verify jurisdiction-specific tax treatment with a qualified professional.",
            "No filing, posting, payment, or ledger write-back was performed.",
        ],
    }


def draft_tax_note(frame: pd.DataFrame, jurisdiction: str = "unspecified") -> str:
    review_count = int(flag_anomalies(frame)["needs_human_review"].sum())
    return (
        f"Draft review note — jurisdiction: {jurisdiction}. "
        f"The dataset contains {len(frame)} transactions, of which {review_count} require human review. "
        "Categories are provisional and should be checked against source invoices, contracts, and the "
        "applicable accounting and tax rules. FinPilot has not calculated a tax liability, submitted a "
        "return, posted entries, or made a legal determination."
    )
