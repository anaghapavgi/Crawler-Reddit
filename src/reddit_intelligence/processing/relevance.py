"""Transparent rules-based relevance scoring."""

from __future__ import annotations

from dataclasses import dataclass, field

from reddit_intelligence.config import RelevanceResearch

PROBLEM_TERMS = (
    "issue",
    "problem",
    "broken",
    "frustrat",
    "annoy",
    "worse",
    "bad",
    "stale",
    "repetitive",
    "same songs",
)
PROMOTION_TERMS = (
    "follow my playlist",
    "playlist promotion",
    "promo code",
    "giveaway",
    "subscribe to my channel",
)


@dataclass(slots=True)
class RelevanceResult:
    """Detailed relevance score output."""

    score: int
    is_relevant: bool
    matched_include_terms: list[str] = field(default_factory=list)
    matched_exclude_terms: list[str] = field(default_factory=list)
    reasons: list[str] = field(default_factory=list)


class RelevanceScorer:
    """Config-driven relevance scoring for posts/comments."""

    def __init__(self, config: RelevanceResearch, feature_terms: list[str] | None = None) -> None:
        self._config = config
        self._feature_terms = [term.lower() for term in (feature_terms or []) if term]

    def score(self, text: str) -> RelevanceResult:
        """Apply scoring formula and return explainable result."""
        text_lower = text.lower()
        score = 0
        reasons: list[str] = []

        exact_phrase_hits = [
            term
            for term in self._config.include_terms
            if " " in term and term.lower() in text_lower
        ]
        if exact_phrase_hits:
            score += 2
            reasons.append("exact_phrase_match:+2")

        include_hits = sorted(
            {term for term in self._config.include_terms if term.lower() in text_lower}
        )
        include_bonus = min(len(include_hits), 5)
        if include_bonus:
            score += include_bonus
            reasons.append(f"include_terms:+{include_bonus}")

        if self._feature_terms and any(term in text_lower for term in self._feature_terms):
            score += 1
            reasons.append("feature_match:+1")

        if any(term in text_lower for term in PROBLEM_TERMS):
            score += 1
            reasons.append("problem_language:+1")

        exclude_hits = [term for term in self._config.exclude_terms if term.lower() in text_lower]
        if exclude_hits:
            score -= 3
            reasons.append("exclude_phrase:-3")

        if len(text.strip()) < self._config.minimum_text_length:
            score -= 2
            reasons.append("below_min_length:-2")

        if any(term in text_lower for term in PROMOTION_TERMS):
            score -= 2
            reasons.append("promotion_detected:-2")

        is_relevant = score >= self._config.minimum_rule_score
        return RelevanceResult(
            score=score,
            is_relevant=is_relevant,
            matched_include_terms=include_hits,
            matched_exclude_terms=exclude_hits,
            reasons=reasons,
        )
