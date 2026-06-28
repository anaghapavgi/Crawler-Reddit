from __future__ import annotations

from datetime import UTC, datetime

from reddit_intelligence.db.repositories import InMemoryRunRepository
from reddit_intelligence.models import DeletionEvent


def test_run_repository_records_start_finalize_and_fetch() -> None:
    repo = InMemoryRunRepository()
    run_id = repo.start_crawl_run(trigger_source="fixture")
    repo.finalize_crawl_run(
        run_id=run_id,
        status="success",
        metrics={
            "posts_seen": 5,
            "posts_upserted": 4,
            "comments_seen": 10,
            "comments_upserted": 8,
            "errors_count": 0,
            "rate_limit_remaining": 88,
        },
    )
    run = repo.get_crawl_run(run_id)
    assert run is not None
    assert run.status == "success"
    assert run.posts_seen == 5
    assert run.rate_limit_remaining == 88.0


def test_run_repository_records_deletion_events() -> None:
    repo = InMemoryRunRepository()
    run_id = repo.start_crawl_run(trigger_source="fixture")
    events = [
        DeletionEvent(
            source_type="post",
            source_reddit_id="p1",
            detected_at=datetime.now(tz=UTC),
            action_taken="content_deleted_detected",
            originating_job_id=run_id,
        )
    ]
    recorded = repo.record_deletion_events(run_id=run_id, events=events)
    assert recorded == 1
    assert len(repo.list_deletion_events()) == 1


def test_run_repository_tracks_analysis_runs() -> None:
    repo = InMemoryRunRepository()
    run_id = repo.start_analysis_run(
        model_name="demo-deterministic-v1",
        prompt_version="v1",
        metadata={"demo_mode": True},
    )
    repo.finalize_analysis_run(
        run_id=run_id,
        status="success",
        records_attempted=10,
        records_succeeded=8,
        records_failed=1,
        records_skipped=1,
        input_tokens=120,
        output_tokens=240,
        estimated_cost_usd=0,
        estimated_cost_inr=0,
    )
    run = repo.get_analysis_run(run_id)
    assert run is not None
    assert run.status == "success"
    assert run.records_attempted == 10
    assert run.records_succeeded == 8


def test_run_repository_retry_queue_deduplicates_and_reserves_due_failures() -> None:
    repo = InMemoryRunRepository()
    first_id = repo.record_pipeline_failure(
        source_type="comment",
        source_reddit_id="c1",
        stage="analysis",
        error_category="provider_failure",
        last_error="temporary timeout",
        next_retry_at=datetime(2026, 1, 1, tzinfo=UTC),
    )
    second_id = repo.record_pipeline_failure(
        source_type="comment",
        source_reddit_id="c1",
        stage="analysis",
        error_category="provider_failure",
        last_error="updated timeout",
        next_retry_at=datetime(2026, 1, 1, tzinfo=UTC),
    )
    assert first_id == second_id
    assert len(repo.list_pipeline_failures(stage="analysis")) == 1

    reserved = repo.reserve_failures_for_retry(
        stage="analysis",
        now=datetime(2026, 1, 1, tzinfo=UTC),
        limit=10,
    )
    assert len(reserved) == 1
    assert reserved[0].attempt_count == 1
    assert repo.resolve_pipeline_failure(reserved[0].failure_id) is True
    assert len(repo.list_pipeline_failures(stage="analysis")) == 0
