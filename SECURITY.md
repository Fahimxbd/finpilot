# Security policy

## Supported versions

Security fixes target the latest `main` branch and the latest tagged release.

## Reporting a vulnerability

Do not open a public issue for a vulnerability involving secrets, sensitive financial data, path traversal, code execution, dependency compromise, or budget-guard bypass.

Report it privately through GitHub Security Advisories for the repository. Include:

- affected commit or version;
- reproduction steps or a minimal proof of concept;
- realistic impact;
- suggested mitigation, when available.

Maintainers should acknowledge a valid report, investigate it, and coordinate disclosure after a fix is available. Never include real account numbers, bank statements, API keys, or personal financial records in a report.

## Security boundaries

FinPilot is read-only by design. Pull requests that add trade execution, transfers, tax filing, accounting write-back, or secret collection require rejection unless the project scope is formally changed with a separate security review.
