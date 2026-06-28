"""Fast baseline sentiment utilities built on VADER."""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer  # type: ignore[import-untyped]

BaselineSentimentLabel = Literal["positive", "neutral", "negative"]


@lru_cache(maxsize=1)
def _analyzer() -> SentimentIntensityAnalyzer:
    return SentimentIntensityAnalyzer()


def vader_compound_score(text: str) -> float:
    """Return baseline VADER compound score in [-1, 1]."""
    if not text.strip():
        return 0.0
    score = _analyzer().polarity_scores(text).get("compound", 0.0)
    return float(score)


def vader_label(text: str) -> BaselineSentimentLabel:
    """Map VADER score to coarse label using common thresholds."""
    score = vader_compound_score(text)
    if score >= 0.05:
        return "positive"
    if score <= -0.05:
        return "negative"
    return "neutral"
