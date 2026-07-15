# Contributing to FinPilot

## Development setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest
ruff check .
```

## Pull-request rules

- Keep all financial outputs behind `core.disclaimer.disclaimed` or `attach_disclaimer`.
- Route every external network call and every LLM call through `APIGuard`.
- Do not add brokerage order placement, transfers, tax filing, or accounting-system write-back.
- Keep the default path free/local and do not require paid services.
- Do not commit secrets, statements, usage ledgers, audit logs, or generated customer data.
- Add tests for new calculations, parsers, guard logic, and safety boundaries.
- Mock network calls in tests.

## Commit style

Use focused commits with an imperative summary, for example:

```text
Add duplicate transaction review flag
Fix token reservation rollback
Document local Ollama privacy controls
```

## Code of conduct

Be factual, respectful, and review security/compliance concerns seriously. Financial-software claims must be conservative and reproducible.
