"""Read-only invoice-to-payment matching for human review."""

from __future__ import annotations

import re
from typing import Any

import pandas as pd


def _column(frame: pd.DataFrame, aliases: tuple[str, ...]) -> str | None:
    normalized = {str(column).strip().lower(): str(column) for column in frame.columns}
    for alias in aliases:
        if alias in normalized:
            return normalized[alias]
    return None


def reconcile_invoices(
    invoices: pd.DataFrame,
    payments: pd.DataFrame,
    *,
    amount_tolerance: float = 0.01,
) -> dict[str, Any]:
    if invoices.empty or payments.empty:
        raise ValueError("Invoice and payment datasets must both contain rows")
    if amount_tolerance < 0:
        raise ValueError("amount_tolerance cannot be negative")

    invoice_id_col = _column(invoices, ("invoice_id", "invoice id", "invoice", "reference"))
    invoice_amount_col = _column(invoices, ("amount", "invoice_amount", "invoice amount", "total"))
    payment_ref_col = _column(payments, ("reference", "description", "memo", "narration"))
    payment_amount_col = _column(payments, ("amount", "payment_amount", "payment amount", "credit"))
    if not all((invoice_id_col, invoice_amount_col, payment_ref_col, payment_amount_col)):
        raise ValueError("Could not identify required invoice/payment columns")

    invoice_rows = invoices.copy().reset_index(drop=True)
    payment_rows = payments.copy().reset_index(drop=True)
    invoice_rows["_amount"] = pd.to_numeric(invoice_rows[invoice_amount_col], errors="coerce")
    payment_rows["_amount"] = pd.to_numeric(payment_rows[payment_amount_col], errors="coerce")
    payment_rows["_used"] = False

    results: list[dict[str, Any]] = []
    for invoice_index, invoice in invoice_rows.iterrows():
        invoice_id = str(invoice[invoice_id_col]).strip()
        invoice_amount = invoice["_amount"]
        candidates: list[tuple[int, str]] = []
        if pd.notna(invoice_amount):
            for payment_index, payment in payment_rows.loc[~payment_rows["_used"]].iterrows():
                payment_reference = str(payment[payment_ref_col])
                payment_amount = payment["_amount"]
                if pd.isna(payment_amount):
                    continue
                amount_matches = (
                    abs(float(payment_amount) - float(invoice_amount)) <= amount_tolerance
                )
                reference_matches = bool(
                    invoice_id
                    and re.search(re.escape(invoice_id), payment_reference, flags=re.IGNORECASE)
                )
                if amount_matches and reference_matches:
                    candidates.append((payment_index, "invoice_id_and_amount"))

            if not candidates:
                amount_only = [
                    payment_index
                    for payment_index, payment in payment_rows.loc[
                        ~payment_rows["_used"]
                    ].iterrows()
                    if pd.notna(payment["_amount"])
                    and abs(float(payment["_amount"]) - float(invoice_amount)) <= amount_tolerance
                ]
                if len(amount_only) == 1:
                    candidates.append((amount_only[0], "unique_amount_only"))

        if len(candidates) == 1:
            payment_index, method = candidates[0]
            payment_rows.loc[payment_index, "_used"] = True
            results.append(
                {
                    "invoice_row": int(invoice_index),
                    "invoice_id": invoice_id,
                    "invoice_amount": None if pd.isna(invoice_amount) else float(invoice_amount),
                    "status": "matched",
                    "payment_row": int(payment_index),
                    "match_method": method,
                    "needs_human_review": method != "invoice_id_and_amount",
                }
            )
        else:
            results.append(
                {
                    "invoice_row": int(invoice_index),
                    "invoice_id": invoice_id,
                    "invoice_amount": None if pd.isna(invoice_amount) else float(invoice_amount),
                    "status": "ambiguous" if len(candidates) > 1 else "unmatched",
                    "payment_row": None,
                    "match_method": None,
                    "needs_human_review": True,
                }
            )

    unmatched_payment_rows = [
        int(index) for index, row in payment_rows.iterrows() if not bool(row["_used"])
    ]
    return {
        "invoice_results": results,
        "matched_invoices": sum(item["status"] == "matched" for item in results),
        "unmatched_or_ambiguous_invoices": sum(item["status"] != "matched" for item in results),
        "unmatched_payment_rows": unmatched_payment_rows,
        "automation_scope": "read-only candidate matching; no posting, settlement, or write-back",
    }
