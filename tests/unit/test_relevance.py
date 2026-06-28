from __future__ import annotations

from reddit_intelligence.config import RelevanceResearch
from reddit_intelligence.processing.relevance import RelevanceScorer


def test_relevance_scorer_rewards_problem_language_and_includes() -> None:
    config = RelevanceResearch(
        minimum_text_length=10,
        minimum_rule_score=1,
        include_terms=["discover weekly", "recommendation", "playlist"],
        exclude_terms=["giveaway"],
    )
    scorer = RelevanceScorer(config=config, feature_terms=["Discover Weekly"])
    result = scorer.score(
        "Discover Weekly recommendation quality is bad and repetitive for my playlist."
    )
    assert result.score >= 4
    assert result.is_relevant is True
    assert "discover weekly" in result.matched_include_terms


def test_relevance_scorer_penalizes_excludes_and_short_text() -> None:
    config = RelevanceResearch(
        minimum_text_length=20,
        minimum_rule_score=1,
        include_terms=["recommendation"],
        exclude_terms=["giveaway"],
    )
    scorer = RelevanceScorer(config=config)
    result = scorer.score("giveaway")
    assert result.score <= -5
    assert result.is_relevant is False
