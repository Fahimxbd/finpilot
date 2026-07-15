"""Personal expense categorization using transparent local rules."""

from __future__ import annotations

import pandas as pd

from ca_assistant.categorizer import TransactionCategorizer

PERSONAL_EXPENSE_RULES: dict[str, tuple[str, ...]] = {
    "housing": ("rent", "mortgage", "property management"),
    "utilities": ("electric", "electricity", "water", "gas bill", "internet", "mobile bill"),
    "groceries": ("grocery", "supermarket", "market"),
    "dining": ("restaurant", "cafe", "food delivery", "takeaway"),
    "transport": ("uber", "taxi", "bus", "train", "fuel", "petrol", "parking"),
    "health": ("hospital", "clinic", "pharmacy", "doctor", "medical"),
    "education": ("tuition", "course", "book", "exam fee"),
    "entertainment": ("cinema", "game", "streaming", "netflix", "spotify"),
    "income": ("salary", "payroll", "interest credit", "refund"),
}


def categorize_expenses(frame: pd.DataFrame) -> pd.DataFrame:
    return TransactionCategorizer(rules=PERSONAL_EXPENSE_RULES).categorize_frame(frame)
