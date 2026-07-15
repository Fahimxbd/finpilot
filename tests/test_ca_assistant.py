import pandas as pd

from ca_assistant.categorizer import TransactionCategorizer, normalize_transactions
from ca_assistant.reconciliation import flag_anomalies
from ca_assistant.service import CAAssistantService
from core.disclaimer import MASTER_DISCLAIMER


def raw_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "Transaction Date": ["2026-01-01", "2026-01-02", "2026-01-02"],
            "Narration": ["Client payment invoice paid", "Unknown ZXQ", "Unknown ZXQ"],
            "Debit": [0, 50, 50],
            "Credit": [500, 0, 0],
        }
    )


def test_normalizes_debit_credit_to_signed_amount() -> None:
    normalized = normalize_transactions(raw_frame())
    assert normalized["amount"].tolist() == [500, -50, -50]


def test_keyword_and_review_flags() -> None:
    categorized = TransactionCategorizer().categorize_frame(raw_frame())
    reviewed = flag_anomalies(categorized)
    assert categorized.loc[0, "category"] == "income"
    assert categorized.loc[1, "category"] == "uncategorized"
    assert reviewed.loc[1, "needs_human_review"]
    assert "possible duplicate" in reviewed.loc[1, "anomaly_reasons"]


def test_reconciliation_and_service_disclaimer() -> None:
    service = CAAssistantService(TransactionCategorizer())
    output = service.process_frame(raw_frame())
    assert output["disclaimer"] == MASTER_DISCLAIMER
    summary = output["data"]["summary"]
    assert summary["transaction_count"] == 3
    assert summary["total_inflow"] == 500
    assert summary["total_outflow"] == 100
