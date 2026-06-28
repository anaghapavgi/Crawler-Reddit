"""Analytics package."""

from reddit_intelligence.analytics.aggregates import (
    AggregationSnapshot,
    AnalyticsRecord,
    DailySentimentSummary,
    EmergingThemeSummary,
    FeatureSummary,
    SegmentSummary,
    ThemeSummary,
    build_aggregation_snapshot,
    load_analytics_records_from_csv,
)
from reddit_intelligence.analytics.data_access import (
    DashboardAnalyticsBundle,
    load_dashboard_analytics_bundle,
)
from reddit_intelligence.analytics.metrics import KpiSnapshot, compute_kpi_snapshot
from reddit_intelligence.analytics.pipeline_health import (
    PipelineHealthSnapshot,
    compute_pipeline_health_from_repositories,
    pipeline_health_from_view_row,
)
from reddit_intelligence.analytics.trends import (
    TrendValue,
    compute_sentiment_trend,
    compute_volume_trend,
)

__all__ = [
    "AggregationSnapshot",
    "AnalyticsRecord",
    "DailySentimentSummary",
    "DashboardAnalyticsBundle",
    "EmergingThemeSummary",
    "FeatureSummary",
    "KpiSnapshot",
    "PipelineHealthSnapshot",
    "SegmentSummary",
    "ThemeSummary",
    "TrendValue",
    "build_aggregation_snapshot",
    "compute_kpi_snapshot",
    "compute_pipeline_health_from_repositories",
    "compute_sentiment_trend",
    "compute_volume_trend",
    "load_dashboard_analytics_bundle",
    "load_analytics_records_from_csv",
    "pipeline_health_from_view_row",
]
