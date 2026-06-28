from __future__ import annotations

from datetime import UTC, datetime

from reddit_intelligence.db.repositories import InMemoryContentRepository, InMemoryRunRepository
from reddit_intelligence.models import RedditComment, RedditPost
from reddit_intelligence.reddit.deletion_sync import sync_deleted_content


def test_sync_deleted_content_records_events() -> None:
    content_repo = InMemoryContentRepository()
    run_repo = InMemoryRunRepository()
    run_id = run_repo.start_crawl_run(trigger_source="deletion_sync")
    created = datetime(2026, 1, 1, tzinfo=UTC)

    content_repo.upsert_posts(
        [
            RedditPost(
                reddit_id="p_deleted",
                subreddit="spotify",
                permalink="https://reddit.com/r/spotify/p_deleted",
                created_utc=created,
                content_hash="hp",
                is_deleted=True,
            )
        ]
    )
    content_repo.upsert_comments(
        [
            RedditComment(
                reddit_id="c_deleted",
                post_reddit_id="p_deleted",
                subreddit="spotify",
                permalink="https://reddit.com/r/spotify/comments/c_deleted",
                created_utc=created,
                content_hash="hc",
                is_deleted=True,
            )
        ]
    )

    result = sync_deleted_content(content_repo, run_repository=run_repo, run_id=run_id)
    assert result.deleted_posts_found == 1
    assert result.deleted_comments_found == 1
    assert result.events_recorded == 2
