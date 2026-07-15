"""Public, zero-cost Streamlit interface for FinPilot.

The hosted interface deliberately excludes paid API providers, user-supplied API keys,
trade execution, transfers, filing, and accounting write-back.
"""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ca_assistant.categorizer import TransactionCategorizer  # noqa: E402
from ca_assistant.invoice_reconciliation import reconcile_invoices  # noqa: E402
from ca_assistant.service import CAAssistantService  # noqa: E402
from ca_assistant.statements import summarize_statement  # noqa: E402
from core.api_guard import APIGuard, BudgetExceededError  # noqa: E402
from core.disclaimer import MASTER_DISCLAIMER, TRADING_DISCLAIMER  # noqa: E402
from investor_tools.pdf_summary import summarize_research_pdf  # noqa: E402
from investor_tools.service import InvestorToolsService  # noqa: E402
from trading_insights.portfolio import analyze_portfolio  # noqa: E402
from trading_insights.service import TradingInsightsService  # noqa: E402

MAX_UPLOAD_BYTES = 8 * 1024 * 1024
MAX_ROWS = 5_000
MAX_PDF_PAGES = 25
MAX_LIVE_CALLS_PER_SESSION = 10

# Fail closed: the public app never enables a paid/cloud LLM path.
os.environ["FINPILOT_ENABLE_LLM"] = "false"
os.environ["FINPILOT_LOG_FULL_AI_CONTENT"] = "false"

