from __future__ import annotations

from reddit_intelligence.reddit.mapper import map_comment, map_submission


def test_map_submission_cleans_deleted_payload() -> None:
    raw = {
        "id": "p1",
        "subreddit": "spotify",
        "title": "[deleted]",
        "selftext": "[removed]",
        "permalink": "/r/spotify/comments/p1/demo/",
        "created_utc": 1719532800,
    }
    mapped = map_submission(raw, matched_queries=["fixture"])
    assert mapped.title == ""
    assert mapped.body == ""
    assert mapped.is_deleted is True
    assert mapped.matched_queries == ["fixture"]


def test_map_comment_normalizes_parent_id() -> None:
    raw = {
        "id": "c1",
        "post_reddit_id": "p1",
        "parent_id": "t1_parent123",
        "subreddit": "spotify",
        "body": "Useful feedback",
        "permalink": "/r/spotify/comments/p1/c1/",
        "created_utc": 1719532800,
        "depth": 1,
    }
    mapped = map_comment(raw, post_reddit_id="p1")
    assert mapped.parent_reddit_id == "parent123"
    assert mapped.body == "Useful feedback"
