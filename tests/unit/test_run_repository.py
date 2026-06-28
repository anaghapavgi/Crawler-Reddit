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
