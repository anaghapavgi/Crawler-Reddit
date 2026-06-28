from __future__ import annotations

from datetime import UTC, date, datetime

import reddit_intelligence.dashboard.data_access as dashboard_data_access
from reddit_intelligence.analytics import (
    DashboardAnalyticsBundle,
    PipelineHealthSnapshot,
    build_aggregation_snapshot,
    compute_kpi_snapshot,
    compute_sentiment_trend,
    compute_volume_trend,
)
from reddit_intelligence.analytics.aggregates import AnalyticsRecord
from reddit_intelligence.dashboard.data_access import DashboardFilters, apply_dashboard_filters


def _record(
    *,
    source_reddit_id: str,
    subreddit: str,
    theme: str,
    feature: str,
    segment: str,
    sentiment_label: str,
    sentiment_score: float,
) -> AnalyticsRecord:
    return AnalyticsRecord(
        day=date(2026, 1, 20),
        subreddit=subreddit,
        source_type="comment",
        source_reddit_id=source_reddit_id,
        sentiment_label=sentiment_label,
        sentiment_score=sentiment_score,
        theme=theme,
        subtheme="general",
        feature=feature,
        user_segment=segment,
        pain_point="",
        severity=2,
        confidence=0.8,
        sarcasm_detected=False,
        relevant=True,
        is_deleted=False,
    )


def _bundle() -> DashboardAnalyticsBundle:
    records = [
        _record(
            source_reddit_id="a",
            subreddit="spotify",
            theme="pricing",
            feature="Search",
            segment="unknown",
            sentiment_label="negative",
            sentiment_score=-0.3,
        ),
        _record(
            source_reddit_id="b",
            subreddit="truespotify",
            theme="reliability",
            feature="Autoplay",
            segment="power_users",
            sentiment_label="positive",
            sentiment_score=0.4,
        ),
    ]
    return DashboardAnalyticsBundle(
        source="demo_csv",
        records=records,
        snapshot=build_aggregation_snapshot(records=records),
        kpis=compute_kpi_snapshot(records, days=30, reference_day=date(2026, 1, 21)),
        volume_trend=compute_volume_trend(records, days=30, reference_day=date(2026, 1, 21)),
        sentiment_trend=compute_sentiment_trend(records, days=30, reference_day=date(2026, 1, 21)),
        pipeline_health=PipelineHealthSnapshot(
            computed_at=datetime(2026, 1, 21, tzinfo=UTC),
            latest_crawl_run_id="crawl-1",
            latest_crawl_status="success",
            latest_crawl_finished_at=datetime(2026, 1, 20, tzinfo=UTC),
            data_freshness_seconds=3600.0,
            latest_analysis_run_id="analysis-1",
            latest_analysis_status="success",
            latest_analysis_finished_at=datetime(2026, 1, 20, tzinfo=UTC),
            pending_records=0,
            failed_records=0,
            stale_records=0,
            complete_records=2,
            cumulative_estimated_cost_inr=0.0,
            crawl_success_rate_30d=1.0,
        ),
    )


def test_build_filter_options_and_apply_filters() -> None:
    bundle = _bundle()
    options = dashboard_data_access.build_filter_options(bundle)
    assert options["subreddits"] == ["spotify", "truespotify"]
    assert options["features"] == ["Autoplay", "Search"]

    filtered = apply_dashboard_filters(
        bundle=bundle,
        filters=DashboardFilters(days=30, subreddits=("spotify",)),
    )
    assert len(filtered.records) == 1
    assert filtered.records[0].subreddit == "spotify"
    assert filtered.kpis.total_relevant_records == 1


def test_apply_filters_empty_state_returns_zero_metrics() -> None:
    bundle = _bundle()
    filtered = apply_dashboard_filters(
        bundle=bundle,
        filters=DashboardFilters(days=30, themes=("non-existent-theme",)),
    )
    assert filtered.records == []
    assert filtered.kpis.total_relevant_records == 0
    assert filtered.snapshot.daily_sentiment == []


def test_load_dashboard_bundle_cache_hits_once(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    call_count = {"value": 0}

    def fake_loader(days: int = 30) -> DashboardAnalyticsBundle:
        call_count["value"] += 1
        return _bundle()

    dashboard_data_access.clear_dashboard_bundle_cache()
    monkeypatch.setattr(dashboard_data_access, "_load_dashboard_bundle_uncached", fake_loader)
    first = dashboard_data_access.load_dashboard_bundle(days=14)
    second = dashboard_data_access.load_dashboard_bundle(days=14)
    assert first.source == "demo_csv"
    assert second.source == "demo_csv"
    assert call_count["value"] == 1
    dashboard_data_access.clear_dashboard_bundle_cache()
