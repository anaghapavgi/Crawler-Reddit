"""Shared in-process runtime state for demo-mode repositories."""

from __future__ import annotations

from reddit_intelligence.db.repositories import InMemoryContentRepository, InMemoryRunRepository

DEMO_CONTENT_REPOSITORY = InMemoryContentRepository()
DEMO_RUN_REPOSITORY = InMemoryRunRepository()


def get_demo_repositories() -> tuple[InMemoryContentRepository, InMemoryRunRepository]:
    """Return process-local in-memory repositories for demo-mode commands."""
    return DEMO_CONTENT_REPOSITORY, DEMO_RUN_REPOSITORY
