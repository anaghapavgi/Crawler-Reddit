from __future__ import annotations

from reddit_intelligence.processing.cleaning import clean_reddit_text, is_deleted_or_removed


def test_deleted_markers_are_detected() -> None:
    assert is_deleted_or_removed("[deleted]") is True
    assert is_deleted_or_removed("[removed]") is True
    assert is_deleted_or_removed("actual content") is False


def test_clean_reddit_text_normalizes_whitespace_and_control_chars() -> None:
    raw = "Hello\x00   world\t\t\n\n\nline\x07 two"
    cleaned = clean_reddit_text(raw)
    assert cleaned == "Hello world\n\nline two"


def test_clean_reddit_text_returns_empty_for_deleted_content() -> None:
    assert clean_reddit_text("[deleted]") == ""
