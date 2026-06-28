"""Repository interfaces and demo in-memory implementations."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import UTC, datetime, timedelta
from typing import Protocol
from uuid import uuid4

from reddit_intelligence.models import (
    AnalysisRecord,
    AnalysisRunRecord,
    AnalysisRunStatus,
    CrawlRunRecord,
    CrawlRunStatus,
    DeletionEvent,
    FailureSourceType,
    PipelineFailureRecord,
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

    def upsert_analysis_results(self, results: Iterable[AnalysisRecord]) -> int:
        """Insert or update analysis outputs idempotently by dedup key."""

    def get_latest_analysis(
        self,
        *,
        source_type: str,
        source_reddit_id: str,
    ) -> AnalysisRecord | None:
        """Fetch latest analysis result for a single source record."""


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


class AnalysisRunRepository(Protocol):
    """Persistence interface for analysis runs and retry queue failures."""

    def start_analysis_run(
        self,
        *,
        model_name: str,
        prompt_version: str,
        metadata: dict[str, object] | None = None,
    ) -> str:
        """Create and return an analysis run identifier."""

    def finalize_analysis_run(
        self,
        *,
        run_id: str,
        status: AnalysisRunStatus,
        records_attempted: int,
        records_succeeded: int,
        records_failed: int,
        records_skipped: int,
        input_tokens: int,
        output_tokens: int,
        estimated_cost_usd: float,
        estimated_cost_inr: float,
        error_summary: str | None = None,
        metadata: dict[str, object] | None = None,
    ) -> None:
        """Finalize an analysis run with usage and completion stats."""

    def get_analysis_run(self, run_id: str) -> AnalysisRunRecord | None:
        """Fetch analysis run metadata by ID."""

    def record_pipeline_failure(
        self,
        *,
        source_type: FailureSourceType,
        source_reddit_id: str,
        stage: str,
        error_category: str,
        last_error: str,
        next_retry_at: datetime | None = None,
        metadata: dict[str, object] | None = None,
    ) -> str:
        """Create or update a retry-queue entry and return failure ID."""

    def reserve_failures_for_retry(
        self,
        *,
        stage: str,
        now: datetime,
        limit: int = 50,
    ) -> list[PipelineFailureRecord]:
        """Reserve due failures for retry and bump attempt counts."""

    def resolve_pipeline_failure(self, failure_id: str) -> bool:
        """Mark a failure as resolved and remove it from queue."""

    def list_pipeline_failures(self, stage: str | None = None) -> list[PipelineFailureRecord]:
        """Return queued failures, optionally filtered by stage."""


class InMemoryContentRepository:
    """Credential-free repository for demo mode and unit tests."""

    def __init__(self) -> None:
        self._posts: dict[str, RedditPost] = {}
        self._comments: dict[str, RedditComment] = {}
        self._analysis_results: dict[tuple[str, str, str, str], AnalysisRecord] = {}
        self._latest_analysis_key_by_source: dict[tuple[str, str], tuple[str, str, str, str]] = {}

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

    def upsert_analysis_results(self, results: Iterable[AnalysisRecord]) -> int:
        upserted = 0
        for result in results:
            dedup_key = (
                result.source_type,
                result.source_reddit_id,
                result.prompt_version,
                result.analyzed_text_hash,
            )
            self._analysis_results[dedup_key] = result
            self._latest_analysis_key_by_source[(result.source_type, result.source_reddit_id)] = (
                dedup_key
            )
            upserted += 1
        return upserted

    def get_latest_analysis(
        self,
        *,
        source_type: str,
        source_reddit_id: str,
    ) -> AnalysisRecord | None:
        dedup_key = self._latest_analysis_key_by_source.get((source_type, source_reddit_id))
        if dedup_key is None:
            return None
        return self._analysis_results.get(dedup_key)

    def analysis_count(self) -> int:
        """Return count of persisted analysis rows."""
        return len(self._analysis_results)

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
        self._analysis_runs: dict[str, AnalysisRunRecord] = {}
        self._pipeline_failures: dict[str, PipelineFailureRecord] = {}
        self._pipeline_failure_key_index: dict[tuple[str, str, str, str], str] = {}

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

    def start_analysis_run(
        self,
        *,
        model_name: str,
        prompt_version: str,
        metadata: dict[str, object] | None = None,
    ) -> str:
        run_id = str(uuid4())
        self._analysis_runs[run_id] = AnalysisRunRecord(
            run_id=run_id,
            started_at=datetime.now(tz=UTC),
            status="running",
            model_name=model_name,
            prompt_version=prompt_version,
            metadata=metadata or {},
        )
        return run_id

    def finalize_analysis_run(
        self,
        *,
        run_id: str,
        status: AnalysisRunStatus,
        records_attempted: int,
        records_succeeded: int,
        records_failed: int,
        records_skipped: int,
        input_tokens: int,
        output_tokens: int,
        estimated_cost_usd: float,
        estimated_cost_inr: float,
        error_summary: str | None = None,
        metadata: dict[str, object] | None = None,
    ) -> None:
        record = self._analysis_runs.get(run_id)
        if record is None:
            return
        record.status = status
        record.finished_at = datetime.now(tz=UTC)
        record.records_attempted = records_attempted
        record.records_succeeded = records_succeeded
        record.records_failed = records_failed
        record.records_skipped = records_skipped
        record.input_tokens = input_tokens
        record.output_tokens = output_tokens
        record.estimated_cost_usd = estimated_cost_usd
        record.estimated_cost_inr = estimated_cost_inr
        record.error_summary = error_summary
        record.metadata = metadata or record.metadata

    def get_analysis_run(self, run_id: str) -> AnalysisRunRecord | None:
        return self._analysis_runs.get(run_id)

    def record_pipeline_failure(
        self,
        *,
        source_type: FailureSourceType,
        source_reddit_id: str,
        stage: str,
        error_category: str,
        last_error: str,
        next_retry_at: datetime | None = None,
        metadata: dict[str, object] | None = None,
    ) -> str:
        dedup_key = (source_type, source_reddit_id, stage, error_category)
        now = datetime.now(tz=UTC)
        existing_id = self._pipeline_failure_key_index.get(dedup_key)
        if existing_id is not None and existing_id in self._pipeline_failures:
            existing = self._pipeline_failures[existing_id]
            existing.last_error = last_error
            existing.next_retry_at = next_retry_at
            existing.updated_at = now
            if metadata:
                existing.metadata = metadata
            return existing.failure_id

        failure_id = str(uuid4())
        self._pipeline_failures[failure_id] = PipelineFailureRecord(
            failure_id=failure_id,
            source_type=source_type,
            source_reddit_id=source_reddit_id,
            stage=stage,
            error_category=error_category,
            attempt_count=0,
            last_error=last_error,
            next_retry_at=next_retry_at,
            metadata=metadata or {},
            created_at=now,
            updated_at=now,
        )
        self._pipeline_failure_key_index[dedup_key] = failure_id
        return failure_id

    def reserve_failures_for_retry(
        self,
        *,
        stage: str,
        now: datetime,
        limit: int = 50,
    ) -> list[PipelineFailureRecord]:
        due_failures = [
            failure
            for failure in self._pipeline_failures.values()
            if failure.stage == stage and (failure.next_retry_at is None or failure.next_retry_at <= now)
        ]
        due_failures.sort(key=lambda failure: failure.created_at)
        reserved = due_failures[: max(0, limit)]
        for failure in reserved:
            failure.attempt_count += 1
            failure.updated_at = now
            failure.next_retry_at = now + timedelta(minutes=5)
        return reserved

    def resolve_pipeline_failure(self, failure_id: str) -> bool:
        failure = self._pipeline_failures.pop(failure_id, None)
        if failure is None:
            return False
        dedup_key = (failure.source_type, failure.source_reddit_id, failure.stage, failure.error_category)
        self._pipeline_failure_key_index.pop(dedup_key, None)
        return True

    def list_pipeline_failures(self, stage: str | None = None) -> list[PipelineFailureRecord]:
        failures = list(self._pipeline_failures.values())
        if stage is None:
            return sorted(failures, key=lambda failure: failure.created_at)
        return sorted(
            (failure for failure in failures if failure.stage == stage),
            key=lambda failure: failure.created_at,
        )
