"""Dashboard data-access helpers with bounded cached analytics loading."""

from __future__ import annotations

from dataclasses import dataclass

import streamlit as st

from reddit_intelligence.analytics import (
    DashboardAnalyticsBundle,
    build_aggregation_snapshot,
    compute_kpi_snapshot,
    compute_sentiment_trend,
    compute_volume_trend,
    load_dashboard_analytics_bundle,
)
from reddit_intelligence.config import load_research_config, load_settings


@dataclass(frozen=True)
class DashboardFilters:
    """Serializable dashboard filter state."""

    days: int
    subreddits: tuple[str, ...] = ()
    themes: tuple[str, ...] = ()
    features: tuple[str, ...] = ()
    segments: tuple[str, ...] = ()
    sentiment_labels: tuple[str, ...] = ()


def _load_dashboard_bundle_uncached(days: int = 30) -> DashboardAnalyticsBundle:
    settings = load_settings()
    return load_dashboard_analytics_bundle(
        settings=settings,
        days=days,
    )


@st.cache_data(ttl=60, show_spinner=False)
def load_dashboard_bundle(days: int = 30) -> DashboardAnalyticsBundle:
    """Load dashboard analytics from source adapter with cache bounds."""
    return _load_dashboard_bundle_uncached(days=days)


def clear_dashboard_bundle_cache() -> None:
    """Clear cached dashboard data bundle (useful in tests/dev loops)."""
    load_dashboard_bundle.clear()


def dashboard_default_days() -> int:
    """Read dashboard default lookback days from research config."""
    research = load_research_config()
    return research.dashboard.default_days


def build_filter_options(bundle: DashboardAnalyticsBundle) -> dict[str, list[str]]:
    """Build unique, sorted filter options from loaded records."""
    records = bundle.records
    return {
        "subreddits": sorted({record.subreddit for record in records}),
        "themes": sorted({record.theme for record in records}),
        "features": sorted({record.feature for record in records}),
        "segments": sorted({record.user_segment for record in records}),
        "sentiment_labels": sorted({record.sentiment_label for record in records}),
    }


def apply_dashboard_filters(
    *,
    bundle: DashboardAnalyticsBundle,
    filters: DashboardFilters,
) -> DashboardAnalyticsBundle:
    """Apply filter state to bundle records and recompute summaries."""
    subreddit_filter = set(filters.subreddits)
    theme_filter = set(filters.themes)
    feature_filter = set(filters.features)
    segment_filter = set(filters.segments)
    sentiment_filter = set(filters.sentiment_labels)

    filtered_records = [
        record
        for record in bundle.records
        if (not subreddit_filter or record.subreddit in subreddit_filter)
        and (not theme_filter or record.theme in theme_filter)
        and (not feature_filter or record.feature in feature_filter)
        and (not segment_filter or record.user_segment in segment_filter)
        and (not sentiment_filter or record.sentiment_label in sentiment_filter)
    ]
    filtered_snapshot = build_aggregation_snapshot(records=filtered_records)
    filtered_kpis = compute_kpi_snapshot(filtered_records, days=filters.days)
    filtered_volume_trend = compute_volume_trend(filtered_records, days=filters.days)
    filtered_sentiment_trend = compute_sentiment_trend(filtered_records, days=filters.days)
    return DashboardAnalyticsBundle(
        source=bundle.source,
        records=filtered_records,
        snapshot=filtered_snapshot,
        kpis=filtered_kpis,
        volume_trend=filtered_volume_trend,
        sentiment_trend=filtered_sentiment_trend,
        pipeline_health=bundle.pipeline_health,
    )
