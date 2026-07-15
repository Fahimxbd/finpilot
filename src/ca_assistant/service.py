"""Accounting workflow service with mandatory disclaimers and no write-back capability."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from ca_assistant.categorizer import TransactionCategorizer
from ca_assistant.invoice_reconciliation import reconcile_invoices
from ca_assistant.reconciliation import draft_tax_note, flag_anomalies, reconciliation_summary
from ca_assistant.statements import summarize_statement
from core.disclaimer import disclaimed


@dataclass
class CAAssistantService:
    categorizer: TransactionCategorizer

    @disclaimed("tax")
    def process_csv(
        self,
        path: str | Path,
        *,
        use_llm: bool = False,
        jurisdiction: str = "unspecified",
    ) -> dict[str, Any]:
        categorized = self.categorizer.categorize_csv(path, use_llm=use_llm)
        reviewed = flag_anomalies(categorized)
        return {
            "rows": reviewed.to_dict(orient="records"),
            "summary": reconciliation_summary(reviewed),
            "draft_tax_note": draft_tax_note(reviewed, jurisdiction=jurisdiction),
            "automation_scope": "read-only analysis and drafting; no ledger posting or tax filing",
        }

    @disclaimed("tax")
    def process_frame(
        self,
        frame: pd.DataFrame,
        *,
        use_llm: bool = False,
        jurisdiction: str = "unspecified",
    ) -> dict[str, Any]:
        categorized = self.categorizer.categorize_frame(frame, use_llm=use_llm)
        reviewed = flag_anomalies(categorized)
        return {
            "rows": reviewed.to_dict(orient="records"),
            "summary": reconciliation_summary(reviewed),
            "draft_tax_note": draft_tax_note(reviewed, jurisdiction=jurisdiction),
            "automation_scope": "read-only analysis and drafting; no ledger posting or tax filing",
        }

    @disclaimed("tax")
    def reconcile_invoice_csvs(
        self,
        invoice_path: str | Path,
        payment_path: str | Path,
        *,
        amount_tolerance: float = 0.01,
    ) -> dict[str, Any]:
        invoices = pd.read_csv(invoice_path)
        payments = pd.read_csv(payment_path)
        return reconcile_invoices(invoices, payments, amount_tolerance=amount_tolerance)

    @disclaimed("tax")
    def summarize_statement_csv(
        self,
        path: str | Path,
        *,
        change_flag_percent: float = 25.0,
    ) -> dict[str, Any]:
        return summarize_statement(
            pd.read_csv(path),
            change_flag_percent=change_flag_percent,
        )
