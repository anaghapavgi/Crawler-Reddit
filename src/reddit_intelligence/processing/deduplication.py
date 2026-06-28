"""Content hash helpers for idempotent upserts."""

from __future__ import annotations

import hashlib


def stable_sha256(text: str) -> str:
    """Return deterministic SHA-256 hash for text content."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def hash_post_content(title: str, body: str) -> str:
    """Hash cleaned post title/body as a single logical unit."""
    payload = f"{title}\n---\n{body}"
    return stable_sha256(payload)


def hash_comment_content(body: str) -> str:
    """Hash cleaned comment body."""
    return stable_sha256(body)
