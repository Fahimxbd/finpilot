# FinPilot

> **FinPilot is a free, open-source automation toolkit that uses AI to assist with trading signal analysis, basic accounting/CA workflows, and personal investment research — with a hard API cost cap and full transparency. MIT licensed.**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://www.python.org/)
[![Live demo](https://img.shields.io/badge/Live%20Demo-Open%20FinPilot-1DBF95?logo=cloudflare&logoColor=white)](https://finpilot.fahimprivateuser-d8a.workers.dev/)

## Mandatory disclaimer

> **FinPilot does not provide financial, investment, tax, or legal advice. It is an educational automation tool. Consult a licensed professional before making financial decisions.**
>
> Trading output is informational only and is never a buy/sell recommendation. FinPilot has no brokerage write access and cannot execute trades, transfers, tax filings, or accounting postings.

## Cloudflare Workers demo (mobile, tablet and desktop)

FinPilot has a **browser-based Cloudflare Workers edition** in `public/`. It has a responsive dashboard and needs **no paid APIs, API keys, Python server, or database**. The original Python/Streamlit app below remains available for local or separate Streamlit hosting.

**Production Worker:** `finpilot`.

**Public live website:** [Launch FinPilot](https://finpilot.fahimprivateuser-d8a.workers.dev/)

**Direct Trading Insights page:** [Open Trading Insights](https://finpilot.fahimprivateuser-d8a.workers.dev/#trading)

Visitors can use the hosted website immediately in a mobile or desktop browser; no installation or sign-in is needed.

### Publish or redeploy

The repository's `wrangler.toml` points to `./public`, so Wrangler can deploy static assets:

```bash
npm install --no-audit --no-fund
npx wrangler deploy
```

For the Cloudflare GitHub integration, use:

- Repository: `Fahimxbd/finpilot`, branch: `main`, root directory `/`.
- Build command: leave blank (there is no frontend compilation step).
- Deploy command: `npx wrangler deploy`.
- Wrangler file: `wrangler.toml` (Worker name `finpilot`, assets `./public`).

**What works in-browser:** SIP, goal and compound-growth calculators; read-only holdings analysis; transaction categorization; invoice candidate matching; statement comparisons; historical OHLCV CSV technical indicators; pasted research text summarization. Files are parsed on-device, and no file content is sent to FinPilot servers.

**Differences from the Python version:** Live Yahoo Finance/yfinance and RSS retrieval, Python's PDF extraction, and local Ollama are **not available in the static Cloudflare edition**. Trading insights use a user-provided historical CSV; research summary uses pasted text. Use `streamlit_app.py` or the CLI for those Python-only features.

This demo is educational, not financial, tax or investment advice. It does not trade, transfer, file taxes or write to ledgers.

## Installation — computer terminal and Android Termux

**If you only want the web app**, no installation is required: [open FinPilot](https://finpilot.fahimprivateuser-d8a.workers.dev/). The browser version runs on Cloudflare and performs its calculations locally on your device.

### Linux / macOS terminal (full Python CLI + Streamlit)

Install Git and Python 3.11 or newer first. From a terminal:

```bash
git clone https://github.com/Fahimxbd/finpilot.git
cd finpilot
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
finpilot --help
streamlit run streamlit_app.py
```

The Streamlit command starts a local web server and shows its browser URL (normally `http://localhost:8501`). To try the command-line interface instead, run, for example:

```bash
finpilot sip --monthly 500 --annual-rate 8 --years 10 --initial 1000
finpilot portfolio sample_data/holdings.csv
```

To update an existing clone later: `git pull` from the `finpilot` directory, then repeat the Python install step if dependencies changed.

### Windows PowerShell (full Python CLI + Streamlit)

Install [Git](https://git-scm.com/) and Python 3.11+ first; then run:

```powershell
git clone https://github.com/Fahimxbd/finpilot.git
cd finpilot
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e .
finpilot --help
streamlit run streamlit_app.py
```

If PowerShell prevents virtual-environment activation, run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` in **that terminal session** and try activation again.

### Android Termux (browser-based Cloudflare edition, served locally)

Use the official, up-to-date Termux installation. These commands clone the project and serve its static frontend on your Android phone. They do not install the full Python/Streamlit backend:

```bash
pkg update -y && pkg upgrade -y
pkg install -y git python
git clone https://github.com/Fahimxbd/finpilot.git
cd finpilot
python -m http.server 8000 --bind 127.0.0.1 --directory public
```

Open a **second Termux session** (leave the server running in the first) and open the website:

```bash
termux-open-url http://127.0.0.1:8000/
```

Or open `http://127.0.0.1:8000/` directly in Chrome/Firefox. To stop the local server, return to its terminal and press `Ctrl+C`.

To update the local Termux copy:

```bash
cd ~/finpilot
git pull
```

**Android compatibility:** Native Python packages such as `numpy`, `pandas`, `pyarrow`, and Streamlit may require special builds or may fail under Termux. For a reliable Android experience, use the live Cloudflare URL or the local static server above. The browser-based edition supports the calculators and local CSV analysis but **does not** include Python-only live Yahoo data, RSS retrieval, Ollama, or PDF extraction.

## Web interface (free public demo)

FinPilot includes a Streamlit interface in `streamlit_app.py` for calculators, read-only
market research, portfolio review, CSV accounting workflows, and text-based PDF summaries.

[![Deploy on Streamlit Community Cloud](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://share.streamlit.io/)

Deploy settings:

- Repository: `Fahimxbd/finpilot`
- Branch: `main`
- Main file path: `streamlit_app.py`

The public interface is deliberately **fail-closed for cost safety**:

- no paid AI provider or cloud-LLM API key;
- local/rule-based processing only;
- no field where a visitor can submit an API key;
- no brokerage, payment, transfer, filing, or ledger-write capability;
- 8 MB upload limit, 5,000-row CSV limit, 25-page PDF limit;
- 10 live market-data requests per browser session.

Streamlit Community Cloud is currently a free hosting option for community apps. Do not
enter a payment card or upgrade to a paid product for this project. Hosting providers can
change their terms in the future, so review any new billing notice before accepting it.

## What it does

### Trading insights

- Downloads read-only OHLCV history through `yfinance`.
- Computes RSI, MACD, SMA, EMA, and recent volatility locally.
- Produces plain-language descriptions of historical indicator conditions.
- Optionally creates a transparent keyword-based digest of public RSS headlines.
- Flags single-position, top-three, asset-class, and short-exposure concentration from a holdings CSV.
- Never predicts guaranteed returns, generates executable orders, or connects to brokerage write APIs.

### CA/accounting assistant

- Imports common bank and ledger CSV formats.
- Normalizes amount, debit/credit, date, description, and balance fields.
- Categorizes transactions with auditable keyword rules.
- Optionally asks a local Ollama model to classify only unresolved rows.
- Flags duplicates, high-value entries, invalid dates, low-confidence rows, and uncategorized transactions.
- Matches invoice and payment CSVs using invoice-reference and amount checks.
- Compares financial-statement line items across periods and flags material changes.
- Drafts reconciliation and tax-review notes without posting entries or filing returns.

### Investor tools

- SIP/recurring-contribution calculator.
- Compound-growth calculator.
- Goal-based monthly contribution planner with an optional inflation assumption.
- Transparent personal-expense categorization.
- Text-based research PDF extraction with a deterministic summary and optional local-Ollama plain-language rewrite.
- Clear assumptions and review flags on every result.

## Zero-cost design

FinPilot's default path requires no paid API:

- Market history: `yfinance` (read-only; check the data source's terms before redistribution or commercial use).
- News: public Google News RSS feeds.
- AI: optional local [Ollama](https://docs.ollama.com/) endpoint; disabled by default.
- PDF processing: local `pypdf` text extraction.
- Calculations and classification rules: local Python.

No package in `requirements.txt` requires a paid license. External data services can change their availability or terms, so treat adapters as replaceable and verify permitted use for your deployment.

## Architecture

```mermaid
flowchart TD
    CLI[FinPilot CLI] --> TG[TradingInsightsService]
    CLI --> CA[CAAssistantService]
    CLI --> IT[InvestorToolsService]

    TG --> YF[yfinance read-only data]
    TG --> RSS[Public RSS digest]
    TG --> IND[Local indicators]
    TG --> PORT[Portfolio concentration flags]

    CA --> CSV[CSV normalization]
    CA --> RULES[Keyword categorizer]
    CA --> OLLAMA[Optional local Ollama]
    CA --> REVIEW[Anomaly and reconciliation review]
    CA --> INV[Invoice matching]
    CA --> STMT[Statement comparison]

    IT --> CALC[Local calculators]
    IT --> EXP[Expense categorization]
    IT --> PDF[pypdf extraction]
    IT --> SUM[Extractive summary]

    YF --> GUARD[API Guard]
    RSS --> GUARD
    OLLAMA --> GUARD
    GUARD --> USAGE[(Local usage JSON)]
    OLLAMA --> AUDIT[(Local AI audit JSONL)]

    TG --> DISC[Mandatory disclaimer wrapper]
    CA --> DISC
    IT --> DISC
```

## Repository layout

```text
finpilot/
├── LICENSE
├── README.md
├── SECURITY.md
├── CONTRIBUTING.md
├── .env.example
├── requirements.txt
├── pyproject.toml
├── streamlit_app.py
├── .streamlit/
│   └── config.toml
├── config/
│   └── limits.yaml
├── src/
│   ├── core/
│   │   ├── api_guard.py
│   │   ├── audit.py
│   │   ├── disclaimer.py
│   │   ├── llm_client.py
│   │   └── settings.py
│   ├── trading_insights/
│   ├── ca_assistant/
│   ├── investor_tools/
│   └── finpilot_cli.py
├── tests/
├── docs/
│   └── DISCLAIMER.md
├── sample_data/
│   ├── bank_transactions.csv
│   ├── holdings.csv
│   ├── invoices.csv
│   ├── payments.csv
│   └── financial_statement.csv
└── .github/workflows/ci.yml
```

## Setup

### 1. Clone and create a virtual environment

```bash
git clone https://github.com/Fahimxbd/finpilot.git
cd finpilot
python -m venv .venv
```

Activate it:

```bash
# Linux/macOS
source .venv/bin/activate

# Windows PowerShell
.venv\Scripts\Activate.ps1
```

### 2. Install

```bash
python -m pip install --upgrade pip
pip install -e ".[dev]"
cp .env.example .env  # Windows: copy .env.example .env
```

FinPilot reads environment variables from your shell. It deliberately does not add a secret-loading framework; use your shell, deployment platform, or a reviewed `.env` loader.

### 3. Optional local AI

Install Ollama separately, download a local model, and enable it:

```bash
ollama pull gemma3:4b
export FINPILOT_ENABLE_LLM=true
export OLLAMA_MODEL=gemma3:4b
```

The deterministic keyword categorizer works without Ollama.

## Usage

### Trading indicator summary

```bash
finpilot trading AAPL --period 6mo
finpilot trading MSFT --period 1y --news
```

### Portfolio concentration review

```bash
finpilot portfolio sample_data/holdings.csv
```

### Categorize a ledger/bank CSV

```bash
finpilot categorize sample_data/bank_transactions.csv --output categorized.csv
```

Use the local LLM only for unresolved descriptions:

```bash
FINPILOT_ENABLE_LLM=true finpilot categorize transactions.csv --use-local-llm
```

### Personal expense categorization

```bash
finpilot expenses sample_data/bank_transactions.csv --output expenses.csv
```

### Invoice reconciliation

```bash
finpilot reconcile-invoices sample_data/invoices.csv sample_data/payments.csv
```

### Financial-statement comparison

```bash
finpilot statement-summary sample_data/financial_statement.csv --change-flag-percent 25
```

### SIP estimate

```bash
finpilot sip --monthly 500 --annual-rate 8 --years 10 --initial 1000
```

### Goal estimate

```bash
finpilot goal --target 100000 --years 8 --annual-rate 7 --current 10000 --inflation 3
```

### Research PDF summary

```bash
finpilot pdf-summary research.pdf --max-pages 30 --sentences 8
FINPILOT_ENABLE_LLM=true finpilot pdf-summary research.pdf --use-local-llm
```

Scanned/image-only PDFs are rejected instead of silently producing unreliable OCR output.

## How the hard API cap works

`config/limits.yaml` is the source of truth:

```yaml
max_monthly_api_calls: 500
max_tokens_per_run: 8000
near_limit_ratio: 0.80
min_seconds_between_calls: 1.0
queue_on_throttle: true
```

The guard:

1. Reserves budget before each external or local-AI call.
2. Blocks calls that would cross a global monthly limit.
3. Blocks service-specific monthly limits.
4. Blocks an AI request that would cross the per-run token cap.
5. Warns near the configured threshold.
6. Queues by sleeping when calls occur too quickly, or raises when queueing is disabled.
7. Stores usage in `.finpilot/usage.json` using an atomic write and file lock.
8. Rolls back a reservation when the underlying call fails.

Environment overrides:

```bash
export MAX_MONTHLY_API_CALLS=100
export MAX_TOKENS_PER_RUN=4000
export FINPILOT_USAGE_FILE=/secure/path/usage.json
```

Inspect current usage:

```bash
finpilot usage
```

## AI audit log

Every local AI call writes metadata to `.finpilot/ai_audit.jsonl`, including:

- timestamp, provider, and model;
- prompt/response SHA-256 hashes;
- character counts and token estimate;
- success/error status.

Full financial document content is **not** logged by default. Explicitly enable it only in a controlled environment:

```bash
export FINPILOT_LOG_FULL_AI_CONTENT=true
```

## Tests and quality checks

```bash
pytest --cov=src --cov-report=term-missing
ruff format --check .
ruff check .
```

CI runs formatting, lint, and tests on Python 3.11, 3.12, and 3.13.

## Security and privacy

- Do not upload sensitive statements to an untrusted model or host.
- Prefer local Ollama for transaction descriptions.
- Review CSV/PDF contents before processing.
- Audit output before relying on it.
- Never place secrets in Git or commit `.env`/`.finpilot`.

See [SECURITY.md](SECURITY.md) and [docs/DISCLAIMER.md](docs/DISCLAIMER.md).

## Contributing

Contributions are welcome. Keep the following boundaries intact:

- no trade, transfer, filing, or posting execution;
- no paid-only dependency as the default path;
- all financial output must pass through the disclaimer wrapper;
- every new external/AI call must pass through `APIGuard`;
- tests must not require internet access or secrets.

Read [CONTRIBUTING.md](CONTRIBUTING.md) before opening a pull request.

## License

MIT. See [LICENSE](LICENSE).
