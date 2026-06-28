"""Reddit collection orchestration."""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

import prawcore
from tenacity import retry, stop_after_attempt, wait_exponential_jitter

from reddit_intelligence.config import RedditResearch
from reddit_intelligence.db.repositories import ContentRepository, CrawlRunRepository
from reddit_intelligence.models import CrawlRunStatus, DeletionEvent, RedditComment, RedditPost
from reddit_intelligence.processing.relevance import RelevanceScorer
from reddit_intelligence.reddit.client import get_rate_limit_remaining
from reddit_intelligence.reddit.mapper import map_comment, map_submission


@dataclass(slots=True)
class CrawlRunMetrics:
    """Counters and metadata from a crawl execution."""

    crawl_run_id: str | None = None
    subreddits_count: int = 0
    queries_count: int = 0
    api_requests: int = 0
    posts_seen: int = 0
    posts_upserted: int = 0
    comments_seen: int = 0
    comments_upserted: int = 0
    records_queued_for_analysis: int = 0
    errors_count: int = 0
    rate_limit_remaining: float | None = None
    error_categories: list[str] = field(default_factory=list)
    deleted_posts_detected: int = 0
    deleted_comments_detected: int = 0
    deletion_events_recorded: int = 0


def classify_reddit_exception(exc: Exception) -> str:
    """Map API/runtime exceptions into safe retry/error categories."""
    if isinstance(exc, TimeoutError):
        return "timeout"
    if isinstance(exc, PermissionError):
        return "forbidden_private_subreddit"
    if isinstance(exc, ConnectionError):
        return "network_error"
    if isinstance(exc, prawcore.exceptions.OAuthException):
        return "invalid_credentials"
    if isinstance(exc, prawcore.exceptions.Forbidden):
        return "forbidden_private_subreddit"
    if isinstance(exc, prawcore.exceptions.NotFound):
        return "not_found"
    if isinstance(exc, (prawcore.exceptions.RequestException, TimeoutError)):
        return "network_error"
    if isinstance(exc, prawcore.exceptions.ServerError):
        return "reddit_server_error"
    if isinstance(exc, prawcore.exceptions.ResponseException):
        return "rate_limit_or_response_error"
    error_text = str(exc).lower()
    if "rate limit" in error_text:
        return "rate_limit_or_response_error"
    if "database" in error_text or "postgres" in error_text or "supabase" in error_text:
        return "database_error"
    if "forbidden" in error_text or "private subreddit" in error_text:
        return "forbidden_private_subreddit"
    if "invalid credential" in error_text or "oauth" in error_text:
        return "invalid_credentials"
    return "unknown_error"


