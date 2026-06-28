"""Windowed trend computations for analytics metrics."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

from reddit_intelligence.analytics.aggregates import AnalyticsRecord


@dataclass(frozen=True)
class TrendValue:
    metric: str
    current_value: float
    previous_value: float
    delta_absolute: float
    delta_percent: float | None


def _window_bounds(*, reference_day: date, days: int) -> tuple[date, date, date]:
    current_start = reference_day - timedelta(days=days)
    previous_start = current_start - timedelta(days=days)
    return previous_start, current_start, reference_day


def _records_in_range(
    records: list[AnalyticsRecord],
    *,
    start: date,
    end: date,
) -> list[AnalyticsRecord]:
    return [
        record
        for record in records
        if record.relevant and not record.is_deleted and start <= record.day < end
    ]


def _avg(values: list[float]) -> float:
    if not values:
        return 0.0
    return sum(values) / float(len(values))


def _delta_percent(current: float, previous: float) -> float | None:
    if previous == 0:
        return None
    return (current - previous) / abs(previous)


def compute_volume_trend(
    records: list[AnalyticsRecord],
    *,
    days: int = 30,
    reference_day: date | None = None,
) -> TrendValue:
    """Compute mention volume change between current and previous windows."""
    eligible = [record for record in records if record.relevant and not record.is_deleted]
    if reference_day is None:
        reference_day = (
            (max(record.day for record in eligible) + timedelta(days=1))
            if eligible
            else date.today()
        )
    previous_start, current_start, current_end = _window_bounds(
        reference_day=reference_day, days=days
    )
    previous = float(len(_records_in_range(eligible, start=previous_start, end=current_start)))
    current = float(len(_records_in_range(eligible, start=current_start, end=current_end)))
    return TrendValue(
        metric="volume",
        current_value=current,
        previous_value=previous,
        delta_absolute=current - previous,
        delta_percent=_delta_percent(current, previous),
    )


def compute_sentiment_trend(
    records: list[AnalyticsRecord],
    *,
    days: int = 30,
    reference_day: date | None = None,
) -> TrendValue:
    """Compute average sentiment-score change between adjacent windows."""
    eligible = [record for record in records if record.relevant and not record.is_deleted]
    if reference_day is None:
        reference_day = (
            (max(record.day for record in eligible) + timedelta(days=1))
            if eligible
            else date.today()
        )
    previous_start, current_start, current_end = _window_bounds(
        reference_day=reference_day, days=days
    )
    previous_records = _records_in_range(eligible, start=previous_start, end=current_start)
    current_records = _records_in_range(eligible, start=current_start, end=current_end)
    previous = _avg([record.sentiment_score for record in previous_records])
    current = _avg([record.sentiment_score for record in current_records])
    return TrendValue(
        metric="sentiment_score",
        current_value=current,
        previous_value=previous,
        delta_absolute=current - previous,
        delta_percent=_delta_percent(current, previous),
    )
