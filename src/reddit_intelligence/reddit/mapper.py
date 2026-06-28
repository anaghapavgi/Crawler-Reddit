"""Map Reddit API payloads into internal models."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import cast

from reddit_intelligence.models import RedditComment, RedditPost
from reddit_intelligence.processing.cleaning import clean_reddit_text
from reddit_intelligence.processing.deduplication import hash_comment_content, hash_post_content

REDDIT_BASE_URL = "https://reddit.com"


def _read_value(source: object, key: str, default: object | None = None) -> object | None:
    if isinstance(source, dict):
        return source.get(key, default)
    return getattr(source, key, default)


def _normalize_permalink(raw_permalink: object | None) -> str:
    permalink = str(raw_permalink or "").strip()
    if permalink.startswith("http://") or permalink.startswith("https://"):
        return permalink
    if not permalink.startswith("/"):
        permalink = f"/{permalink}"
    return f"{REDDIT_BASE_URL}{permalink}"


def _to_datetime_utc(raw_timestamp: object | None) -> datetime:
    if isinstance(raw_timestamp, (int, float)):
        return datetime.fromtimestamp(raw_timestamp, tz=UTC)
    return datetime.now(tz=UTC)


def _normalize_parent_id(raw_parent_id: object | None) -> str | None:
    if raw_parent_id is None:
        return None
    parent_id = str(raw_parent_id)
    if "_" in parent_id:
        return parent_id.split("_", maxsplit=1)[1]
    return parent_id


def map_submission(
    source: object,
    matched_queries: list[str] | None = None,
) -> RedditPost:
    """Map Reddit submission payload/object to normalized post model."""
    title = clean_reddit_text(cast(str | None, _read_value(source, "title", "")))
    body = clean_reddit_text(
        cast(
            str | None,
            _read_value(source, "selftext", _read_value(source, "body", "")),
        )
    )
    content_hash = hash_post_content(title, body)

    return RedditPost(
        reddit_id=str(_read_value(source, "id", "")),
        subreddit=str(
            _read_value(
                source,
                "subreddit",
                _read_value(source, "subreddit_name_prefixed", "unknown"),
            )
        ).replace("r/", ""),
        title=title,
        body=body,
        permalink=_normalize_permalink(_read_value(source, "permalink")),
        score=int(cast(int | float | str, _read_value(source, "score", 0))),
        upvote_ratio=cast(float | None, _read_value(source, "upvote_ratio")),
        num_comments=int(cast(int | float | str, _read_value(source, "num_comments", 0))),
        created_utc=_to_datetime_utc(_read_value(source, "created_utc")),
        content_hash=content_hash,
        matched_queries=matched_queries or [],
        relevance_score=0,
        is_deleted=title == "" and body == "",
        raw_metadata={"collected_from": "reddit_api_or_fixture"},
    )


def map_comment(source: object, post_reddit_id: str) -> RedditComment:
    """Map Reddit comment payload/object to normalized comment model."""
    body = clean_reddit_text(cast(str | None, _read_value(source, "body", "")))
    content_hash = hash_comment_content(body)
    return RedditComment(
        reddit_id=str(_read_value(source, "id", "")),
        post_reddit_id=post_reddit_id,
        parent_reddit_id=_normalize_parent_id(_read_value(source, "parent_id")),
        subreddit=str(
            _read_value(
                source,
                "subreddit",
                _read_value(source, "subreddit_name_prefixed", "unknown"),
            )
        ).replace("r/", ""),
        body=body,
        permalink=_normalize_permalink(_read_value(source, "permalink")),
        score=int(cast(int | float | str, _read_value(source, "score", 0))),
        depth=int(cast(int | float | str, _read_value(source, "depth", 0))),
        created_utc=_to_datetime_utc(_read_value(source, "created_utc")),
        content_hash=content_hash,
        relevance_score=0,
        is_deleted=body == "",
        raw_metadata={"collected_from": "reddit_api_or_fixture"},
    )
