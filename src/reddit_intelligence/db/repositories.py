"""Repository interfaces and demo in-memory implementations."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Protocol

from reddit_intelligence.models import RedditComment, RedditPost


class ContentRepository(Protocol):
    """Persistence interface for normalized Reddit content."""

    def upsert_posts(self, posts: Iterable[RedditPost]) -> int:
        """Insert or update posts idempotently."""

    def upsert_comments(self, comments: Iterable[RedditComment]) -> int:
        """Insert or update comments idempotently."""

    def get_post(self, reddit_id: str) -> RedditPost | None:
        """Fetch a post by Reddit ID."""

    def get_comment(self, reddit_id: str) -> RedditComment | None:
        """Fetch a comment by Reddit ID."""


class InMemoryContentRepository:
    """Credential-free repository for demo mode and unit tests."""

    def __init__(self) -> None:
        self._posts: dict[str, RedditPost] = {}
        self._comments: dict[str, RedditComment] = {}

    def upsert_posts(self, posts: Iterable[RedditPost]) -> int:
        upserted = 0
        for post in posts:
            existing = self._posts.get(post.reddit_id)
            if existing is not None:
                merged_queries = sorted(set(existing.matched_queries) | set(post.matched_queries))
                post = post.model_copy(update={"matched_queries": merged_queries})
            self._posts[post.reddit_id] = post
            upserted += 1
        return upserted

    def upsert_comments(self, comments: Iterable[RedditComment]) -> int:
        upserted = 0
        for comment in comments:
            self._comments[comment.reddit_id] = comment
            upserted += 1
        return upserted

    def get_post(self, reddit_id: str) -> RedditPost | None:
        return self._posts.get(reddit_id)

    def get_comment(self, reddit_id: str) -> RedditComment | None:
        return self._comments.get(reddit_id)
