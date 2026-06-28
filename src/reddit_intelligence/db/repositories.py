"""Repository interfaces and demo in-memory implementations."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import UTC, datetime
from typing import Protocol
from uuid import uuid4

from reddit_intelligence.models import (
    CrawlRunRecord,
    CrawlRunStatus,
    DeletionEvent,
    RedditComment,
    RedditPost,
)


def _as_int(value: object, default: int = 0) -> int:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        try:
            return int(value)
        except ValueError:
            return default
    return default


def _as_float(value: object) -> float | None:
    if isinstance(value, bool):
        return float(value)
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return None
    return None


class ContentRepository(Protocol):
    """Persistence interface for normalized Reddit content."""

    def upsert_posts(self, posts: Iterable[RedditPost]) -> int:
        """Insert or update posts idempotently."""

    def upsert_comments(self, comments: Iterable[RedditComment]) -> int:
        """Insert or update comments idempotently."""

    def get_post(self, reddit_id: str) -> RedditPost | None:
        """Fetch a post by Reddit ID."""

    def get_comment(self, reddit_id: str) -> RedditComment | None:
        """Fetch a comment by Reddit ID."""

    def iter_posts(self) -> Iterable[RedditPost]:
        """Iterate over stored posts."""

    def iter_comments(self) -> Iterable[RedditComment]:
        """Iterate over stored comments."""


class CrawlRunRepository(Protocol):
    """Persistence interface for crawl run and deletion event metadata."""

    def start_crawl_run(self, trigger_source: str) -> str:
        """Create and return a crawl run identifier."""

    def finalize_crawl_run(
        self,
        run_id: str,
        status: CrawlRunStatus,
        metrics: dict[str, object],
        error_summary: str | None = None,
    ) -> None:
        """Finalize a run record with metrics and status."""

    def record_deletion_events(
        self,
        run_id: str,
        events: Iterable[DeletionEvent],
    ) -> int:
        """Persist deletion events for a run and return count recorded."""

    def get_crawl_run(self, run_id: str) -> CrawlRunRecord | None:
        """Fetch run metadata by ID."""

    def list_deletion_events(self) -> list[DeletionEvent]:
        """Return all recorded deletion events."""


class InMemoryContentRepository:
    """Credential-free repository for demo mode and unit tests."""

    def __init__(self) -> None:
        self._posts: dict[str, RedditPost] = {}
        self._comments: dict[str, RedditComment] = {}

    def upsert_posts(self, posts: Iterable[RedditPost]) -> int:
        upserted = 0
        for post in posts:
            existing = self._posts.get(post.reddit_id)
            if existing is not None:
                merged_queries = sorted(set(existing.matched_queries) | set(post.matched_queries))
                post = post.model_copy(update={"matched_queries": merged_queries})
            self._posts[post.reddit_id] = post
            upserted += 1
        return upserted

    def upsert_comments(self, comments: Iterable[RedditComment]) -> int:
        upserted = 0
        for comment in comments:
            self._comments[comment.reddit_id] = comment
            upserted += 1
        return upserted

    def get_post(self, reddit_id: str) -> RedditPost | None:
        return self._posts.get(reddit_id)

    def get_comment(self, reddit_id: str) -> RedditComment | None:
        return self._comments.get(reddit_id)

    def iter_posts(self) -> Iterable[RedditPost]:
        return self._posts.values()

    def iter_comments(self) -> Iterable[RedditComment]:
        return self._comments.values()

    def post_count(self) -> int:
        """Return current post count in repository."""
        return len(self._posts)

    def comment_count(self) -> int:
        """Return current comment count in repository."""
        return len(self._comments)


class InMemoryRunRepository:
    """In-memory run/deletion repository used in demo mode and tests."""

    def __init__(self) -> None:
        self._runs: dict[str, CrawlRunRecord] = {}
        self._deletion_events: list[DeletionEvent] = []

    def start_crawl_run(self, trigger_source: str) -> str:
        run_id = str(uuid4())
        self._runs[run_id] = CrawlRunRecord(
            run_id=run_id,
            started_at=datetime.now(tz=UTC),
            trigger_source=trigger_source,
            status="running",
            metadata={},
        )
        return run_id

    def finalize_crawl_run(
        self,
        run_id: str,
        status: CrawlRunStatus,
        metrics: dict[str, object],
        error_summary: str | None = None,
    ) -> None:
        record = self._runs.get(run_id)
        if record is None:
            return
        record.status = status
        record.finished_at = datetime.now(tz=UTC)
        record.error_summary = error_summary
        record.subreddits_count = _as_int(metrics.get("subreddits_count", 0))
        record.queries_count = _as_int(metrics.get("queries_count", 0))
        record.api_requests = _as_int(metrics.get("api_requests", 0))
        record.posts_seen = _as_int(metrics.get("posts_seen", 0))
        record.posts_upserted = _as_int(metrics.get("posts_upserted", 0))
        record.comments_seen = _as_int(metrics.get("comments_seen", 0))
        record.comments_upserted = _as_int(metrics.get("comments_upserted", 0))
        record.records_queued_for_analysis = _as_int(metrics.get("records_queued_for_analysis", 0))
        record.errors_count = _as_int(metrics.get("errors_count", 0))
        raw_rate_limit = metrics.get("rate_limit_remaining")
        record.rate_limit_remaining = _as_float(raw_rate_limit)
        record.metadata = metrics

    def record_deletion_events(
        self,
        run_id: str,
        events: Iterable[DeletionEvent],
    ) -> int:
        del run_id
        collected = list(events)
        self._deletion_events.extend(collected)
        return len(collected)

    def get_crawl_run(self, run_id: str) -> CrawlRunRecord | None:
        return self._runs.get(run_id)

    def list_deletion_events(self) -> list[DeletionEvent]:
        return list(self._deletion_events)
