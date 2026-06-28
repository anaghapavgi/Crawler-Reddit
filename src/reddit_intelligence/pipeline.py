"""Pipeline orchestration entry points."""

from __future__ import annotations

from datetime import UTC, datetime

from reddit_intelligence.models import RunSummary


def run_demo_pipeline() -> RunSummary:
    """Return a placeholder run summary for Phase 0."""
    return RunSummary(
        started_at=datetime.now(tz=UTC),
        status="success",
        message="Demo pipeline scaffold executed.",
    )
