"""Pipeline health page for operational run metrics."""

from __future__ import annotations

import streamlit as st

from reddit_intelligence.analytics import DashboardAnalyticsBundle


def render(bundle: DashboardAnalyticsBundle) -> None:
    """Render pipeline health metrics."""
    st.subheader("Pipeline Health")
    health = bundle.pipeline_health
    st.write(
        {
            "latest_crawl_run_id": health.latest_crawl_run_id,
            "latest_crawl_status": health.latest_crawl_status,
            "latest_analysis_run_id": health.latest_analysis_run_id,
            "latest_analysis_status": health.latest_analysis_status,
            "pending_records": health.pending_records,
            "failed_records": health.failed_records,
            "stale_records": health.stale_records,
            "complete_records": health.complete_records,
            "cumulative_estimated_cost_inr": round(health.cumulative_estimated_cost_inr, 4),
            "crawl_success_rate_30d": round(health.crawl_success_rate_30d, 4),
            "data_freshness_seconds": None
            if health.data_freshness_seconds is None
            else round(health.data_freshness_seconds, 2),
        }
    )
