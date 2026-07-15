"""Research-PDF text extraction and transparent extractive summarization."""

from __future__ import annotations

import re
from collections import Counter
from pathlib import Path
from typing import Any

from pypdf import PdfReader

STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "been",
    "by",
    "for",
    "from",
    "has",
    "have",
    "in",
    "into",
    "is",
    "it",
    "its",
    "of",
    "on",
    "or",
    "that",
    "the",
    "their",
    "this",
    "to",
    "was",
    "were",
    "will",
    "with",
    "we",
    "our",
    "you",
    "your",
}


def extract_pdf_text(path: str | Path, max_pages: int = 50) -> tuple[str, dict[str, Any]]:
    pdf_path = Path(path)
    if not pdf_path.exists():
        raise FileNotFoundError(pdf_path)
    if pdf_path.suffix.lower() != ".pdf":
        raise ValueError("Only PDF files are supported")
    if max_pages <= 0:
        raise ValueError("max_pages must be greater than zero")

    reader = PdfReader(str(pdf_path))
    if reader.is_encrypted:
        try:
            reader.decrypt("")
        except Exception as exc:
            raise ValueError("Encrypted PDF could not be opened") from exc

    page_count = len(reader.pages)
    extracted: list[str] = []
    processed = min(page_count, max_pages)
    for page in reader.pages[:processed]:
        extracted.append(page.extract_text() or "")
    text = "\n".join(extracted).strip()
    if not text:
        raise ValueError(
            "No machine-readable text was found. Scanned/image-only PDFs require OCR, "
            "which FinPilot does not run automatically."
        )
    return text, {
        "file": pdf_path.name,
        "total_pages": page_count,
        "pages_processed": processed,
        "truncated_by_page_limit": page_count > processed,
        "characters_extracted": len(text),
    }


def _sentences(text: str) -> list[str]:
    compact = re.sub(r"\s+", " ", text).strip()
    return [item.strip() for item in re.split(r"(?<=[.!?])\s+", compact) if len(item.strip()) >= 40]


def _words(text: str) -> list[str]:
    return [
        token.lower()
        for token in re.findall(r"[A-Za-z][A-Za-z0-9'-]{2,}", text)
        if token.lower() not in STOPWORDS
    ]


def extractive_summary(text: str, sentence_count: int = 8) -> list[str]:
    if sentence_count <= 0:
        raise ValueError("sentence_count must be greater than zero")
    sentences = _sentences(text)
    if not sentences:
        return [text[:1000].strip()]
    frequencies = Counter(_words(text))
    if not frequencies:
        return sentences[:sentence_count]
    maximum = max(frequencies.values())
    normalized = {word: count / maximum for word, count in frequencies.items()}
    scored: list[tuple[float, int, str]] = []
    for index, sentence in enumerate(sentences):
        words = _words(sentence)
        if not words or len(words) > 80:
            continue
        score = sum(normalized.get(word, 0.0) for word in words) / max(1, len(words))
        scored.append((score, index, sentence))
    selected = sorted(scored, reverse=True)[: min(sentence_count, len(scored))]
    return [sentence for _, _, sentence in sorted(selected, key=lambda item: item[1])]


def summarize_research_pdf(
    path: str | Path,
    *,
    max_pages: int = 50,
    sentence_count: int = 8,
) -> dict[str, Any]:
    text, metadata = extract_pdf_text(path, max_pages=max_pages)
    return {
        "metadata": metadata,
        "summary_sentences": extractive_summary(text, sentence_count=sentence_count),
        "method": (
            "Extractive frequency-based summary; tables, charts, and images may not be represented."
        ),
        "review_flags": [
            "Check the original PDF before relying on any number, forecast, or conclusion.",
            "The summarizer does not validate methodology, conflicts of interest, or data quality.",
        ],
    }