st.set_page_config(
    page_title="FinPilot",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


def _money(value: float) -> str:
    return f"{value:,.2f}"


def _uploaded_frame(uploaded_file: Any) -> pd.DataFrame:
    if uploaded_file is None:
        raise ValueError("Upload a CSV file first.")
    if uploaded_file.size > MAX_UPLOAD_BYTES:
        raise ValueError("File is larger than the 8 MB public-app limit.")
    frame = pd.read_csv(uploaded_file)
    if len(frame) > MAX_ROWS:
        raise ValueError(f"CSV has {len(frame):,} rows; the public-app limit is {MAX_ROWS:,}.")
    return frame


def _data(payload: dict[str, Any]) -> dict[str, Any]:
    return payload.get("data", payload)


def _show_disclaimer(*, trading: bool = False) -> None:
    text = MASTER_DISCLAIMER
    if trading:
        text = f"{text} {TRADING_DISCLAIMER}"
    st.warning(text, icon="⚠️")


def _download_csv(frame: pd.DataFrame, filename: str, label: str = "Download CSV") -> None:
    st.download_button(
        label,
        frame.to_csv(index=False).encode("utf-8"),
        file_name=filename,
        mime="text/csv",
        use_container_width=True,
    )


def _live_call_allowed() -> bool:
    count = int(st.session_state.get("live_calls", 0))
    if count >= MAX_LIVE_CALLS_PER_SESSION:
        st.error(
            "This browser session reached the public demo's 10 live-market-call limit. "
            "Refresh later or run FinPilot locally."
        )
        return False
    st.session_state["live_calls"] = count + 1
    return True


@st.cache_resource
def _guard() -> APIGuard:
    return APIGuard()


investor_service = InvestorToolsService(llm_client=None)
accounting_service = CAAssistantService(TransactionCategorizer(llm_client=None))

st.title("FinPilot")
st.caption("Open-source financial operations toolkit — public zero-cost demo")

with st.container(border=True):
    left, right = st.columns([2, 1])
    with left:
        st.markdown(
            "**Cost-safe public mode:** no paid AI provider, no user API keys, no brokerage "
            "connection, no payments, and no automatic financial actions."
        )
    with right:
        st.success("Paid API usage: OFF", icon="🔒")

st.info(
    "This public app runs on free hosting and free/local libraries. Uploaded files are processed "
    "temporarily on the app server and are not intentionally saved by FinPilot. Do not upload "
    "unredacted highly sensitive financial records to any public demo.",
    icon="ℹ️",
)

page = st.sidebar.radio(
    "Choose a tool",
    [
        "Overview",
        "SIP calculator",
        "Goal planner",
        "Compound growth",
        "Trading insights",
        "Portfolio review",
        "Transaction categorizer",
        "Invoice reconciliation",
        "Statement comparison",
        "Research PDF summary",
    ],
)

st.sidebar.divider()
st.sidebar.markdown("**Public-demo safeguards**")
st.sidebar.markdown(
    "- No paid APIs\n"
    "- No API-key input\n"
    "- Local/rule-based analysis\n"
    "- 8 MB upload cap\n"
    "- 5,000-row CSV cap\n"
    "- 25-page PDF cap\n"
    "- 10 live calls/session"
)
st.sidebar.link_button(
    "View source on GitHub",
    "https://github.com/Fahimxbd/finpilot",
    use_container_width=True,
)

if page == "Overview":
    st.subheader("What you can use here")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("### Investors")
        st.write(
            "SIP, goal and compound-growth estimates, portfolio concentration review, PDF summaries."
        )
    with col2:
        st.markdown("### Accounting")
        st.write("CSV categorization, anomaly flags, invoice matching and statement comparisons.")
    with col3:
        st.markdown("### Market research")
        st.write("Read-only technical-indicator summaries from public market data.")
    st.markdown("### What FinPilot will not do")
    st.write(
        "It will not execute a trade, transfer money, file a tax return, post journal entries, "
        "guarantee returns, or replace a licensed professional."
    )
    _show_disclaimer()

elif page == "SIP calculator":
    st.subheader("SIP / recurring investment calculator")
    with st.form("sip_form"):
        monthly = st.number_input("Monthly contribution", min_value=0.0, value=500.0, step=50.0)
        initial = st.number_input("Initial amount", min_value=0.0, value=0.0, step=100.0)
        annual_rate = st.number_input(
            "Assumed annual return (%)", min_value=-99.0, max_value=100.0, value=8.0, step=0.5
        )
        years = st.number_input("Years", min_value=0.0, max_value=100.0, value=10.0, step=1.0)
        submitted = st.form_submit_button("Calculate", use_container_width=True)
    if submitted:
        try:
            result = _data(investor_service.calculate_sip(monthly, annual_rate, years, initial))
            a, b, c = st.columns(3)
            a.metric("Total contributed", _money(result["total_contributed"]))
            b.metric("Estimated future value", _money(result["estimated_future_value"]))
            c.metric("Estimated growth", _money(result["estimated_growth"]))
            st.caption(result["assumption"])
        except ValueError as exc:
            st.error(str(exc))
    _show_disclaimer()

elif page == "Goal planner":
    st.subheader("Goal-based contribution planner")
    with st.form("goal_form"):
        target = st.number_input("Target amount in today's money", min_value=0.0, value=100000.0)
        current = st.number_input("Current savings", min_value=0.0, value=10000.0)
        years = st.number_input("Years to goal", min_value=0.0, max_value=100.0, value=8.0)
        annual_rate = st.number_input(
            "Assumed annual return (%)", min_value=-99.0, max_value=100.0, value=7.0
        )
        inflation = st.number_input(
            "Assumed annual inflation (%)", min_value=-99.0, max_value=100.0, value=3.0
        )
        submitted = st.form_submit_button("Plan goal", use_container_width=True)
    if submitted:
        try:
            result = _data(
                investor_service.plan_goal(target, years, annual_rate, current, inflation)
            )
            a, b = st.columns(2)
            a.metric("Inflation-adjusted target", _money(result["inflation_adjusted_target"]))
            b.metric(
                "Estimated monthly contribution required",
                _money(result["estimated_monthly_contribution_required"]),
            )
            st.caption(result["assumption"])
        except ValueError as exc:
            st.error(str(exc))
    _show_disclaimer()

elif page == "Compound growth":
    st.subheader("Compound-growth calculator")
    with st.form("compound_form"):
        principal = st.number_input("Starting principal", min_value=0.0, value=10000.0)
        annual_rate = st.number_input(
            "Assumed annual rate (%)", min_value=-99.0, max_value=100.0, value=7.0
        )
        years = st.number_input("Years", min_value=0.0, max_value=100.0, value=10.0)
        submitted = st.form_submit_button("Calculate", use_container_width=True)
    if submitted:
        try:
            result = _data(
                investor_service.calculate_compound_growth(principal, annual_rate, years)
            )
            a, b = st.columns(2)
            a.metric("Estimated future value", _money(result["estimated_future_value"]))
            b.metric("Estimated growth", _money(result["estimated_growth"]))
            st.caption(result["assumption"])
        except ValueError as exc:
            st.error(str(exc))
    _show_disclaimer()

elif page == "Trading insights":
    st.subheader("Read-only technical indicator summary")
    st.caption("Uses public Yahoo market data through yfinance. It cannot place orders.")
    with st.form("trading_form"):
        symbol = st.text_input("Ticker symbol", value="AAPL", max_chars=15).strip().upper()
        period = st.selectbox("History period", ["1mo", "3mo", "6mo", "1y", "2y"], index=2)
        include_news = st.checkbox("Include public RSS headline digest", value=False)
        submitted = st.form_submit_button("Analyze", use_container_width=True)
    if submitted and symbol and _live_call_allowed():
        try:
            with st.spinner("Loading public market data..."):
                payload = TradingInsightsService(_guard()).analyze_symbol(
                    symbol,
                    period=period,
                    include_news=include_news,
                    news_limit=6,
                )
            result = _data(payload)
            st.markdown(f"### {result['symbol']}")
            st.write(result["summary"])
            snapshot = result["indicator_snapshot"]
            st.dataframe(pd.DataFrame([snapshot]), use_container_width=True, hide_index=True)
            if include_news and result.get("news_digest"):
                digest = result["news_digest"]
                st.markdown("### Headline digest")
                st.write(digest.get("summary", ""))
                if digest.get("headlines"):
                    st.dataframe(pd.DataFrame(digest["headlines"]), use_container_width=True)
        except BudgetExceededError as exc:
            st.error(f"Public demo limit reached: {exc}")
        except Exception as exc:  # Network/data-source errors must be user-readable.
            st.error(f"Market data could not be loaded: {exc}")
    _show_disclaimer(trading=True)

elif page == "Portfolio review":
    st.subheader("Portfolio concentration review")
    st.caption("CSV requires symbol/ticker and market_value/value columns.")
    upload = st.file_uploader("Upload holdings CSV", type=["csv"], key="portfolio")
    if st.button("Review portfolio", use_container_width=True):
        try:
            frame = _uploaded_frame(upload)
            result = analyze_portfolio(frame)
            a, b, c = st.columns(3)
            a.metric("Positions", result["position_count"])
            b.metric("Largest position", f"{result['largest_position_weight']:.1%}")
            c.metric("Top three", f"{result['top_three_weight']:.1%}")
            st.markdown("### Risk flags")
            if result["risk_flags"]:
                st.dataframe(pd.DataFrame(result["risk_flags"]), use_container_width=True)
            else:
                st.success("No concentration threshold was triggered by this simple review.")
            positions = pd.DataFrame(result["top_positions"])
            st.dataframe(positions, use_container_width=True)
        except Exception as exc:
            st.error(str(exc))
    _show_disclaimer(trading=True)

elif page == "Transaction categorizer":
    st.subheader("Bank / ledger CSV categorizer")
    st.caption("Classification uses transparent keyword rules only. Cloud AI is disabled.")
    upload = st.file_uploader("Upload transaction CSV", type=["csv"], key="transactions")
    jurisdiction = st.text_input("Jurisdiction label for the draft note", value="unspecified")
    if st.button("Categorize transactions", use_container_width=True):
        try:
            frame = _uploaded_frame(upload)
            result = _data(
                accounting_service.process_frame(
                    frame,
                    use_llm=False,
                    jurisdiction=jurisdiction.strip() or "unspecified",
                )
            )
            rows = pd.DataFrame(result["rows"])
            st.dataframe(rows, use_container_width=True)
            st.markdown("### Reconciliation summary")
            st.json(result["summary"], expanded=False)
            st.markdown("### Draft review note")
            st.write(result["draft_tax_note"])
            _download_csv(rows, "finpilot-categorized-transactions.csv")
        except Exception as exc:
            st.error(str(exc))
    _show_disclaimer()

elif page == "Invoice reconciliation":
    st.subheader("Invoice-to-payment candidate matching")
    left, right = st.columns(2)
    with left:
        invoices_upload = st.file_uploader("Invoices CSV", type=["csv"], key="invoices")
    with right:
        payments_upload = st.file_uploader("Payments CSV", type=["csv"], key="payments")
    tolerance = st.number_input("Amount tolerance", min_value=0.0, value=0.01, step=0.01)
    if st.button("Match invoices", use_container_width=True):
        try:
            invoices = _uploaded_frame(invoices_upload)
            payments = _uploaded_frame(payments_upload)
            result = reconcile_invoices(invoices, payments, amount_tolerance=tolerance)
            a, b = st.columns(2)
            a.metric("Matched invoices", result["matched_invoices"])
            b.metric(
                "Unmatched / ambiguous",
                result["unmatched_or_ambiguous_invoices"],
            )
            rows = pd.DataFrame(result["invoice_results"])
            st.dataframe(rows, use_container_width=True)
            _download_csv(rows, "finpilot-invoice-matches.csv")
        except Exception as exc:
            st.error(str(exc))
    _show_disclaimer()

elif page == "Statement comparison":
    st.subheader("Period-over-period statement comparison")
    st.caption("CSV columns: line_item, current_period, prior_period.")
    upload = st.file_uploader("Upload statement CSV", type=["csv"], key="statement")
    threshold = st.slider("Flag absolute changes at or above (%)", 1, 200, 25)
    if st.button("Compare periods", use_container_width=True):
        try:
            frame = _uploaded_frame(upload)
            result = summarize_statement(frame, change_flag_percent=float(threshold))
            a, b = st.columns(2)
            a.metric("Line items", result["line_item_count"])
            b.metric("Flagged line items", result["flagged_line_items"])
            rows = pd.DataFrame(result["rows"])
            st.dataframe(rows, use_container_width=True)
            _download_csv(rows, "finpilot-statement-comparison.csv")
            st.caption(result["method"])
        except Exception as exc:
            st.error(str(exc))
    _show_disclaimer()

elif page == "Research PDF summary":
    st.subheader("Research PDF extractive summary")
    st.caption(
        "Public mode uses local text extraction only. It does not send the PDF to OpenAI, "
        "Claude, Gemini, or another paid model."
    )
    upload = st.file_uploader("Upload a text-based PDF", type=["pdf"], key="pdf")
    sentences = st.slider("Summary sentences", 3, 12, 7)
    if st.button("Summarize PDF", use_container_width=True):
        temp_path: Path | None = None
        try:
            if upload is None:
                raise ValueError("Upload a PDF first.")
            if upload.size > MAX_UPLOAD_BYTES:
                raise ValueError("PDF is larger than the 8 MB public-app limit.")
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp:
                temp.write(upload.getbuffer())
                temp_path = Path(temp.name)
            result = summarize_research_pdf(
                temp_path,
                max_pages=MAX_PDF_PAGES,
                sentence_count=sentences,
            )
            st.json(result["metadata"], expanded=False)
            st.markdown("### Extractive summary")
            for sentence in result["summary_sentences"]:
                st.write(f"- {sentence}")
            for flag in result["review_flags"]:
                st.caption(f"• {flag}")
        except Exception as exc:
            st.error(str(exc))
        finally:
            if temp_path is not None:
                temp_path.unlink(missing_ok=True)
    _show_disclaimer()
