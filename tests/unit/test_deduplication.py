from __future__ import annotations

from reddit_intelligence.processing.deduplication import (
    hash_comment_content,
    hash_post_content,
    stable_sha256,
)


def test_stable_sha256_is_deterministic() -> None:
    assert stable_sha256("abc") == stable_sha256("abc")
    assert stable_sha256("abc") != stable_sha256("abcd")


def test_post_and_comment_hash_helpers() -> None:
    post_hash = hash_post_content("title", "body")
    same_post_hash = hash_post_content("title", "body")
    comment_hash = hash_comment_content("body")

    assert post_hash == same_post_hash
    assert post_hash != comment_hash
