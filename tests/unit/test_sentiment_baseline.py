from __future__ import annotations

from reddit_intelligence.processing.sentiment_baseline import vader_compound_score, vader_label


def test_vader_label_positive() -> None:
    assert vader_label("I love this feature, it works wonderfully.") == "positive"


def test_vader_label_negative() -> None:
    assert vader_label("This is frustrating and disappointing.") == "negative"


def test_vader_score_empty_text_defaults_to_zero() -> None:
    assert vader_compound_score("   ") == 0.0
