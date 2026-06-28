"""Database access package."""

from reddit_intelligence.db.client import get_supabase_client
from reddit_intelligence.db.repositories import (
    ContentRepository,
    CrawlRunRepository,
    InMemoryContentRepository,
    InMemoryRunRepository,
)

__all__ = [
    "ContentRepository",
    "CrawlRunRepository",
    "InMemoryContentRepository",
    "InMemoryRunRepository",
    "get_supabase_client",
]
