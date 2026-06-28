from __future__ import annotations

from datetime import date, timedelta

from reddit_intelligence.analytics.aggregates import AnalyticsRecord
from reddit_intelligence.analytics.trends import compute_sentiment_trend, compute_volume_trend


def _record(day: date, source_reddit_id: str, sentiment_score: float) -> AnalyticsRecord:
    return AnalyticsRecord(
        day=day,
        subreddit="spotify",
        source_type="comment",
        source_reddit_id=source_reddit_id,
        sentiment_label="positive" if sentiment_score >= 0 else "negative",
        sentiment_score=sentiment_score,
        theme="other",
        subtheme="general",
        feature="Unknown",
        user_segment="unknown",
        pain_point="",
        severity=2,
        confidence=0.8,
        sarcasm_detected=False,
        relevant=True,
        is_deleted=False,
    )


def test_volume_trend_handles_zero_previous_window() -> None:
    reference_day = date(2026, 2, 1)
    rows = [_record(reference_day - timedelta(days=3), "a", 0.2)]
    trend = compute_volume_trend(rows, days=7, reference_day=reference_day)
    assert trend.current_value == 1.0
    assert trend.previous_value == 0.0
    assert trend.delta_percent is None


def test_sentiment_trend_computes_window_delta() -> None:
    reference_day = date(2026, 2, 1)
    rows = [
        _record(reference_day - timedelta(days=2), "current-1", 0.6),
        _record(reference_day - timedelta(days=1), "current-2", 0.4),
        _record(reference_day - timedelta(days=8), "previous-1", 0.1),
    ]
    trend = compute_sentiment_trend(rows, days=7, reference_day=reference_day)
    assert round(trend.current_value, 4) == 0.5
    assert round(trend.previous_value, 4) == 0.1
    assert round(trend.delta_absolute, 4) == 0.4
