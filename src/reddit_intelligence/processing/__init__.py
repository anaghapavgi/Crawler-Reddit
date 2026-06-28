"""Text processing package."""

from reddit_intelligence.processing.cleaning import clean_reddit_text, is_deleted_or_removed
from reddit_intelligence.processing.deduplication import (
    hash_comment_content,
    hash_post_content,
    stable_sha256,
)
from reddit_intelligence.processing.relevance import RelevanceResult, RelevanceScorer
from reddit_intelligence.processing.sentiment_baseline import vader_compound_score, vader_label

__all__ = [
    "RelevanceResult",
    "RelevanceScorer",
    "clean_reddit_text",
    "hash_comment_content",
    "hash_post_content",
    "is_deleted_or_removed",
    "stable_sha256",
    "vader_compound_score",
    "vader_label",
]
