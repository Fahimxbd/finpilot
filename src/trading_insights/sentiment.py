"""Public RSS headline digest with transparent lexicon sentiment."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from urllib.parse import quote_plus

import feedparser

from core.api_guard import APIGuard

POSITIVE = {
    "beat",
    "beats",
    "growth",
    "gain",
    "gains",
    "strong",
    "upgrade",
    "upgraded",
    "record",
    "profit",
    "profits",
    "surge",
    "surges",
    "optimistic",
    "expands",
}
NEGATIVE = {
    "miss",
    "misses",
    "loss",
    "losses",
    "weak",
    "downgrade",
    "downgraded",
    "fall",
    "falls",
    "drop",
    "drops",
    "lawsuit",
    "probe",
    "fraud",
    "cuts",
    "risk",
}


def score_headline(text: str) -> int:
    punctuation = ".,:;!?()[]{}\"'"
    tokens = {token.strip(punctuation).lower() for token in text.split()}
    return len(tokens & POSITIVE) - len(tokens & NEGATIVE)


def label_score(score: float) -> str:
    if score > 0.25:
        return "positive"
    if score < -0.25:
        return "negative"
    return "mixed/neutral"


@dataclass
class RSSNewsDigest:
    guard: APIGuard

    def fetch(self, query: str, limit: int = 10) -> dict[str, Any]:
        query = query.strip()
        if not query:
            raise ValueError("News query cannot be empty")
        url = f"https://news.google.com/rss/search?q={quote_plus(query)}&hl=en-US&gl=US&ceid=US:en"
        with self.guard.budget("rss_news"):
            parsed = feedparser.parse(url)
        if getattr(parsed, "bozo", False) and not parsed.entries:
            error = getattr(parsed, "bozo_exception", "unknown error")
            raise RuntimeError(f"RSS fetch failed: {error}")

        items: list[dict[str, Any]] = []
        for entry in parsed.entries[: max(1, min(limit, 30))]:
            title = str(entry.get("title", "Untitled"))
            raw_score = score_headline(title)
            items.append(
                {
                    "title": title,
                    "link": str(entry.get("link", "")),
                    "published": str(entry.get("published", "")),
                    "sentiment_score": raw_score,
                    "sentiment": label_score(raw_score),
                }
            )
        average = sum(item["sentiment_score"] for item in items) / len(items) if items else 0.0
        return {
            "query": query,
            "retrieved_at": datetime.now(UTC).isoformat(),
            "headline_count": len(items),
            "aggregate_sentiment": label_score(average),
            "average_lexicon_score": round(average, 3),
            "headlines": items,
            "method": "Transparent keyword lexicon; not a predictive model.",
        }
