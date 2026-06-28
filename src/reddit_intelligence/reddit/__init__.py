"""Reddit API integration package."""

from reddit_intelligence.reddit.client import create_reddit_client, get_rate_limit_remaining
from reddit_intelligence.reddit.collector import (
    CrawlRunMetrics,
    RedditCollector,
    classify_reddit_exception,
)
from reddit_intelligence.reddit.deletion_sync import DeletionSyncResult, sync_deleted_content
from reddit_intelligence.reddit.mapper import map_comment, map_submission

__all__ = [
    "CrawlRunMetrics",
    "RedditCollector",
    "classify_reddit_exception",
    "create_reddit_client",
    "DeletionSyncResult",
    "get_rate_limit_remaining",
    "map_comment",
    "map_submission",
    "sync_deleted_content",
]
