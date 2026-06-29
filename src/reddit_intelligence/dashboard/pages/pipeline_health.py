"""Pipeline health page for operational run metrics."""

from __future__ import annotations

import plotly.express as px  # type: ignore[import-untyped]
import streamlit as st

from reddit_intelligence.analytics import DashboardAnalyticsBundle


def render(bundle: DashboardAnalyticsBundle) -> None:
    """Render pipeline health metrics."""
    st.subheader("Pipeline Health")
    health = bundle.pipeline_health
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Pending", str(health.pending_records))
    col2.metric("Failed", str(health.failed_records))
    col3.metric("Stale", str(health.stale_records))
    col4.metric("Complete", str(health.complete_records))

    status_rows = [
        {"status": "pending", "count": health.pending_records},
        {"status": "failed", "count": health.failed_records},
        {"status": "stale", "count": health.stale_records},
        {"status": "complete", "count": health.complete_records},
    ]
    status_chart = px.bar(
        status_rows,
        x="status",
        y="count",
        color="status",
        title="Pipeline record status distribution",
    )
    status_chart.update_layout(showlegend=False, xaxis_title="Status", yaxis_title="Count")
    st.plotly_chart(status_chart, use_container_width=True)

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
