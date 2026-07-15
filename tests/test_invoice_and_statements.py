import pandas as pd

from ca_assistant.invoice_reconciliation import reconcile_invoices
from ca_assistant.statements import summarize_statement


def test_invoice_reconciliation_exact_and_amount_only() -> None:
    invoices = pd.DataFrame(
        {
            "invoice_id": ["INV-1", "INV-2", "INV-3"],
            "amount": [100.0, 75.0, 50.0],
        }
    )
    payments = pd.DataFrame(
        {
            "reference": ["Paid INV-1", "Generic card settlement", "Other"],
            "amount": [100.0, 75.0, 20.0],
        }
    )
    result = reconcile_invoices(invoices, payments)
    assert result["matched_invoices"] == 2
    assert result["invoice_results"][0]["match_method"] == "invoice_id_and_amount"
    assert result["invoice_results"][1]["match_method"] == "unique_amount_only"
    assert result["invoice_results"][2]["status"] == "unmatched"


def test_statement_summary_flags_large_change_and_sign_change() -> None:
    frame = pd.DataFrame(
        {
            "line_item": ["Revenue", "Net income"],
            "current_period": [130, -20],
            "prior_period": [100, 10],
        }
    )
    result = summarize_statement(frame, change_flag_percent=25)
    assert result["flagged_line_items"] == 2
    assert "sign change" in result["rows"][1]["review_flag"]
