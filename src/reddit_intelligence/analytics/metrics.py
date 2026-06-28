"""KPI computations for dashboard cards and aggregate reporting."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

from reddit_intelligence.analytics.aggregates import AnalyticsRecord


@dataclass(frozen=True)
class KpiSnapshot:
    total_relevant_records: int
    avg_sentiment_score: float
    negative_rate: float
    avg_confidence: float
    sarcasm_rate: float


def _avg(values: list[float]) -> float:
    if not values:
        return 0.0
    return sum(values) / float(len(values))


def _window_records(
    records: list[AnalyticsRecord],
    *,
    days: int,
    reference_day: date,
) -> list[AnalyticsRecord]:
    window_start = reference_day - timedelta(days=days)
    return [
        record
        for record in records
        if record.relevant and not record.is_deleted and window_start <= record.day < reference_day
    ]


def compute_kpi_snapshot(
    records: list[AnalyticsRecord],
    *,
    days: int = 30,
    reference_day: date | None = None,
) -> KpiSnapshot:
    """Compute bounded KPI snapshot over the selected lookback window."""
    eligible = [record for record in records if record.relevant and not record.is_deleted]
    if reference_day is None:
        if not eligible:
            return KpiSnapshot(0, 0.0, 0.0, 0.0, 0.0)
        reference_day = max(record.day for record in eligible) + timedelta(days=1)
    window = _window_records(eligible, days=days, reference_day=reference_day)
    return KpiSnapshot(
        total_relevant_records=len(window),
        avg_sentiment_score=_avg([record.sentiment_score for record in window]),
        negative_rate=_avg(
            [1.0 if record.sentiment_label == "negative" else 0.0 for record in window]
        ),
        avg_confidence=_avg([record.confidence for record in window]),
        sarcasm_rate=_avg([1.0 if record.sarcasm_detected else 0.0 for record in window]),
    )
