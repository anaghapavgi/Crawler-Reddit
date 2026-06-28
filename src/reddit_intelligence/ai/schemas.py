"""Strict Pydantic schemas for AI analysis and summaries."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator

from reddit_intelligence.config import TaxonomyConfig

SourceType = Literal["post", "comment"]
BatchStatus = Literal["success", "partial", "failed", "budget_stopped"]
SentimentLabel = Literal["positive", "neutral", "negative", "mixed", "unknown"]


class AnalysisInput(BaseModel):
    """Input item passed to AI classification providers."""

    source_type: SourceType
    source_reddit_id: str
    text: str
    analyzed_text_hash: str


class UsageStats(BaseModel):
    """Token/cost usage accounting for a provider call or batch."""

    input_tokens: int = Field(default=0, ge=0)
    output_tokens: int = Field(default=0, ge=0)
    estimated_cost_usd: float = Field(default=0, ge=0)
    estimated_cost_inr: float = Field(default=0, ge=0)


class ClassificationResult(BaseModel):
    """Structured classification output for one content item."""

    source_type: SourceType
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
    baseline_sentiment_score: float | None = Field(default=None, ge=-1, le=1)
    input_tokens: int = Field(default=0, ge=0)
    output_tokens: int = Field(default=0, ge=0)
    estimated_cost_usd: float = Field(default=0, ge=0)

    @field_validator("evidence_snippet")
    @classmethod
    def snippet_not_overly_long(cls, value: str) -> str:
        """Keep snippets concise for evidence rendering."""
        if len(value) > 400:
            return value[:400]
        return value


class AnalysisBatchResult(BaseModel):
    """Provider batch output including usage and failures."""

    status: BatchStatus
    model_name: str
    prompt_version: str
    results: list[ClassificationResult] = Field(default_factory=list)
    failed_ids: list[str] = Field(default_factory=list)
    skipped_ids: list[str] = Field(default_factory=list)
    usage: UsageStats = Field(default_factory=UsageStats)
    error_summary: str | None = None


class SummaryRequest(BaseModel):
    """Request payload for insight summarization."""

    question: str
    product_name: str
    metrics: dict[str, float | int | str]
    evidence_records: list[ClassificationResult]


class SummaryResult(BaseModel):
    """Structured summary output for dashboard assistant."""

    headline: str
    key_change: str
    top_drivers: list[str]
    affected_segments: list[str]
    opportunity: str
    risk_or_caveat: str
    confidence: float = Field(ge=0, le=1)
    evidence_ids: list[str]


def validate_result_taxonomy(
    result: ClassificationResult, taxonomy: TaxonomyConfig
) -> ClassificationResult:
    """Coerce provider outputs to taxonomy-safe labels when needed."""
    updates: dict[str, str] = {}
    if result.theme not in taxonomy.themes:
        updates["theme"] = "other"
    if result.feature not in taxonomy.features:
        updates["feature"] = "Unknown"
    if result.user_segment not in taxonomy.behavioral_segments:
        updates["user_segment"] = "unknown"
    if result.journey_stage not in taxonomy.journey_stages:
        updates["journey_stage"] = "unknown"
    if result.primary_emotion not in taxonomy.emotions:
        updates["primary_emotion"] = "unknown"
    if result.secondary_emotion not in [*taxonomy.emotions, "none"]:
        updates["secondary_emotion"] = "none"
    if not updates:
        return result
    return result.model_copy(update=updates)
