"""Retail-investor educational tools with mandatory disclaimers."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from core.disclaimer import disclaimed
from core.llm_client import LocalOllamaClient
from investor_tools.calculators import compound_growth, goal_plan, sip_future_value
from investor_tools.expenses import categorize_expenses
from investor_tools.pdf_summary import summarize_research_pdf


@dataclass
class InvestorToolsService:
    llm_client: LocalOllamaClient | None = None

    @disclaimed("investment")
    def calculate_sip(
        self,
        monthly_contribution: float,
        annual_rate_percent: float,
        years: float,
        initial_principal: float = 0.0,
    ) -> dict[str, Any]:
        return sip_future_value(
            monthly_contribution,
            annual_rate_percent,
            years,
            initial_principal,
        )

    @disclaimed("investment")
    def calculate_compound_growth(
        self,
        principal: float,
        annual_rate_percent: float,
        years: float,
    ) -> dict[str, Any]:
        return compound_growth(principal, annual_rate_percent, years)

    @disclaimed("investment")
    def plan_goal(
        self,
        target_amount: float,
        years: float,
        annual_rate_percent: float,
        current_savings: float = 0.0,
        annual_inflation_percent: float = 0.0,
    ) -> dict[str, Any]:
        return goal_plan(
            target_amount,
            years,
            annual_rate_percent,
            current_savings,
            annual_inflation_percent,
        )

    @disclaimed("investment")
    def summarize_pdf(
        self,
        path: str | Path,
        *,
        max_pages: int = 50,
        sentence_count: int = 8,
        use_llm: bool = False,
    ) -> dict[str, Any]:
        result = summarize_research_pdf(
            path,
            max_pages=max_pages,
            sentence_count=sentence_count,
        )
        if use_llm:
            if not self.llm_client:
                raise RuntimeError("A local LLM client is required when use_llm=True")
            source = "\n".join(result["summary_sentences"])
            prompt = (
                "Rewrite the research excerpts below into a concise plain-language summary. "
                "Preserve uncertainty, do not invent numbers, and do not give investment advice.\n\n"
                f"{source[:12000]}"
            )
            response = self.llm_client.generate(prompt, max_output_tokens=600)
            result["plain_language_summary"] = response.text
            result["plain_language_method"] = "optional local Ollama rewrite"
        else:
            result["plain_language_summary"] = " ".join(result["summary_sentences"])
            result["plain_language_method"] = (
                "deterministic extractive fallback; enable local Ollama for rewriting"
            )
        return result

    @disclaimed("investment")
    def categorize_expense_csv(self, path: str | Path) -> dict[str, Any]:
        categorized = categorize_expenses(pd.read_csv(path))
        return {
            "rows": categorized.to_dict(orient="records"),
            "automation_scope": "read-only categorization for personal review",
        }
