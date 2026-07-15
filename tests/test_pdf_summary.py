import pytest

from investor_tools.pdf_summary import extractive_summary


def test_extractive_summary_returns_requested_number_in_original_order() -> None:
    text = (
        "Revenue increased because subscription demand expanded across multiple regions. "
        "The company also reported higher customer acquisition costs during the period. "
        "Management expects operating investment to remain elevated next year. "
        "Cash flow improved after working capital normalized in the final quarter. "
        "The report warns that currency movements may affect future comparisons."
    )
    summary = extractive_summary(text, sentence_count=3)
    assert len(summary) == 3
    positions = [text.index(sentence) for sentence in summary]
    assert positions == sorted(positions)


def test_rejects_invalid_sentence_count() -> None:
    with pytest.raises(ValueError):
        extractive_summary("A sufficiently long sentence for testing purposes.", sentence_count=0)
