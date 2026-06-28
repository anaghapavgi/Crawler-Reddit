from __future__ import annotations

from datetime import UTC, datetime, timedelta

from reddit_intelligence.analytics.pipeline_health import (
    compute_pipeline_health_from_repositories,
    pipeline_health_from_view_row,
)
from reddit_intelligence.db.repositories import InMemoryContentRepository, InMemoryRunRepository
from reddit_intelligence.models import AnalysisRecord, RedditComment, RedditPost


def _post(*, reddit_id: str, status: str, created: datetime) -> RedditPost:
    return RedditPost(
        reddit_id=reddit_id,
        subreddit="spotify",
        permalink=f"https://reddit.com/{reddit_id}",
        created_utc=created,
        content_hash=f"h-{reddit_id}",
        analysis_status=status,
    )


def _comment(*, reddit_id: str, post_id: str, status: str, created: datetime) -> RedditComment:
    return RedditComment(
        reddit_id=reddit_id,
        post_reddit_id=post_id,
        subreddit="spotify",
        permalink=f"https://reddit.com/{reddit_id}",
        created_utc=created,
        content_hash=f"h-{reddit_id}",
        analysis_status=status,
    )


def test_pipeline_health_from_repositories_tracks_counts_and_rates() -> None:
    now = datetime(2026, 2, 1, tzinfo=UTC)
    content_repo = InMemoryContentRepository()
    run_repo = InMemoryRunRepository()

    content_repo.upsert_posts(
        [_post(reddit_id="p1", status="pending", created=now - timedelta(days=3))]
    )
    content_repo.upsert_comments(
        [
            _comment(
                reddit_id="c1",
                post_id="p1",
                status="failed",
                created=now - timedelta(days=3),
            ),
            _comment(
                reddit_id="c2",
                post_id="p1",
                status="stale",
                created=now - timedelta(days=2),
            ),
        ]
    )
    content_repo.upsert_analysis_results(
        [
            AnalysisRecord(
                source_type="comment",
                source_reddit_id="c3",
                analyzed_text_hash="hash-c3",
                prompt_version="v1",
                model_name="demo",
                relevant=True,
                sentiment_label="neutral",
                sentiment_score=0.0,
                intensity=2,
                severity=2,
                confidence=0.6,
            )
        ]
    )

    crawl_success_id = run_repo.start_crawl_run(trigger_source="fixture")
    run_repo.finalize_crawl_run(crawl_success_id, status="success", metrics={})
    run_success = run_repo.get_crawl_run(crawl_success_id)
    assert run_success is not None
    run_success.started_at = now - timedelta(days=5)
    run_success.finished_at = now - timedelta(days=4)

    crawl_failed_id = run_repo.start_crawl_run(trigger_source="fixture")
    run_repo.finalize_crawl_run(crawl_failed_id, status="failed", metrics={})
    run_failed = run_repo.get_crawl_run(crawl_failed_id)
    assert run_failed is not None
    run_failed.started_at = now - timedelta(days=2)
    run_failed.finished_at = now - timedelta(days=2, hours=1)

    analysis_run_id = run_repo.start_analysis_run(
        model_name="demo",
        prompt_version="v1",
    )
    run_repo.finalize_analysis_run(
        run_id=analysis_run_id,
        status="success",
        records_attempted=4,
        records_succeeded=3,
        records_failed=1,
        records_skipped=0,
        input_tokens=100,
        output_tokens=120,
        estimated_cost_usd=0.1,
        estimated_cost_inr=8.5,
    )
    run_repo.record_pipeline_failure(
        source_type="comment",
        source_reddit_id="c1",
        stage="analysis",
        error_category="provider_failure",
        last_error="temporary timeout",
    )

    snapshot = compute_pipeline_health_from_repositories(
        content_repository=content_repo,
        run_repository=run_repo,
        now=now,
    )
    assert snapshot.latest_crawl_run_id == crawl_failed_id
    assert snapshot.pending_records == 1
    assert snapshot.failed_records == 1
    assert snapshot.stale_records == 1
    assert snapshot.complete_records == 1
    assert snapshot.cumulative_estimated_cost_inr == 8.5
    assert snapshot.crawl_success_rate_30d == 0.5
    assert snapshot.data_freshness_seconds == 176400.0


def test_pipeline_health_from_view_row_parses_values() -> None:
    now = datetime(2026, 2, 1, 12, tzinfo=UTC)
    row = {
        "computed_at": "2026-02-01T11:59:00+00:00",
        "latest_crawl_run_id": "crawl-1",
        "latest_crawl_status": "success",
        "latest_crawl_finished_at": "2026-02-01T11:00:00+00:00",
        "latest_analysis_run_id": "analysis-1",
        "latest_analysis_status": "partial",
        "latest_analysis_finished_at": "2026-02-01T11:30:00+00:00",
        "pending_records": 5,
        "failed_records": 1,
        "stale_records": 2,
        "complete_records": 12,
        "cumulative_estimated_cost_inr": "23.4",
        "crawl_success_rate_30d": "0.75",
    }
    snapshot = pipeline_health_from_view_row(row, now=now)
    assert snapshot.latest_crawl_run_id == "crawl-1"
    assert snapshot.failed_records == 1
    assert snapshot.cumulative_estimated_cost_inr == 23.4
    assert snapshot.crawl_success_rate_30d == 0.75
    assert snapshot.data_freshness_seconds == 3600.0
