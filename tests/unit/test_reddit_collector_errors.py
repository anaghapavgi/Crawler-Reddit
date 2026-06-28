from __future__ import annotations

from reddit_intelligence.reddit.collector import classify_reddit_exception


def test_classify_timeout_and_connection_errors() -> None:
    assert classify_reddit_exception(TimeoutError("timed out")) == "timeout"
    assert classify_reddit_exception(ConnectionError("network down")) == "network_error"


def test_classify_database_and_rate_limit_messages() -> None:
    assert classify_reddit_exception(RuntimeError("database write failed")) == "database_error"
    assert (
        classify_reddit_exception(RuntimeError("hit rate limit from reddit"))
        == "rate_limit_or_response_error"
    )


def test_classify_permission_and_unknown_errors() -> None:
    assert classify_reddit_exception(PermissionError("forbidden")) == "forbidden_private_subreddit"
    assert classify_reddit_exception(RuntimeError("unexpected")) == "unknown_error"
