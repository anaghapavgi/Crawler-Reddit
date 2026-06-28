"""Deterministic cleaning helpers for Reddit text."""

from __future__ import annotations

import re

UNSAFE_CONTROL_CHARS = re.compile(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]")
MULTISPACE = re.compile(r"[ \t]+")
MULTINEWLINE = re.compile(r"\n{3,}")
DELETED_MARKERS = {"[deleted]", "[removed]", "deleted", "removed", "unavailable", ""}


def is_deleted_or_removed(text: str | None) -> bool:
    """Return true when Reddit content represents deleted or removed text."""
    if text is None:
        return True
    normalized = text.strip().lower()
    return normalized in DELETED_MARKERS


def clean_reddit_text(text: str | None, max_length: int | None = None) -> str:
    """Normalize Reddit text while preserving punctuation semantics for sentiment."""
    if text is None:
        return ""
    if is_deleted_or_removed(text):
        return ""

    cleaned = text.replace("\r\n", "\n").replace("\r", "\n")
    cleaned = UNSAFE_CONTROL_CHARS.sub("", cleaned)
    cleaned = "\n".join(MULTISPACE.sub(" ", line).strip() for line in cleaned.split("\n"))
    cleaned = MULTINEWLINE.sub("\n\n", cleaned).strip()
    if max_length is not None and max_length > 0:
        return cleaned[:max_length]
    return cleaned
