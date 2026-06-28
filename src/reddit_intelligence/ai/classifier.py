"""Batch AI classification orchestration with budget enforcement."""

from __future__ import annotations

from collections.abc import Iterable

from reddit_intelligence.ai.budget import BudgetGuard
from reddit_intelligence.ai.prompts import PROMPT_VERSION
from reddit_intelligence.ai.provider import AIProvider
from reddit_intelligence.ai.schemas import (
    AnalysisBatchResult,
    AnalysisInput,
    BatchStatus,
    ClassificationResult,
    UsageStats,
    validate_result_taxonomy,
)
from reddit_intelligence.config import TaxonomyConfig


def should_reanalyze(
    *,
    prior_text_hash: str | None,
    prior_prompt_version: str | None,
    current_text_hash: str,
    current_prompt_version: str = PROMPT_VERSION,
) -> bool:
    """Only re-analyze when text or prompt version changes."""
    if not prior_text_hash or not prior_prompt_version:
        return True
    if prior_text_hash != current_text_hash:
        return True
    return prior_prompt_version != current_prompt_version


class AIClassifier:
    """Coordinates batching, provider calls, and budget controls."""

    def __init__(
        self,
        *,
        provider: AIProvider,
        taxonomy: TaxonomyConfig,
        budget_guard: BudgetGuard,
        product_name: str,
        batch_size: int = 20,
    ) -> None:
        self.provider = provider
        self.taxonomy = taxonomy
        self.budget_guard = budget_guard
        self.product_name = product_name
        self.batch_size = batch_size

    def _chunk(self, records: list[AnalysisInput]) -> Iterable[list[AnalysisInput]]:
        for start in range(0, len(records), self.batch_size):
            yield records[start : start + self.batch_size]

    def classify_records(
        self,
        *,
        records: list[AnalysisInput],
        month_to_date_spend_inr: float = 0.0,
    ) -> AnalysisBatchResult:
        if not records:
            return AnalysisBatchResult(
                status="success",
                model_name=self.provider.model_name,
                prompt_version=PROMPT_VERSION,
            )

        call_count = 0
        processed_records = 0
        failed_ids: list[str] = []
        skipped_ids: list[str] = []
        merged_results: list[ClassificationResult] = []
        usage = UsageStats()
        status: BatchStatus = "success"
        error_summary: str | None = None

        for batch in self._chunk(records):
            # Conservative pre-call estimate for budget gating.
            estimated_next_call_inr = float(len(batch)) * 0.02
            decision = self.budget_guard.evaluate(
                processed_records=processed_records,
                call_count=call_count,
                month_to_date_inr=month_to_date_spend_inr + usage.estimated_cost_inr,
                next_call_estimated_inr=estimated_next_call_inr,
            )
            if not decision.allowed:
                status = "budget_stopped"
                skipped_ids.extend(item.source_reddit_id for item in batch)
                break

            call_count += 1
            try:
                batch_result = self.provider.classify_batch(
                    product_name=self.product_name,
                    taxonomy=self.taxonomy,
                    records=batch,
                )
            except Exception as exc:  # noqa: BLE001
                status = "partial"
                failed_ids.extend(item.source_reddit_id for item in batch)
                error_summary = f"Provider call failed: {exc}"
                continue

            processed_records += len(batch)
            failed_ids.extend(batch_result.failed_ids)
            skipped_ids.extend(batch_result.skipped_ids)
            merged_results.extend(
                validate_result_taxonomy(item, self.taxonomy) for item in batch_result.results
            )
            usage.input_tokens += batch_result.usage.input_tokens
            usage.output_tokens += batch_result.usage.output_tokens
            usage.estimated_cost_usd += batch_result.usage.estimated_cost_usd
            usage.estimated_cost_inr += batch_result.usage.estimated_cost_inr
            if batch_result.status in {"partial", "failed"} and status == "success":
                status = batch_result.status

        if not merged_results and failed_ids and status != "budget_stopped":
            status = "failed"
        elif merged_results and failed_ids and status == "success":
            status = "partial"

        return AnalysisBatchResult(
            status=status,
            model_name=self.provider.model_name,
            prompt_version=PROMPT_VERSION,
            results=merged_results,
            failed_ids=failed_ids,
            skipped_ids=skipped_ids,
            usage=usage,
            error_summary=error_summary,
        )
