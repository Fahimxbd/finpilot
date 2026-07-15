"""Command-line interface for FinPilot."""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
from typing import Any

import pandas as pd

from ca_assistant.categorizer import TransactionCategorizer
from ca_assistant.service import CAAssistantService
from core.api_guard import APIGuard
from core.disclaimer import MASTER_DISCLAIMER
from core.llm_client import LocalOllamaClient
from investor_tools.service import InvestorToolsService
from trading_insights.service import TradingInsightsService


def print_json(payload: Any) -> None:
    print(json.dumps(payload, indent=2, ensure_ascii=False, default=str))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="finpilot",
        description="Educational, read-only financial operations toolkit.",
    )
    parser.add_argument("--verbose", action="store_true", help="Enable informational logs")
    subparsers = parser.add_subparsers(dest="command", required=True)

    trading = subparsers.add_parser("trading", help="Summarize local technical indicators")
    trading.add_argument("symbol")
    trading.add_argument("--period", default="6mo")
    trading.add_argument("--interval", default="1d")
    trading.add_argument("--news", action="store_true")
    trading.add_argument("--news-limit", type=int, default=8)

    portfolio = subparsers.add_parser("portfolio", help="Flag concentration in a holdings CSV")
    portfolio.add_argument("csv_path", type=Path)

    categorize = subparsers.add_parser("categorize", help="Categorize a bank/ledger CSV")
    categorize.add_argument("csv_path", type=Path)
    categorize.add_argument("--output", type=Path)
    categorize.add_argument("--jurisdiction", default="unspecified")
    categorize.add_argument("--use-local-llm", action="store_true")

    expenses = subparsers.add_parser("expenses", help="Categorize a personal-expense CSV")
    expenses.add_argument("csv_path", type=Path)
    expenses.add_argument("--output", type=Path)

    invoices = subparsers.add_parser("reconcile-invoices", help="Match invoice and payment CSVs")
    invoices.add_argument("invoice_csv", type=Path)
    invoices.add_argument("payment_csv", type=Path)
    invoices.add_argument("--amount-tolerance", type=float, default=0.01)

    statement = subparsers.add_parser("statement-summary", help="Compare statement periods")
    statement.add_argument("csv_path", type=Path)
    statement.add_argument("--change-flag-percent", type=float, default=25.0)

    sip = subparsers.add_parser("sip", help="Estimate recurring-contribution growth")
    sip.add_argument("--monthly", type=float, required=True)
    sip.add_argument("--annual-rate", type=float, required=True)
    sip.add_argument("--years", type=float, required=True)
    sip.add_argument("--initial", type=float, default=0.0)

    goal = subparsers.add_parser("goal", help="Estimate monthly contribution for a target")
    goal.add_argument("--target", type=float, required=True)
    goal.add_argument("--years", type=float, required=True)
    goal.add_argument("--annual-rate", type=float, required=True)
    goal.add_argument("--current", type=float, default=0.0)
    goal.add_argument("--inflation", type=float, default=0.0)

    compound = subparsers.add_parser("compound", help="Estimate compound growth")
    compound.add_argument("--principal", type=float, required=True)
    compound.add_argument("--annual-rate", type=float, required=True)
    compound.add_argument("--years", type=float, required=True)

    pdf = subparsers.add_parser("pdf-summary", help="Summarize a text-based research PDF")
    pdf.add_argument("pdf_path", type=Path)
    pdf.add_argument("--max-pages", type=int, default=50)
    pdf.add_argument("--sentences", type=int, default=8)
    pdf.add_argument("--use-local-llm", action="store_true")

    subparsers.add_parser("usage", help="Display local API/token usage")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO if args.verbose else logging.WARNING)
    guard = APIGuard()

    try:
        if args.command == "trading":
            output = TradingInsightsService(guard).analyze_symbol(
                args.symbol,
                period=args.period,
                interval=args.interval,
                include_news=args.news,
                news_limit=args.news_limit,
            )
            print_json(output)

        elif args.command == "portfolio":
            print_json(TradingInsightsService(guard).analyze_portfolio_csv(args.csv_path))

        elif args.command == "categorize":
            llm = LocalOllamaClient(guard=guard) if args.use_local_llm else None
            service = CAAssistantService(TransactionCategorizer(llm_client=llm))
            output = service.process_csv(
                args.csv_path,
                use_llm=args.use_local_llm,
                jurisdiction=args.jurisdiction,
            )
            if args.output:
                args.output.parent.mkdir(parents=True, exist_ok=True)
                pd.DataFrame(output["data"]["rows"]).to_csv(args.output, index=False)
                output["data"]["categorized_csv"] = str(args.output)
            print_json(output)

        elif args.command == "expenses":
            output = InvestorToolsService().categorize_expense_csv(args.csv_path)
            if args.output:
                args.output.parent.mkdir(parents=True, exist_ok=True)
                pd.DataFrame(output["data"]["rows"]).to_csv(args.output, index=False)
                output["data"]["categorized_csv"] = str(args.output)
            print_json(output)

        elif args.command == "reconcile-invoices":
            service = CAAssistantService(TransactionCategorizer())
            print_json(
                service.reconcile_invoice_csvs(
                    args.invoice_csv,
                    args.payment_csv,
                    amount_tolerance=args.amount_tolerance,
                )
            )

        elif args.command == "statement-summary":
            service = CAAssistantService(TransactionCategorizer())
            print_json(
                service.summarize_statement_csv(
                    args.csv_path,
                    change_flag_percent=args.change_flag_percent,
                )
            )

        elif args.command == "sip":
            print_json(
                InvestorToolsService().calculate_sip(
                    args.monthly,
                    args.annual_rate,
                    args.years,
                    args.initial,
                )
            )

        elif args.command == "goal":
            print_json(
                InvestorToolsService().plan_goal(
                    args.target,
                    args.years,
                    args.annual_rate,
                    args.current,
                    args.inflation,
                )
            )

        elif args.command == "compound":
            print_json(
                InvestorToolsService().calculate_compound_growth(
                    args.principal,
                    args.annual_rate,
                    args.years,
                )
            )

        elif args.command == "pdf-summary":
            llm = LocalOllamaClient(guard=guard) if args.use_local_llm else None
            print_json(
                InvestorToolsService(llm_client=llm).summarize_pdf(
                    args.pdf_path,
                    max_pages=args.max_pages,
                    sentence_count=args.sentences,
                    use_llm=args.use_local_llm,
                )
            )

        elif args.command == "usage":
            print_json(guard.snapshot())

        return 0
    except Exception as exc:
        print_json({"error": str(exc), "disclaimer": MASTER_DISCLAIMER})
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
