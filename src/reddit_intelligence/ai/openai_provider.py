"""OpenAI provider adapter skeleton for structured analysis calls."""

from __future__ import annotations

from openai import OpenAI

from reddit_intelligence.ai.provider import AIProvider
from reddit_intelligence.ai.schemas import (
    AnalysisBatchResult,
    AnalysisInput,
    SummaryRequest,
    SummaryResult,
)
from reddit_intelligence.config import TaxonomyConfig


class OpenAIProvider(AIProvider):
    """Live provider adapter reserved for credentialed environments."""

    def __init__(
        self,
        *,
        api_key: str,
        model_name: str,
        timeout_seconds: int = 30,
        client: OpenAI | None = None,
    ) -> None:
        self.model_name = model_name
        self._client = client or OpenAI(api_key=api_key, timeout=timeout_seconds)

    def classify_batch(
        self,
        *,
        product_name: str,
        taxonomy: TaxonomyConfig,
        records: list[AnalysisInput],
    ) -> AnalysisBatchResult:
        """Raise explicit error until live structured output integration is wired."""
        raise RuntimeError(
            "OpenAI live classification is not enabled in demo mode. "
            "Use DeterministicDemoProvider or inject a mocked provider in tests."
        )

    def summarize(self, *, request: SummaryRequest) -> SummaryResult:
        raise RuntimeError(
            "OpenAI live summarization is not enabled in demo mode. "
            "Use DeterministicDemoProvider or inject a mocked provider in tests."
        )
