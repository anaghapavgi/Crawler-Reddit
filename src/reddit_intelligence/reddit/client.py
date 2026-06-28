"""Read-only PRAW client adapter."""

from __future__ import annotations

from typing import Any

import praw

from reddit_intelligence.config import Settings


def create_reddit_client(settings: Settings) -> praw.Reddit | None:
    """Create authenticated read-only Reddit client when credentials are present."""
    has_credentials = all(
        [
            settings.reddit_client_id,
            settings.reddit_client_secret,
            settings.reddit_user_agent,
        ]
    )
    if not has_credentials:
        if settings.demo_mode:
            return None
        msg = "Reddit credentials are required when DEMO_MODE=false."
        raise RuntimeError(msg)

    reddit = praw.Reddit(
        client_id=settings.reddit_client_id,
        client_secret=settings.reddit_client_secret,
        user_agent=settings.reddit_user_agent,
    )
    reddit.read_only = True
    if not reddit.read_only:
        msg = "PRAW client must run in read-only mode."
        raise RuntimeError(msg)
    return reddit


def get_rate_limit_remaining(reddit: Any) -> float | None:
    """Read rate-limit remaining budget from PRAW auth limits when available."""
    auth = getattr(reddit, "auth", None)
    if auth is None:
        return None
    limits = getattr(auth, "limits", None)
    if not isinstance(limits, dict):
        return None
    remaining = limits.get("remaining")
    if remaining is None:
        return None
    try:
        return float(remaining)
    except (TypeError, ValueError):
        return None
