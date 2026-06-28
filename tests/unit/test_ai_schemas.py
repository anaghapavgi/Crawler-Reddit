from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from reddit_intelligence.ai.schemas import (
    AnalysisBatchResult,
    ClassificationResult,
    validate_result_taxonomy,
)
from reddit_intelligence.config import load_taxonomy_config


def test_analysis_batch_schema_rejects_malformed_fixture() -> None:
    malformed = json.loads(
        Path("tests/fixtures/ai_malformed_response.json").read_text(encoding="utf-8")
    )
    with pytest.raises(ValidationError):
        AnalysisBatchResult.model_validate(malformed)


def test_validate_result_taxonomy_coerces_invalid_labels() -> None:
    taxonomy = load_taxonomy_config()
    result = ClassificationResult(
        source_type="post",
        source_reddit_id="abc",
        analyzed_text_hash="hash",
        prompt_version="v1",
        model_name="demo",
        relevant=True,
        language="en",
        sentiment_label="neutral",
        sentiment_score=0.0,
        primary_emotion="unknown-emotion",
        secondary_emotion="another-unknown",
        intensity=2,
        sarcasm_detected=False,
        theme="does-not-exist",
        subtheme="general",
        feature="NotAFeature",
        journey_stage="NotAStage",
        user_segment="NotASegment",
        pain_point="",
        desired_outcome="",
        severity=2,
        confidence=0.5,
        one_line_summary="summary",
        evidence_snippet="snippet",
    )
    coerced = validate_result_taxonomy(result, taxonomy)
    assert coerced.theme == "other"
    assert coerced.feature == "Unknown"
    assert coerced.journey_stage == "unknown"
    assert coerced.user_segment == "unknown"
    assert coerced.primary_emotion == "unknown"
    assert coerced.secondary_emotion == "none"
