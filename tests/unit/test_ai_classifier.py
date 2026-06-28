from __future__ import annotations

from reddit_intelligence.ai.budget import BudgetGuard
from reddit_intelligence.ai.classifier import AIClassifier, should_reanalyze
from reddit_intelligence.ai.schemas import (
    AnalysisBatchResult,
    AnalysisInput,
    ClassificationResult,
    UsageStats,
)
from reddit_intelligence.config import load_taxonomy_config
from reddit_intelligence.processing.deduplication import stable_sha256


class _InvalidThemeProvider:
    model_name = "invalid-theme-provider"

    def classify_batch(  # noqa: PLR0913
        self,
        *,
        product_name: str,
        taxonomy,
        records: list[AnalysisInput],
    ) -> AnalysisBatchResult:
        _ = product_name, taxonomy
        results = [
            ClassificationResult(
                source_type=item.source_type,
                source_reddit_id=item.source_reddit_id,
                analyzed_text_hash=item.analyzed_text_hash,
                prompt_version="v1",
                model_name=self.model_name,
                relevant=True,
                language="en",
                sentiment_label="neutral",
                sentiment_score=0.0,
                primary_emotion="bad-emotion",
                secondary_emotion="worse-emotion",
                intensity=2,
                sarcasm_detected=False,
                theme="bad-theme",
                subtheme="general",
                feature="bad-feature",
                journey_stage="bad-stage",
                user_segment="bad-segment",
                pain_point="",
                desired_outcome="",
                severity=2,
                confidence=0.5,
                one_line_summary="summary",
                evidence_snippet=item.text,
            )
            for item in records
        ]
        return AnalysisBatchResult(
            status="success",
            model_name=self.model_name,
            prompt_version="v1",
            results=results,
            usage=UsageStats(),
        )


def _records(count: int) -> list[AnalysisInput]:
    values: list[AnalysisInput] = []
    for idx in range(count):
        text = f"Record {idx} text"
        values.append(
            AnalysisInput(
                source_type="comment",
                source_reddit_id=f"id-{idx}",
                text=text,
                analyzed_text_hash=stable_sha256(text),
            )
        )
    return values


def test_should_reanalyze_depends_on_hash_and_prompt() -> None:
    assert (
        should_reanalyze(
            prior_text_hash="a",
            prior_prompt_version="v1",
            current_text_hash="a",
            current_prompt_version="v1",
        )
        is False
    )
    assert (
        should_reanalyze(
            prior_text_hash="a",
            prior_prompt_version="v1",
            current_text_hash="b",
            current_prompt_version="v1",
        )
        is True
    )
    assert (
        should_reanalyze(
            prior_text_hash="a",
            prior_prompt_version="v1",
            current_text_hash="a",
            current_prompt_version="v2",
        )
        is True
    )


def test_classifier_stops_when_per_run_record_budget_hit() -> None:
    taxonomy = load_taxonomy_config()
    classifier = AIClassifier(
        provider=_InvalidThemeProvider(),
        taxonomy=taxonomy,
        budget_guard=BudgetGuard(
            monthly_budget_inr=100,
            max_records_per_run=2,
            max_calls_per_run=10,
        ),
        product_name="Spotify",
        batch_size=2,
    )
    result = classifier.classify_records(records=_records(3))
    assert result.status == "budget_stopped"
    assert len(result.results) == 2
    assert result.skipped_ids == ["id-2"]


def test_classifier_coerces_outputs_to_taxonomy_safe_values() -> None:
    taxonomy = load_taxonomy_config()
    classifier = AIClassifier(
        provider=_InvalidThemeProvider(),
        taxonomy=taxonomy,
        budget_guard=BudgetGuard(
            monthly_budget_inr=100,
            max_records_per_run=10,
            max_calls_per_run=10,
        ),
        product_name="Spotify",
        batch_size=5,
    )
    result = classifier.classify_records(records=_records(1))
    assert result.status == "success"
    assert result.results[0].theme == "other"
    assert result.results[0].feature == "Unknown"
    assert result.results[0].journey_stage == "unknown"
    assert result.results[0].user_segment == "unknown"
    assert result.results[0].primary_emotion == "unknown"
