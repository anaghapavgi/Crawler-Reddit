"""Core domain models."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


@dataclass(slots=True)
class RunSummary:
    """Simple run summary used by scaffold commands."""

    started_at: datetime
    status: str
    message: str


AnalysisStatus = Literal["pending", "processing", "complete", "failed", "skipped", "stale"]
ContentType = Literal["post", "comment"]
FailureSourceType = Literal["post", "comment", "run"]
SentimentLabel = Literal["positive", "neutral", "negative", "mixed", "unknown"]
CrawlRunStatus = Literal["running", "success", "partial", "failed", "budget_stopped"]
AnalysisRunStatus = Literal["running", "success", "partial", "failed", "budget_stopped"]


@dataclass(slots=True)
class DeletionEvent:
    """Deletion event metadata for compliance tracking."""

    source_type: ContentType
    source_reddit_id: str
    detected_at: datetime
    action_taken: str
    originating_job_id: str | None = None


@dataclass(slots=True)
class CrawlRunRecord:
    """Operational crawl run record persisted by run repositories."""

    run_id: str
    started_at: datetime
    trigger_source: str
    status: CrawlRunStatus
    finished_at: datetime | None = None
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
    error_summary: str | None = None
    metadata: dict[str, object] | None = None


@dataclass(slots=True)
class AnalysisRunRecord:
    """Operational analysis run metadata tracked per analyze invocation."""

    run_id: str
    started_at: datetime
    status: AnalysisRunStatus
    model_name: str
    prompt_version: str
    finished_at: datetime | None = None
    records_attempted: int = 0
    records_succeeded: int = 0
    records_failed: int = 0
    records_skipped: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    estimated_cost_usd: float = 0
    estimated_cost_inr: float = 0
    metadata: dict[str, object] | None = None
    error_summary: str | None = None


@dataclass(slots=True)
class PipelineFailureRecord:
    """Retry-queue entry for failed crawl/analysis pipeline work."""

    failure_id: str
    source_type: FailureSourceType
    source_reddit_id: str
    stage: str
    error_category: str
    attempt_count: int
    last_error: str
    created_at: datetime
    updated_at: datetime
    next_retry_at: datetime | None = None
    metadata: dict[str, object] | None = None


class RedditPost(BaseModel):
    """Normalized Reddit post record."""

    reddit_id: str
    subreddit: str
    title: str = ""
    body: str = ""
    permalink: str
    score: int = 0
    upvote_ratio: float | None = None
    num_comments: int = 0
    created_utc: datetime
    content_hash: str
    matched_queries: list[str] = Field(default_factory=list)
    relevance_score: float = 0
    is_deleted: bool = False
    deleted_at: datetime | None = None
    analysis_status: AnalysisStatus = "pending"
    raw_metadata: dict[str, object] = Field(default_factory=dict)


class RedditComment(BaseModel):
    """Normalized Reddit comment record."""

    reddit_id: str
    post_reddit_id: str
    parent_reddit_id: str | None = None
    subreddit: str
    body: str = ""
    permalink: str
    score: int = 0
    depth: int = 0
    created_utc: datetime
    content_hash: str
    relevance_score: float = 0
    is_deleted: bool = False
    deleted_at: datetime | None = None
    analysis_status: AnalysisStatus = "pending"
    raw_metadata: dict[str, object] = Field(default_factory=dict)


class AnalysisRecord(BaseModel):
    """Structured analysis record persisted in content_analysis."""

    source_type: ContentType
    source_reddit_id: str
    analyzed_text_hash: str
    prompt_version: str
    model_name: str
    relevant: bool
    language: str = "unknown"
    sentiment_label: SentimentLabel
    sentiment_score: float = Field(ge=-1, le=1)
    primary_emotion: str = "unknown"
    secondary_emotion: str = "none"
    intensity: int = Field(ge=1, le=5)
    sarcasm_detected: bool = False
    theme: str = "other"
    subtheme: str = "other"
    feature: str = "Unknown"
    journey_stage: str = "unknown"
    user_segment: str = "unknown"
    pain_point: str = ""
    desired_outcome: str = ""
    severity: int = Field(ge=1, le=5)
    confidence: float = Field(ge=0, le=1)
    one_line_summary: str = ""
    evidence_snippet: str = ""
    baseline_sentiment_score: float | None = None
    input_tokens: int = 0
    output_tokens: int = 0
    estimated_cost_usd: float = 0
