"""Database access package."""

from reddit_intelligence.db.client import get_supabase_client
from reddit_intelligence.db.repositories import ContentRepository, InMemoryContentRepository

__all__ = ["ContentRepository", "InMemoryContentRepository", "get_supabase_client"]