class RedditCollector:
    """Collect posts/comments from fixtures or Reddit API search responses."""

    def __init__(
        self,
        repository: ContentRepository,
        relevance_scorer: RelevanceScorer,
        max_comments_per_post: int,
        minimum_post_score: int,
        run_repository: CrawlRunRepository | None = None,
    ) -> None:
        self._repository = repository
        self._relevance_scorer = relevance_scorer
        self._max_comments_per_post = max_comments_per_post
        self._minimum_post_score = minimum_post_score
        self._run_repository = run_repository

    def collect_from_fixture(
        self,
        posts_path: Path,
        comments_path: Path,
        matched_query: str = "fixture",
    ) -> CrawlRunMetrics:
        """Collect and upsert content from local JSON fixtures."""
        run_id = self._start_run("fixture")
        try:
            with posts_path.open("r", encoding="utf-8") as posts_file:
                posts_payload = json.load(posts_file)
            with comments_path.open("r", encoding="utf-8") as comments_file:
                comments_payload = json.load(comments_file)

            if not isinstance(posts_payload, list) or not isinstance(comments_payload, list):
                msg = "Fixture files must contain JSON arrays."
                raise ValueError(msg)

            comments_by_post: dict[str, list[object]] = {}
            for raw_comment in comments_payload:
                if not isinstance(raw_comment, dict):
                    continue
                post_id = str(raw_comment.get("post_reddit_id", raw_comment.get("link_id", "")))
                if post_id.startswith("t3_"):
                    post_id = post_id.split("_", maxsplit=1)[1]
                if post_id == "":
                    continue
                comments_by_post.setdefault(post_id, []).append(raw_comment)

            metrics = self.collect_from_items(
                submissions=posts_payload,
                comments_by_post=comments_by_post,
                matched_query=matched_query,
                run_id=run_id,
            )
            self._finalize_run(run_id, metrics, status="success")
            return metrics
        except Exception as exc:
            failed_metrics = CrawlRunMetrics(crawl_run_id=run_id, errors_count=1)
            failed_metrics.error_categories.append(classify_reddit_exception(exc))
            self._finalize_run(run_id, failed_metrics, status="failed", error_summary=str(exc))
            raise

    def collect_incremental(
        self, reddit_client: object, research: RedditResearch
    ) -> CrawlRunMetrics:
        """Collect submissions/comments from configured subreddits and queries."""
        run_id = self._start_run("incremental")
        metrics = CrawlRunMetrics(
            crawl_run_id=run_id,
            subreddits_count=len(research.subreddits),
            queries_count=len(research.search_queries),
            rate_limit_remaining=get_rate_limit_remaining(reddit_client),
        )
        subreddit_factory = getattr(reddit_client, "subreddit", None)
        if not callable(subreddit_factory):
            msg = "Reddit client is missing subreddit() API."
            raise RuntimeError(msg)

        for subreddit_name in research.subreddits:
            subreddit_obj = subreddit_factory(subreddit_name)
            for query in research.search_queries:
                metrics.api_requests += 1
                try:
                    submissions = self._search_with_retry(
                        subreddit_obj=subreddit_obj,
                        query=query,
                        sort=research.sort,
                        time_filter=research.time_filter,
                        limit=research.posts_per_query,
                    )
                    run_metrics = self.collect_from_items(
                        submissions=submissions,
                        matched_query=query,
                        minimum_post_score=research.minimum_post_score,
                        max_comments_per_post=research.max_comments_per_post,
                        rate_limit_remaining=get_rate_limit_remaining(reddit_client),
                        run_id=run_id,
                    )
                    metrics.posts_seen += run_metrics.posts_seen
                    metrics.posts_upserted += run_metrics.posts_upserted
                    metrics.comments_seen += run_metrics.comments_seen
                    metrics.comments_upserted += run_metrics.comments_upserted
                    metrics.records_queued_for_analysis += run_metrics.records_queued_for_analysis
                    metrics.error_categories.extend(run_metrics.error_categories)
                    metrics.errors_count += run_metrics.errors_count
                    metrics.rate_limit_remaining = run_metrics.rate_limit_remaining
                    metrics.deleted_posts_detected += run_metrics.deleted_posts_detected
                    metrics.deleted_comments_detected += run_metrics.deleted_comments_detected
                    metrics.deletion_events_recorded += run_metrics.deletion_events_recorded
                except (
                    Exception
                ) as exc:  # pragma: no cover - exercised via integration tests with fakes
                    metrics.errors_count += 1
                    metrics.error_categories.append(classify_reddit_exception(exc))
        status: CrawlRunStatus = "success"
        if metrics.errors_count > 0:
            if metrics.posts_upserted > 0 or metrics.comments_upserted > 0:
                status = "partial"
            else:
                status = "failed"
        self._finalize_run(run_id, metrics, status=status)
        return metrics

    @retry(reraise=True, stop=stop_after_attempt(3), wait=wait_exponential_jitter(initial=1, max=8))
    def _search_with_retry(
        self,
        subreddit_obj: object,
        query: str,
        sort: str,
        time_filter: str,
        limit: int,
    ) -> list[object]:
        search = getattr(subreddit_obj, "search", None)
        if not callable(search):
            msg = "Subreddit object does not expose search()."
            raise RuntimeError(msg)
        results = search(query=query, sort=sort, time_filter=time_filter, limit=limit)
        return list(results)

    def collect_from_items(
        self,
        submissions: Iterable[object],
        comments_by_post: Mapping[str, Sequence[object]] | None = None,
        matched_query: str = "",
        minimum_post_score: int | None = None,
        max_comments_per_post: int | None = None,
        rate_limit_remaining: float | None = None,
        run_id: str | None = None,
    ) -> CrawlRunMetrics:
        """Normalize, score, and persist posts/comments from submission-like objects."""
        metrics = CrawlRunMetrics(crawl_run_id=run_id, rate_limit_remaining=rate_limit_remaining)
        comments_index = comments_by_post or {}
        post_threshold = (
            self._minimum_post_score if minimum_post_score is None else minimum_post_score
        )
        comment_cap = (
            self._max_comments_per_post if max_comments_per_post is None else max_comments_per_post
        )

        posts_to_upsert: list[RedditPost] = []
        comments_to_upsert: list[RedditComment] = []
        deletion_events: list[DeletionEvent] = []

        for submission in submissions:
            post = map_submission(
                submission,
                matched_queries=[matched_query] if matched_query else [],
            )
            metrics.posts_seen += 1
            scored_post = self._relevance_scorer.score(f"{post.title}\n{post.body}".strip())
            post = post.model_copy(update={"relevance_score": scored_post.score})
            posts_to_upsert.append(post)
            if post.is_deleted:
                metrics.deleted_posts_detected += 1
                deletion_events.append(
                    DeletionEvent(
                        source_type="post",
                        source_reddit_id=post.reddit_id,
                        detected_at=datetime.now(tz=UTC),
                        action_taken="content_deleted_detected",
                        originating_job_id=run_id,
                    )
                )
            if scored_post.is_relevant:
                metrics.records_queued_for_analysis += 1

            if post.score < post_threshold:
                continue

            raw_comments = self._extract_comments_for_post(
                post.reddit_id, submission, comments_index
            )
            for raw_comment in raw_comments[:comment_cap]:
                comment = map_comment(raw_comment, post_reddit_id=post.reddit_id)
                comment_score = self._relevance_scorer.score(comment.body)
                comment = comment.model_copy(update={"relevance_score": comment_score.score})
                comments_to_upsert.append(comment)
                if comment.is_deleted:
                    metrics.deleted_comments_detected += 1
                    deletion_events.append(
                        DeletionEvent(
                            source_type="comment",
                            source_reddit_id=comment.reddit_id,
                            detected_at=datetime.now(tz=UTC),
                            action_taken="content_deleted_detected",
                            originating_job_id=run_id,
                        )
                    )
                metrics.comments_seen += 1
                if comment_score.is_relevant:
                    metrics.records_queued_for_analysis += 1

        metrics.posts_upserted = self._repository.upsert_posts(posts_to_upsert)
        metrics.comments_upserted = self._repository.upsert_comments(comments_to_upsert)
        metrics.deletion_events_recorded = self._record_deletion_events(run_id, deletion_events)
        return metrics

    def _extract_comments_for_post(
        self,
        post_reddit_id: str,
        submission: object,
        comments_index: Mapping[str, Sequence[object]],
    ) -> list[object]:
        indexed = comments_index.get(post_reddit_id)
        if indexed is not None:
            return list(indexed)

        comments_attr = getattr(submission, "comments", None)
        if comments_attr is None:
            return []
        replace_more = getattr(comments_attr, "replace_more", None)
        if callable(replace_more):
            # Explicitly bounded to avoid unbounded replace_more(limit=None).
            replace_more(limit=0)
        list_method = getattr(comments_attr, "list", None)
        if callable(list_method):
            return list(list_method())
        if isinstance(comments_attr, Sequence):
            return list(comments_attr)
        return []

    def _start_run(self, trigger_source: str) -> str | None:
        if self._run_repository is None:
            return None
        return self._run_repository.start_crawl_run(trigger_source=trigger_source)

    def _finalize_run(
        self,
        run_id: str | None,
        metrics: CrawlRunMetrics,
        status: CrawlRunStatus,
        error_summary: str | None = None,
    ) -> None:
        if self._run_repository is None or run_id is None:
            return
        self._run_repository.finalize_crawl_run(
            run_id=run_id,
            status=status,
            metrics={
                "subreddits_count": metrics.subreddits_count,
                "queries_count": metrics.queries_count,
                "api_requests": metrics.api_requests,
                "posts_seen": metrics.posts_seen,
                "posts_upserted": metrics.posts_upserted,
                "comments_seen": metrics.comments_seen,
                "comments_upserted": metrics.comments_upserted,
                "records_queued_for_analysis": metrics.records_queued_for_analysis,
                "errors_count": metrics.errors_count,
                "rate_limit_remaining": metrics.rate_limit_remaining,
                "error_categories": metrics.error_categories,
                "deleted_posts_detected": metrics.deleted_posts_detected,
                "deleted_comments_detected": metrics.deleted_comments_detected,
                "deletion_events_recorded": metrics.deletion_events_recorded,
            },
            error_summary=error_summary,
        )

    def _record_deletion_events(
        self,
        run_id: str | None,
        events: list[DeletionEvent],
    ) -> int:
        if self._run_repository is None or run_id is None or not events:
            return 0
        return self._run_repository.record_deletion_events(run_id=run_id, events=events)
