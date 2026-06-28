"""Provider interfaces and deterministic demo provider."""

from __future__ import annotations

from typing import Protocol

from reddit_intelligence.ai.budget import estimate_cost_inr
from reddit_intelligence.ai.prompts import PROMPT_VERSION
from reddit_intelligence.ai.schemas import (
    AnalysisBatchResult,
    AnalysisInput,
    ClassificationResult,
    SummaryRequest,
    SummaryResult,
    UsageStats,
)
from reddit_intelligence.config import TaxonomyConfig
from reddit_intelligence.processing.sentiment_baseline import vader_compound_score, vader_label


class AIProvider(Protocol):
    """Interface for AI providers used by classifier/summarizer stages."""

    model_name: str

    def classify_batch(
        self,
        *,
        product_name: str,
        taxonomy: TaxonomyConfig,
        records: list[AnalysisInput],
    ) -> AnalysisBatchResult:
        """Classify a list of content records into structured labels."""

    def summarize(self, *, request: SummaryRequest) -> SummaryResult:
        """Generate structured summary from metrics and evidence."""


class DeterministicDemoProvider:
    """Cost-aware deterministic provider for demo mode and tests."""

    def __init__(self, model_name: str = "demo-deterministic-v1") -> None:
        self.model_name = model_name

    def _pick_theme(self, text: str, taxonomy: TaxonomyConfig) -> str:
        lowered = text.lower()
        for candidate in taxonomy.themes:
            if candidate == "other":
                continue
            normalized = candidate.replace("_", " ")
            tokens = [token for token in normalized.split(" ") if token]
            if any(token in lowered for token in tokens):
                return candidate
        return "other" if "other" in taxonomy.themes else taxonomy.themes[0]

    def _pick_feature(self, text: str, taxonomy: TaxonomyConfig) -> str:
        lowered = text.lower()
        for feature in taxonomy.features:
            if feature.lower() in lowered:
                return feature
        return "Unknown" if "Unknown" in taxonomy.features else taxonomy.features[0]

    def classify_batch(
        self,
        *,
        product_name: str,
        taxonomy: TaxonomyConfig,
        records: list[AnalysisInput],
    ) -> AnalysisBatchResult:
        results: list[ClassificationResult] = []
        total_input_tokens = 0
        total_output_tokens = 0
        for record in records:
            baseline_score = vader_compound_score(record.text)
            coarse_label = vader_label(record.text)
            sentiment_label = "mixed" if "but" in record.text.lower() else coarse_label
            input_tokens = max(1, len(record.text) // 4)
            output_tokens = 120
            total_input_tokens += input_tokens
            total_output_tokens += output_tokens
            results.append(
                ClassificationResult(
                    source_type=record.source_type,
                    source_reddit_id=record.source_reddit_id,
                    analyzed_text_hash=record.analyzed_text_hash,
                    prompt_version=PROMPT_VERSION,
                    model_name=self.model_name,
                    relevant=True,
                    language="en",
                    sentiment_label=sentiment_label,
                    sentiment_score=baseline_score,
                    primary_emotion="frustration" if baseline_score < -0.05 else "satisfaction",
                    secondary_emotion="none",
                    intensity=4 if abs(baseline_score) > 0.5 else 2,
                    sarcasm_detected="/s" in record.text.lower()
                    or "yeah right" in record.text.lower(),
                    theme=self._pick_theme(record.text, taxonomy),
                    subtheme="general",
                    feature=self._pick_feature(record.text, taxonomy),
                    journey_stage=(
                        "unknown"
                        if "unknown" in taxonomy.journey_stages
                        else taxonomy.journey_stages[0]
                    ),
                    user_segment=(
                        "unknown"
                        if "unknown" in taxonomy.behavioral_segments
                        else taxonomy.behavioral_segments[0]
                    ),
                    pain_point="Slow response or confusing UX."
                    if baseline_score < -0.05
                    else "No major pain point stated.",
                    desired_outcome="Faster and clearer experience.",
                    severity=4 if baseline_score < -0.05 else 2,
                    confidence=0.72,
                    one_line_summary=f"{product_name} feedback classified from Reddit.",
                    evidence_snippet=record.text[:240],
                    baseline_sentiment_score=baseline_score,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    estimated_cost_usd=0.0,
                )
            )
        total_usd, total_inr = estimate_cost_inr(
            input_tokens=total_input_tokens,
            output_tokens=total_output_tokens,
            input_cost_per_1k_usd=0.0,
            output_cost_per_1k_usd=0.0,
        )
        usage = UsageStats(
            input_tokens=total_input_tokens,
            output_tokens=total_output_tokens,
            estimated_cost_usd=total_usd,
            estimated_cost_inr=total_inr,
        )
        return AnalysisBatchResult(
            status="success",
            model_name=self.model_name,
            prompt_version=PROMPT_VERSION,
            results=results,
            usage=usage,
        )

    def summarize(self, *, request: SummaryRequest) -> SummaryResult:
        evidence_ids = [record.source_reddit_id for record in request.evidence_records[:5]]
        return SummaryResult(
            headline=f"{request.product_name}: stable trend in sampled Reddit discussions",
            key_change="No significant week-over-week shift detected in demo mode.",
            top_drivers=["Pricing perception", "Reliability comments", "Support quality"],
            affected_segments=["power_users"],
            opportunity="Prioritize fixes for repeated pain points in reliability mentions.",
            risk_or_caveat="Demo summary generated from synthetic or sampled inputs.",
            confidence=0.55,
            evidence_ids=evidence_ids,
        )
