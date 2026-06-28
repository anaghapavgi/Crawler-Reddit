"""Deletion synchronization hooks."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from reddit_intelligence.db.repositories import ContentRepository, CrawlRunRepository
from reddit_intelligence.models import DeletionEvent


@dataclass(slots=True)
class DeletionSyncResult:
    """Summary of deletion sync operation."""

    deleted_posts_found: int
    deleted_comments_found: int
    events_recorded: int


def sync_deleted_content(
    content_repository: ContentRepository,
    run_repository: CrawlRunRepository | None = None,
    run_id: str | None = None,
) -> DeletionSyncResult:
    """Scan repository for deleted content and optionally record deletion events."""
    events: list[DeletionEvent] = []
    deleted_posts = 0
    deleted_comments = 0

    for post in content_repository.iter_posts():
        if post.is_deleted:
            deleted_posts += 1
            events.append(
                DeletionEvent(
                    source_type="post",
                    source_reddit_id=post.reddit_id,
                    detected_at=datetime.now(tz=UTC),
                    action_taken="deletion_sync_confirmed",
                    originating_job_id=run_id,
                )
            )
    for comment in content_repository.iter_comments():
        if comment.is_deleted:
            deleted_comments += 1
            events.append(
                DeletionEvent(
                    source_type="comment",
                    source_reddit_id=comment.reddit_id,
                    detected_at=datetime.now(tz=UTC),
                    action_taken="deletion_sync_confirmed",
                    originating_job_id=run_id,
                )
            )

    events_recorded = 0
    if run_repository is not None and run_id is not None and events:
        events_recorded = run_repository.record_deletion_events(run_id=run_id, events=events)

    return DeletionSyncResult(
        deleted_posts_found=deleted_posts,
        deleted_comments_found=deleted_comments,
        events_recorded=events_recorded,
    )
