from __future__ import annotations

from datetime import UTC, datetime

from reddit_intelligence.db.repositories import InMemoryContentRepository
from reddit_intelligence.models import RedditComment, RedditPost


def test_upsert_posts_is_idempotent_and_merges_matched_queries() -> None:
    repo = InMemoryContentRepository()
    created = datetime(2026, 1, 1, tzinfo=UTC)
    first = RedditPost(
        reddit_id="p1",
        subreddit="spotify",
        permalink="https://reddit.com/r/spotify/p1",
        created_utc=created,
        content_hash="h1",
        matched_queries=["discover weekly"],
    )
    second = RedditPost(
        reddit_id="p1",
        subreddit="spotify",
        permalink="https://reddit.com/r/spotify/p1",
        created_utc=created,
        content_hash="h1",
        matched_queries=["same songs"],
    )
    assert repo.upsert_posts([first]) == 1
    assert repo.upsert_posts([second]) == 1
    stored = repo.get_post("p1")
    assert stored is not None
    assert stored.matched_queries == ["discover weekly", "same songs"]


def test_upsert_comments_overwrites_by_reddit_id() -> None:
    repo = InMemoryContentRepository()
    created = datetime(2026, 1, 1, tzinfo=UTC)
    comment = RedditComment(
        reddit_id="c1",
        post_reddit_id="p1",
        subreddit="spotify",
        permalink="https://reddit.com/r/spotify/comments/c1",
        created_utc=created,
        content_hash="h1",
        body="first",
    )
    updated = comment.model_copy(update={"body": "updated"})

    repo.upsert_comments([comment])
    repo.upsert_comments([updated])
    stored = repo.get_comment("c1")
    assert stored is not None
    assert stored.body == "updated"


def test_iter_helpers_and_count_helpers() -> None:
    repo = InMemoryContentRepository()
    created = datetime(2026, 1, 1, tzinfo=UTC)
    post = RedditPost(
        reddit_id="p_iter",
        subreddit="spotify",
        permalink="https://reddit.com/r/spotify/p_iter",
        created_utc=created,
        content_hash="h_iter",
    )
    comment = RedditComment(
        reddit_id="c_iter",
        post_reddit_id="p_iter",
        subreddit="spotify",
        permalink="https://reddit.com/r/spotify/comments/c_iter",
        created_utc=created,
        content_hash="hc_iter",
    )
    repo.upsert_posts([post])
    repo.upsert_comments([comment])
    assert repo.post_count() == 1
    assert repo.comment_count() == 1
    assert len(list(repo.iter_posts())) == 1
    assert len(list(repo.iter_comments())) == 1
