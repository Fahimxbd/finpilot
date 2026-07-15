import pandas as pd

from investor_tools.expenses import categorize_expenses
from investor_tools.service import InvestorToolsService


def test_personal_expense_categories_and_disclaimer(tmp_path) -> None:
    frame = pd.DataFrame(
        {
            "date": ["2026-01-01", "2026-01-02"],
            "description": ["Supermarket grocery", "Monthly salary"],
            "amount": [-40, 500],
        }
    )
    categorized = categorize_expenses(frame)
    assert categorized["category"].tolist() == ["groceries", "income"]

    path = tmp_path / "expenses.csv"
    frame.to_csv(path, index=False)
    output = InvestorToolsService().categorize_expense_csv(path)
    assert "disclaimer" in output
