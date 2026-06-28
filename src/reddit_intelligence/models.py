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
SentimentLabel = Literal["positive", "neutral", "negative", "mixed", "unknown"]


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
