from __future__ import annotations

import csv
from datetime import UTC, date, datetime
from io import StringIO

from reddit_intelligence.analytics import (
    DashboardAnalyticsBundle,
    PipelineHealthSnapshot,
    build_aggregation_snapshot,
    compute_kpi_snapshot,
    compute_sentiment_trend,
    compute_volume_trend,
)
from reddit_intelligence.analytics.aggregates import AnalyticsRecord
from reddit_intelligence.dashboard import app
from reddit_intelligence.dashboard.pages import (
    assistant,
    explorer,
    features,
    overview,
    pain_points,
    pipeline_health,
    segments,
    sentiment,
    trends,
)


def test_dashboard_page_modules_export_render_functions() -> None:
    assert callable(overview.render)
    assert callable(sentiment.render)
    assert callable(pain_points.render)
    assert callable(features.render)
    assert callable(segments.render)
    assert callable(trends.render)
    assert callable(explorer.render)
    assert callable(assistant.render)
    assert callable(pipeline_health.render)


def test_dashboard_empty_state_message_text() -> None:
    assert app.empty_state_message() == "No records match current dashboard filters."


def _bundle_for_page_helpers() -> DashboardAnalyticsBundle:
    records = [
        AnalyticsRecord(
            day=date(2026, 1, 20),
            subreddit="spotify",
            source_type="comment",
            source_reddit_id="c1",
            sentiment_label="negative",
            sentiment_score=-0.7,
            theme="pricing",
            subtheme="tiers",
            feature="Search",
            user_segment="power_users",
            pain_point="=SUM(A1:A2)",
            severity=5,
            confidence=0.9,
            sarcasm_detected=False,
            relevant=True,
            is_deleted=False,
        ),
        AnalyticsRecord(
            day=date(2026, 1, 20),
            subreddit="truespotify",
            source_type="post",
            source_reddit_id="p2",
            sentiment_label="negative",
            sentiment_score=-0.4,
            theme="reliability",
            subtheme="playback",
            feature="Autoplay",
            user_segment="unknown",
            pain_point="@cmd",
            severity=4,
            confidence=0.82,
            sarcasm_detected=False,
            relevant=True,
            is_deleted=False,
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


def test_assistant_evidence_snippets_are_bounded_and_sorted() -> None:
    bundle = _bundle_for_page_helpers()
    snippets = assistant.build_evidence_snippets(bundle, limit=1)
    assert len(snippets) == 1
    assert snippets[0]["source_id"] == "c1"
    assert snippets[0]["snippet"] == "=SUM(A1:A2)"


def test_explorer_csv_export_sanitizes_formula_cells() -> None:
    bundle = _bundle_for_page_helpers()
    rows = explorer.build_explorer_rows(bundle, max_rows=2)
    payload = explorer.build_explorer_export_csv(rows)
    parsed_rows = list(csv.DictReader(StringIO(payload)))
    assert parsed_rows[0]["pain_point"] == "'=SUM(A1:A2)"
    assert parsed_rows[1]["pain_point"] == "'@cmd"


def test_sanitize_csv_cell_handles_whitespace_prefixed_formulas() -> None:
    assert explorer.sanitize_csv_cell("  +SUM(A1:A3)") == "'  +SUM(A1:A3)"
    assert explorer.sanitize_csv_cell("\tunsafe") == "'\tunsafe"
    assert explorer.sanitize_csv_cell("safe text") == "safe text"
