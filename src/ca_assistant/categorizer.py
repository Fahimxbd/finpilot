"""Transaction normalization and conservative categorization."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pandas as pd

from core.llm_client import LocalOllamaClient

DEFAULT_RULES: dict[str, tuple[str, ...]] = {
    "income": ("salary", "payroll", "client payment", "invoice paid", "interest credit"),
    "rent_and_utilities": (
        "rent",
        "electric",
        "electricity",
        "water bill",
        "gas bill",
        "internet",
    ),
    "software_and_subscriptions": (
        "hosting",
        "software",
        "subscription",
        "github",
        "microsoft",
        "google workspace",
    ),
    "travel_and_transport": (
        "uber",
        "lyft",
        "taxi",
        "bus",
        "train",
        "flight",
        "fuel",
        "petrol",
    ),
    "food_and_meals": ("restaurant", "cafe", "food", "grocery", "supermarket", "meal"),
    "bank_and_finance_fees": (
        "bank fee",
        "service charge",
        "late fee",
        "atm fee",
        "transfer fee",
    ),
    "taxes_and_government": ("tax", "vat", "gst", "government fee", "customs"),
    "office_and_supplies": ("stationery", "office supply", "printer", "paper", "courier"),
    "professional_services": ("consulting", "legal", "accounting", "audit", "freelancer"),
    "healthcare": ("hospital", "clinic", "pharmacy", "doctor", "medical"),
}

COLUMN_ALIASES: dict[str, tuple[str, ...]] = {
    "date": ("date", "transaction date", "posted date", "value date"),
    "description": ("description", "details", "narration", "memo", "merchant", "transaction"),
    "amount": ("amount", "net amount", "transaction amount"),
    "debit": ("debit", "withdrawal", "money out", "paid out"),
    "credit": ("credit", "deposit", "money in", "paid in"),
    "balance": ("balance", "running balance", "closing balance"),
}


def _normalized_column_name(name: Any) -> str:
    return re.sub(r"\s+", " ", str(name).strip().lower())


def _find_column(frame: pd.DataFrame, canonical: str) -> str | None:
    normalized = {_normalized_column_name(column): str(column) for column in frame.columns}
    for alias in COLUMN_ALIASES[canonical]:
        if alias in normalized:
            return normalized[alias]
    return None


def normalize_transactions(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        raise ValueError("Transaction data is empty")
    date_col = _find_column(frame, "date")
    description_col = _find_column(frame, "description")
    amount_col = _find_column(frame, "amount")
    debit_col = _find_column(frame, "debit")
    credit_col = _find_column(frame, "credit")
    balance_col = _find_column(frame, "balance")

    if not description_col:
        raise ValueError("Could not identify a description/narration column")
    if not amount_col and not (debit_col or credit_col):
        raise ValueError("Could not identify amount or debit/credit columns")

    output = pd.DataFrame(index=frame.index)
    output["date"] = pd.to_datetime(frame[date_col], errors="coerce") if date_col else pd.NaT
    output["description"] = frame[description_col].fillna("").astype(str).str.strip()

    if amount_col:
        output["amount"] = pd.to_numeric(frame[amount_col], errors="coerce").fillna(0.0)
    else:
        debit = (
            pd.to_numeric(frame[debit_col], errors="coerce").fillna(0.0)
            if debit_col
            else pd.Series(0.0, index=frame.index)
        )
        credit = (
            pd.to_numeric(frame[credit_col], errors="coerce").fillna(0.0)
            if credit_col
            else pd.Series(0.0, index=frame.index)
        )
        output["amount"] = credit.abs() - debit.abs()

    if balance_col:
        output["balance"] = pd.to_numeric(frame[balance_col], errors="coerce")
    output["source_row"] = frame.index.astype(str)
    return output.reset_index(drop=True)


def keyword_category(
    description: str,
    rules: dict[str, tuple[str, ...]] | None = None,
) -> tuple[str, float, str]:
    text = description.lower()
    matches: list[tuple[str, str]] = []
    for category, keywords in (rules or DEFAULT_RULES).items():
        for keyword in keywords:
            if keyword in text:
                matches.append((category, keyword))
    if not matches:
        return "uncategorized", 0.0, "No keyword rule matched"
    categories = {category for category, _ in matches}
    best_category, best_keyword = max(matches, key=lambda item: len(item[1]))
    confidence = 0.95 if len(categories) == 1 else 0.65
    return best_category, confidence, f"Matched keyword '{best_keyword}'"


@dataclass
class TransactionCategorizer:
    rules: dict[str, tuple[str, ...]] = field(default_factory=lambda: DEFAULT_RULES.copy())
    llm_client: LocalOllamaClient | None = None

    def categorize_description(self, description: str, use_llm: bool = False) -> dict[str, Any]:
        category, confidence, reason = keyword_category(description, self.rules)
        method = "keyword"
        if category == "uncategorized" and use_llm and self.llm_client:
            prompt = (
                "Classify this financial transaction into exactly one category from the list below. "
                "Return strict JSON with keys category, confidence, reason. "
                "Do not provide tax advice.\n"
                f"Categories: {sorted(self.rules)} + ['uncategorized']\n"
                f"Transaction: {description[:500]}"
            )
            response = self.llm_client.generate(prompt, max_output_tokens=120)
            try:
                parsed = json.loads(response.text)
                proposed = str(parsed.get("category", "uncategorized"))
                if proposed not in self.rules and proposed != "uncategorized":
                    proposed = "uncategorized"
                category = proposed
                confidence = min(0.8, max(0.0, float(parsed.get("confidence", 0.5))))
                reason = str(parsed.get("reason", "Local LLM classification"))[:300]
                method = "local_llm"
            except (json.JSONDecodeError, TypeError, ValueError):
                reason = "Local LLM response was invalid; retained uncategorized status"
                method = "keyword_fallback"
        return {
            "category": category,
            "confidence": round(confidence, 2),
            "reason": reason,
            "method": method,
            "needs_human_review": category == "uncategorized" or confidence < 0.75,
        }

    def categorize_frame(self, frame: pd.DataFrame, use_llm: bool = False) -> pd.DataFrame:
        normalized = normalize_transactions(frame)
        classifications = [
            self.categorize_description(description, use_llm=use_llm)
            for description in normalized["description"]
        ]
        classified = pd.DataFrame(classifications)
        return pd.concat([normalized, classified], axis=1)

    def categorize_csv(self, input_path: str | Path, use_llm: bool = False) -> pd.DataFrame:
        frame = pd.read_csv(input_path)
        return self.categorize_frame(frame, use_llm=use_llm)
