from pathlib import Path


def test_no_execution_or_filing_functions_in_source() -> None:
    source = "\n".join(
        path.read_text(encoding="utf-8") for path in Path("src").rglob("*.py")
    ).lower()
    forbidden = (
        "place_order(",
        "submit_order(",
        "execute_trade(",
        "create_transfer(",
        "submit_tax_return(",
        "file_tax_return(",
    )
    assert all(term not in source for term in forbidden)
