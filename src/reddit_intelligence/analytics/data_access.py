"""Analytics source adapters for demo CSV and live SQL views."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Protocol

from reddit_intelligence.analytics.aggregates import (
    AggregationSnapshot,
    AnalyticsRecord,
    build_aggregation_snapshot,
    load_analytics_records_from_csv,
)
from reddit_intelligence.analytics.metrics import KpiSnapshot, compute_kpi_snapshot
from reddit_intelligence.analytics.pipeline_health import (
    PipelineHealthSnapshot,
    compute_pipeline_health_from_repositories,
    pipeline_health_from_view_row,
)
from reddit_intelligence.analytics.trends import TrendValue, compute_sentiment_trend, compute_volume_trend
from reddit_intelligence.config import Settings
from reddit_intelligence.db.client import get_supabase_client
from reddit_intelligence.db.repositories import InMemoryContentRepository, InMemoryRunRepository
from reddit_intelligence.runtime_state import get_demo_repositories


@dataclass(frozen=True)
class DashboardAnalyticsBundle:
    """Single payload used by CLI aggregate and dashboard views."""

    source: str
    records: list[AnalyticsRecord]
    snapshot: AggregationSnapshot
    kpis: KpiSnapshot
    volume_trend: TrendValue
    sentiment_trend: TrendValue
    pipeline_health: PipelineHealthSnapshot


class AnalyticsSourceAdapter(Protocol):
    """Source adapter contract for analytics inputs."""

    source_name: str

    def load_records(self, *, days: int) -> list[AnalyticsRecord]:
        """Load normalized analytics records for downstream computations."""

    def load_pipeline_health(self) -> PipelineHealthSnapshot:
        """Load pipeline-health snapshot from source-native data."""


class DemoCsvAnalyticsAdapter:
    """Demo adapter using deterministic CSV artifacts + in-memory run metadata."""

    source_name = "demo_csv"

    def __init__(
        self,
        *,
        dataset_path: Path,
        content_repository: InMemoryContentRepository,
        run_repository: InMemoryRunRepository,
    ) -> None:
        self.dataset_path = dataset_path
        self.content_repository = content_repository
        self.run_repository = run_repository

    def load_records(self, *, days: int) -> list[AnalyticsRecord]:
        records = load_analytics_records_from_csv(self.dataset_path)
        if not records:
            return []
        reference_day = max(record.day for record in records) + timedelta(days=1)
        window_start = reference_day - timedelta(days=days * 2)
        return [record for record in records if record.day >= window_start]

    def load_pipeline_health(self) -> PipelineHealthSnapshot:
        return compute_pipeline_health_from_repositories(
            content_repository=self.content_repository,
            run_repository=self.run_repository,
        )


def _parse_day(value: object) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        normalized = value.replace("Z", "+00:00")
        try:
            return datetime.fromisoformat(normalized).date()
        except ValueError:
            return date.today()
    return date.today()


def _as_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"true", "1", "yes"}
    if isinstance(value, (int, float)):
        return bool(value)
    return False


def _as_float(value: object) -> float:
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


def _as_int(value: object) -> int:
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


class SupabaseViewAnalyticsAdapter:
    """Live adapter that reads analytics SQL views through Supabase."""

    source_name = "live_sql_views"

    def __init__(self, settings: Settings, *, max_rows: int = 5000) -> None:
        client = get_supabase_client(settings)
        if client is None:
            msg = "Supabase client unavailable for live analytics adapter."
            raise RuntimeError(msg)
        self._client = client
        self._max_rows = max_rows

    def load_records(self, *, days: int) -> list[AnalyticsRecord]:
        start_date = (datetime.now(tz=UTC) - timedelta(days=days * 2)).date().isoformat()
        response = (
            self._client.table("v_analysed_content")
            .select("*")
            .gte("source_created_utc", start_date)
            .range(0, self._max_rows - 1)
            .execute()
        )
        rows = response.data if isinstance(response.data, list) else []
        records: list[AnalyticsRecord] = []
        for row in rows:
            source_type = "post" if str(row.get("source_type", "comment")) == "post" else "comment"
            records.append(
                AnalyticsRecord(
                    day=_parse_day(row.get("source_created_utc")),
                    subreddit=str(row.get("subreddit", "")),
                    source_type=source_type,
                    source_reddit_id=str(row.get("source_reddit_id", "")),
                    sentiment_label=str(row.get("sentiment_label", "unknown")),
                    sentiment_score=_as_float(row.get("sentiment_score")),
                    theme=str(row.get("theme", "other")),
                    subtheme=str(row.get("subtheme", "other")),
                    feature=str(row.get("feature", "Unknown")),
                    user_segment=str(row.get("user_segment", "unknown")),
                    pain_point=str(row.get("pain_point", "")),
                    severity=_as_int(row.get("severity")),
                    confidence=_as_float(row.get("confidence")),
                    sarcasm_detected=_as_bool(row.get("sarcasm_detected")),
                    relevant=_as_bool(row.get("relevant")),
                    is_deleted=False,
                )
            )
        return records

    def load_pipeline_health(self) -> PipelineHealthSnapshot:
        response = self._client.table("v_pipeline_health").select("*").limit(1).execute()
        rows = response.data if isinstance(response.data, list) else []
        if not rows:
            now = datetime.now(tz=UTC)
            return PipelineHealthSnapshot(
                computed_at=now,
                latest_crawl_run_id=None,
                latest_crawl_status=None,
                latest_crawl_finished_at=None,
                data_freshness_seconds=None,
                latest_analysis_run_id=None,
                latest_analysis_status=None,
                latest_analysis_finished_at=None,
                pending_records=0,
                failed_records=0,
                stale_records=0,
                complete_records=0,
                cumulative_estimated_cost_inr=0.0,
                crawl_success_rate_30d=0.0,
            )
        return pipeline_health_from_view_row(rows[0], now=datetime.now(tz=UTC))


def load_dashboard_analytics_bundle(
    *,
    settings: Settings,
    days: int,
    demo_dataset_path: Path = Path("data/demo/demo_dataset.csv"),
    content_repository: InMemoryContentRepository | None = None,
    run_repository: InMemoryRunRepository | None = None,
    max_rows: int = 5000,
) -> DashboardAnalyticsBundle:
    """Load analytics bundle from demo or live source adapter."""
    if settings.demo_mode:
        repo_content, repo_runs = get_demo_repositories()
        adapter: AnalyticsSourceAdapter = DemoCsvAnalyticsAdapter(
            dataset_path=demo_dataset_path,
            content_repository=content_repository or repo_content,
            run_repository=run_repository or repo_runs,
        )
    else:
        adapter = SupabaseViewAnalyticsAdapter(settings, max_rows=max_rows)

    records = adapter.load_records(days=days)
    snapshot = build_aggregation_snapshot(records=records)
    kpis = compute_kpi_snapshot(records, days=days)
    volume_trend = compute_volume_trend(records, days=days)
    sentiment_trend = compute_sentiment_trend(records, days=days)
    pipeline_health = adapter.load_pipeline_health()
    return DashboardAnalyticsBundle(
        source=adapter.source_name,
        records=records,
        snapshot=snapshot,
        kpis=kpis,
        volume_trend=volume_trend,
        sentiment_trend=sentiment_trend,
        pipeline_health=pipeline_health,
    )
