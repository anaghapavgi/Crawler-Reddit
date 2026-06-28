from __future__ import annotations

from datetime import date, timedelta

from reddit_intelligence.analytics.aggregates import (
    AnalyticsRecord,
    build_aggregation_snapshot,
    compute_emerging_themes,
    compute_feature_summary,
    compute_theme_summary,
)
from reddit_intelligence.analytics.metrics import compute_kpi_snapshot


def _record(
    *,
    day: date,
    source_reddit_id: str,
    sentiment_label: str = "neutral",
    sentiment_score: float = 0.0,
    theme: str = "other",
    subtheme: str = "general",
    feature: str = "Unknown",
    user_segment: str = "unknown",
    pain_point: str = "",
    severity: int = 2,
    confidence: float = 0.8,
    sarcasm_detected: bool = False,
    relevant: bool = True,
    is_deleted: bool = False,
) -> AnalyticsRecord:
    return AnalyticsRecord(
        day=day,
        subreddit="spotify",
        source_type="comment",
        source_reddit_id=source_reddit_id,
        sentiment_label=sentiment_label,
        sentiment_score=sentiment_score,
        theme=theme,
        subtheme=subtheme,
        feature=feature,
        user_segment=user_segment,
        pain_point=pain_point,
        severity=severity,
        confidence=confidence,
        sarcasm_detected=sarcasm_detected,
        relevant=relevant,
        is_deleted=is_deleted,
    )


def test_theme_summary_formula_parity() -> None:
    day = date(2026, 1, 10)
    rows = [
        _record(day=day, source_reddit_id="a", theme="pricing", subtheme="monthly", sentiment_label="negative"),
        _record(day=day, source_reddit_id="b", theme="pricing", subtheme="monthly", sentiment_label="positive"),
    ]
    summary = compute_theme_summary(rows)
    assert len(summary) == 1
    assert summary[0].record_count == 2
    assert summary[0].negative_rate == 0.5


def test_feature_summary_top_theme_tie_breaks_alphabetically() -> None:
    day = date(2026, 1, 10)
    rows = [
        _record(day=day, source_reddit_id="a", feature="Search", theme="zeta"),
        _record(day=day, source_reddit_id="b", feature="Search", theme="alpha"),
    ]
    summary = compute_feature_summary(rows)
    assert len(summary) == 1
    assert summary[0].top_theme == "alpha"


def test_kpi_snapshot_excludes_deleted_records() -> None:
    day = date(2026, 1, 10)
    rows = [
        _record(day=day, source_reddit_id="keep", sentiment_score=0.2),
        _record(day=day, source_reddit_id="deleted", sentiment_score=-0.9, is_deleted=True),
    ]
    kpis = compute_kpi_snapshot(rows, days=30, reference_day=date(2026, 1, 11))
    assert kpis.total_relevant_records == 1
    assert kpis.avg_sentiment_score == 0.2


def test_emerging_theme_zero_baseline_uses_floor_divisor() -> None:
    reference_day = date(2026, 1, 31)
    recent_day = reference_day - timedelta(days=3)
    rows = [
        _record(
            day=recent_day,
            source_reddit_id=f"r{i}",
            theme="spike_theme",
            confidence=0.9,
            sentiment_label="negative" if i % 2 == 0 else "neutral",
        )
        for i in range(5)
    ]
    emerging = compute_emerging_themes(rows, reference_day=reference_day)
    assert len(emerging) == 1
    assert emerging[0].theme == "spike_theme"
    assert emerging[0].baseline_weekly_volume == 0.0
    assert emerging[0].emergence_score == 5.0


def test_snapshot_contains_all_view_like_outputs() -> None:
    rows = [
        _record(day=date(2026, 1, 10), source_reddit_id="a", feature="Search", theme="navigation"),
        _record(day=date(2026, 1, 11), source_reddit_id="b", feature="Search", theme="navigation"),
    ]
    snapshot = build_aggregation_snapshot(records=rows, reference_day=date(2026, 1, 12))
    assert len(snapshot.daily_sentiment) == 2
    assert len(snapshot.theme_summary) == 1
    assert len(snapshot.feature_summary) == 1
    assert len(snapshot.segment_summary) == 1
