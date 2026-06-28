"""Pipeline-health analytics helpers aligned to v_pipeline_health semantics."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from reddit_intelligence.db.repositories import InMemoryContentRepository, InMemoryRunRepository


@dataclass(frozen=True)
class PipelineHealthSnapshot:
    """Operational health summary for crawl/analyze pipeline visibility."""

    computed_at: datetime
    latest_crawl_run_id: str | None
    latest_crawl_status: str | None
    latest_crawl_finished_at: datetime | None
    data_freshness_seconds: float | None
    latest_analysis_run_id: str | None
    latest_analysis_status: str | None
    latest_analysis_finished_at: datetime | None
    pending_records: int
    failed_records: int
    stale_records: int
    complete_records: int
    cumulative_estimated_cost_inr: float
    crawl_success_rate_30d: float


def _to_datetime(value: object) -> datetime | None:
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=UTC)
    if isinstance(value, str):
        normalized = value.replace("Z", "+00:00")
        try:
            parsed = datetime.fromisoformat(normalized)
        except ValueError:
            return None
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)
    return None


def _to_int(value: object) -> int:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        try:
            return int(float(value))
        except ValueError:
            return 0
    return 0


def _to_float(value: object) -> float:
    if isinstance(value, bool):
        return float(value)
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return 0.0
    return 0.0


def compute_pipeline_health_from_repositories(
    *,
    content_repository: InMemoryContentRepository,
    run_repository: InMemoryRunRepository,
    now: datetime | None = None,
) -> PipelineHealthSnapshot:
    """Compute pipeline-health metrics using in-memory demo repositories."""
    if now is None:
        now = datetime.now(tz=UTC)

    crawl_runs = run_repository.list_crawl_runs()
    analysis_runs = run_repository.list_analysis_runs()
    latest_crawl = crawl_runs[0] if crawl_runs else None
    latest_analysis = analysis_runs[0] if analysis_runs else None

    freshness_seconds: float | None = None
    if latest_crawl is not None and latest_crawl.finished_at is not None:
        freshness_seconds = max((now - latest_crawl.finished_at).total_seconds(), 0.0)

    window_start = now - timedelta(days=30)
    recent_crawl_runs = [run for run in crawl_runs if run.started_at >= window_start]
    successful_statuses = {"success", "partial", "budget_stopped"}
    successful_recent = [run for run in recent_crawl_runs if run.status in successful_statuses]
    crawl_success_rate_30d = (
        float(len(successful_recent)) / float(len(recent_crawl_runs)) if recent_crawl_runs else 0.0
    )

    post_statuses = [
        post.analysis_status for post in content_repository.iter_posts() if not post.is_deleted
    ]
    comment_statuses = [
        comment.analysis_status
        for comment in content_repository.iter_comments()
        if not comment.is_deleted
    ]
    statuses = post_statuses + comment_statuses
    pending_records = statuses.count("pending")
    stale_records = statuses.count("stale")
    failed_from_status = statuses.count("failed")
    complete_from_status = statuses.count("complete")
    failed_from_queue = len(run_repository.list_pipeline_failures(stage="analysis"))
    failed_records = max(failed_from_status, failed_from_queue)
    complete_records = max(complete_from_status, content_repository.analysis_count())

    cumulative_estimated_cost_inr = sum(run.estimated_cost_inr for run in analysis_runs)
    return PipelineHealthSnapshot(
        computed_at=now,
        latest_crawl_run_id=latest_crawl.run_id if latest_crawl else None,
        latest_crawl_status=latest_crawl.status if latest_crawl else None,
        latest_crawl_finished_at=latest_crawl.finished_at if latest_crawl else None,
        data_freshness_seconds=freshness_seconds,
        latest_analysis_run_id=latest_analysis.run_id if latest_analysis else None,
        latest_analysis_status=latest_analysis.status if latest_analysis else None,
        latest_analysis_finished_at=latest_analysis.finished_at if latest_analysis else None,
        pending_records=pending_records,
        failed_records=failed_records,
        stale_records=stale_records,
        complete_records=complete_records,
        cumulative_estimated_cost_inr=cumulative_estimated_cost_inr,
        crawl_success_rate_30d=crawl_success_rate_30d,
    )


def pipeline_health_from_view_row(
    row: Mapping[str, object],
    *,
    now: datetime | None = None,
) -> PipelineHealthSnapshot:
    """Parse v_pipeline_health row payload into typed snapshot."""
    resolved_now = now or datetime.now(tz=UTC)
    computed_at = _to_datetime(row.get("computed_at")) or resolved_now
    latest_crawl_finished_at = _to_datetime(row.get("latest_crawl_finished_at"))
    latest_analysis_finished_at = _to_datetime(row.get("latest_analysis_finished_at"))
    freshness_seconds: float | None
    if latest_crawl_finished_at is None:
        freshness_seconds = None
    else:
        freshness_seconds = max((resolved_now - latest_crawl_finished_at).total_seconds(), 0.0)
    return PipelineHealthSnapshot(
        computed_at=computed_at,
        latest_crawl_run_id=str(row.get("latest_crawl_run_id"))
        if row.get("latest_crawl_run_id") is not None
        else None,
        latest_crawl_status=str(row.get("latest_crawl_status"))
        if row.get("latest_crawl_status") is not None
        else None,
        latest_crawl_finished_at=latest_crawl_finished_at,
        data_freshness_seconds=freshness_seconds,
        latest_analysis_run_id=str(row.get("latest_analysis_run_id"))
        if row.get("latest_analysis_run_id") is not None
        else None,
        latest_analysis_status=str(row.get("latest_analysis_status"))
        if row.get("latest_analysis_status") is not None
        else None,
        latest_analysis_finished_at=latest_analysis_finished_at,
        pending_records=_to_int(row.get("pending_records")),
        failed_records=_to_int(row.get("failed_records")),
        stale_records=_to_int(row.get("stale_records")),
        complete_records=_to_int(row.get("complete_records")),
        cumulative_estimated_cost_inr=_to_float(row.get("cumulative_estimated_cost_inr")),
        crawl_success_rate_30d=_to_float(row.get("crawl_success_rate_30d")),
    )
