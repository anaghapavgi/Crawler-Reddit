"""Deterministic analytics aggregations aligned to SQL view formulas."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Literal

SourceType = Literal["post", "comment"]


@dataclass(frozen=True)
class AnalyticsRecord:
    """Normalized record used for analytics computations."""

    day: date
    subreddit: str
    source_type: SourceType
    source_reddit_id: str
    sentiment_label: str
    sentiment_score: float
    theme: str
    subtheme: str
    feature: str
    user_segment: str
    pain_point: str
    severity: int
    confidence: float
    sarcasm_detected: bool
    relevant: bool
    is_deleted: bool


@dataclass(frozen=True)
class DailySentimentSummary:
    day: date
    subreddit: str
    sentiment_label: str
    record_count: int
    avg_sentiment_score: float
    avg_severity: float


@dataclass(frozen=True)
class ThemeSummary:
    theme: str
    subtheme: str
    record_count: int
    negative_rate: float
    avg_severity: float
    avg_confidence: float


@dataclass(frozen=True)
class FeatureSummary:
    feature: str
    record_count: int
    avg_sentiment_score: float
    negative_rate: float
    top_theme: str


@dataclass(frozen=True)
class SegmentSummary:
    user_segment: str
    record_count: int
    avg_sentiment_score: float
    top_pain_point: str


@dataclass(frozen=True)
class EmergingThemeSummary:
    theme: str
    recent_weekly_volume: int
    baseline_weekly_volume: float
    recent_distinct_sources: int
    avg_confidence: float
    recent_negative_rate: float
    emergence_score: float


@dataclass(frozen=True)
class AggregationSnapshot:
    """Collection of view-like aggregation outputs."""

    daily_sentiment: list[DailySentimentSummary]
    theme_summary: list[ThemeSummary]
    feature_summary: list[FeatureSummary]
    segment_summary: list[SegmentSummary]
    emerging_themes: list[EmergingThemeSummary]


def _as_bool(value: str) -> bool:
    return value.strip().lower() in {"true", "1", "yes"}


def _avg(values: list[float]) -> float:
    if not values:
        return 0.0
    return sum(values) / float(len(values))


def _eligible(records: list[AnalyticsRecord]) -> list[AnalyticsRecord]:
    return [record for record in records if record.relevant and not record.is_deleted]


def load_analytics_records_from_csv(path: Path) -> list[AnalyticsRecord]:
    """Load deterministic analytics input rows from CSV fixture/demo data."""
    records: list[AnalyticsRecord] = []
    with path.open("r", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            source_type: SourceType = "post" if row.get("source_type", "") == "post" else "comment"
            records.append(
                AnalyticsRecord(
                    day=date.fromisoformat(str(row.get("date", ""))),
                    subreddit=str(row.get("subreddit", "")),
                    source_type=source_type,
                    source_reddit_id=str(row.get("source_reddit_id", "")),
                    sentiment_label=str(row.get("sentiment_label", "unknown")),
                    sentiment_score=float(row.get("sentiment_score", 0.0)),
                    theme=str(row.get("theme", "other")),
                    subtheme=str(row.get("subtheme", "other")),
                    feature=str(row.get("feature", "Unknown")),
                    user_segment=str(row.get("segment", "unknown")),
                    pain_point=str(row.get("pain_point", "")),
                    severity=int(float(row.get("severity", 0))),
                    confidence=float(row.get("confidence", 0.0)),
                    sarcasm_detected=_as_bool(str(row.get("sarcasm_detected", "false"))),
                    relevant=_as_bool(str(row.get("relevant", "false"))),
                    is_deleted=_as_bool(str(row.get("is_deleted", "false"))),
                )
            )
    return records


def compute_daily_sentiment_summary(records: list[AnalyticsRecord]) -> list[DailySentimentSummary]:
    grouped: dict[tuple[date, str, str], list[AnalyticsRecord]] = {}
    for record in _eligible(records):
        key = (record.day, record.subreddit, record.sentiment_label or "unknown")
        grouped.setdefault(key, []).append(record)

    summaries = [
        DailySentimentSummary(
            day=day,
            subreddit=subreddit,
            sentiment_label=label,
            record_count=len(bucket),
            avg_sentiment_score=_avg([item.sentiment_score for item in bucket]),
            avg_severity=_avg([float(item.severity) for item in bucket]),
        )
        for (day, subreddit, label), bucket in grouped.items()
    ]
    return sorted(summaries, key=lambda item: (item.day, item.subreddit, item.sentiment_label))


def compute_theme_summary(records: list[AnalyticsRecord]) -> list[ThemeSummary]:
    grouped: dict[tuple[str, str], list[AnalyticsRecord]] = {}
    for record in _eligible(records):
        key = (record.theme or "other", record.subtheme or "other")
        grouped.setdefault(key, []).append(record)

    summaries = [
        ThemeSummary(
            theme=theme,
            subtheme=subtheme,
            record_count=len(bucket),
            negative_rate=_avg([1.0 if item.sentiment_label == "negative" else 0.0 for item in bucket]),
            avg_severity=_avg([float(item.severity) for item in bucket]),
            avg_confidence=_avg([item.confidence for item in bucket]),
        )
        for (theme, subtheme), bucket in grouped.items()
    ]
    return sorted(summaries, key=lambda item: (item.record_count * -1, item.theme, item.subtheme))


def compute_feature_summary(records: list[AnalyticsRecord]) -> list[FeatureSummary]:
    eligible = _eligible(records)
    by_feature: dict[str, list[AnalyticsRecord]] = {}
    for record in eligible:
        by_feature.setdefault(record.feature or "Unknown", []).append(record)

    summaries: list[FeatureSummary] = []
    for feature, bucket in by_feature.items():
        theme_counts: dict[str, int] = {}
        for item in bucket:
            theme_counts[item.theme] = theme_counts.get(item.theme, 0) + 1
        top_theme = min(theme_counts, key=lambda theme: (-theme_counts[theme], theme))
        summaries.append(
            FeatureSummary(
                feature=feature,
                record_count=len(bucket),
                avg_sentiment_score=_avg([item.sentiment_score for item in bucket]),
                negative_rate=_avg(
                    [1.0 if item.sentiment_label == "negative" else 0.0 for item in bucket]
                ),
                top_theme=top_theme,
            )
        )
    return sorted(summaries, key=lambda item: (item.record_count * -1, item.feature))


def compute_segment_summary(records: list[AnalyticsRecord]) -> list[SegmentSummary]:
    eligible = _eligible(records)
    by_segment: dict[str, list[AnalyticsRecord]] = {}
    for record in eligible:
        by_segment.setdefault(record.user_segment or "unknown", []).append(record)

    summaries: list[SegmentSummary] = []
    for segment, bucket in by_segment.items():
        pain_counts: dict[str, int] = {}
        for item in bucket:
            pain = item.pain_point or ""
            pain_counts[pain] = pain_counts.get(pain, 0) + 1
        top_pain_point = min(pain_counts, key=lambda pain: (-pain_counts[pain], pain))
        summaries.append(
            SegmentSummary(
                user_segment=segment,
                record_count=len(bucket),
                avg_sentiment_score=_avg([item.sentiment_score for item in bucket]),
                top_pain_point=top_pain_point,
            )
        )
    return sorted(summaries, key=lambda item: (item.record_count * -1, item.user_segment))


def compute_emerging_themes(
    records: list[AnalyticsRecord],
    *,
    reference_day: date | None = None,
) -> list[EmergingThemeSummary]:
    eligible = _eligible(records)
    if not eligible:
        return []
    if reference_day is None:
        reference_day = max(record.day for record in eligible) + timedelta(days=1)

    recent_start = reference_day - timedelta(days=7)
    baseline_start = reference_day - timedelta(days=35)
    baseline_end = recent_start

    recent_by_theme: dict[str, list[AnalyticsRecord]] = {}
    baseline_by_theme: dict[str, list[AnalyticsRecord]] = {}
    for record in eligible:
        if recent_start <= record.day < reference_day:
            recent_by_theme.setdefault(record.theme, []).append(record)
        elif baseline_start <= record.day < baseline_end:
            baseline_by_theme.setdefault(record.theme, []).append(record)

    summaries: list[EmergingThemeSummary] = []
    for theme, bucket in recent_by_theme.items():
        recent_weekly_volume = len(bucket)
        recent_distinct_sources = len({item.source_reddit_id for item in bucket})
        avg_confidence = _avg([item.confidence for item in bucket])
        recent_negative_rate = _avg(
            [1.0 if item.sentiment_label == "negative" else 0.0 for item in bucket]
        )
        baseline_weekly_volume = len(baseline_by_theme.get(theme, [])) / 4.0
        emergence_score = recent_weekly_volume / max(baseline_weekly_volume, 1.0)
        if recent_weekly_volume < 5 or recent_distinct_sources < 2 or avg_confidence < 0.65:
            continue
        summaries.append(
            EmergingThemeSummary(
                theme=theme,
                recent_weekly_volume=recent_weekly_volume,
                baseline_weekly_volume=baseline_weekly_volume,
                recent_distinct_sources=recent_distinct_sources,
                avg_confidence=avg_confidence,
                recent_negative_rate=recent_negative_rate,
                emergence_score=emergence_score,
            )
        )
    return sorted(summaries, key=lambda item: (item.emergence_score * -1, item.theme))


def build_aggregation_snapshot(
    *,
    records: list[AnalyticsRecord],
    reference_day: date | None = None,
) -> AggregationSnapshot:
    """Compute all view-like analytics outputs from normalized records."""
    return AggregationSnapshot(
        daily_sentiment=compute_daily_sentiment_summary(records),
        theme_summary=compute_theme_summary(records),
        feature_summary=compute_feature_summary(records),
        segment_summary=compute_segment_summary(records),
        emerging_themes=compute_emerging_themes(records, reference_day=reference_day),
    )
