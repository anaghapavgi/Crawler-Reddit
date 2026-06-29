"""Segments page for user-segment level view."""

from __future__ import annotations

import plotly.express as px  # type: ignore[import-untyped]
import streamlit as st

from reddit_intelligence.analytics import DashboardAnalyticsBundle


def render(bundle: DashboardAnalyticsBundle) -> None:
    """Render segment summary rows and comparisons."""
    st.subheader("Segments")
    rows = [
        {
            "segment": row.user_segment,
            "record_count": row.record_count,
            "avg_sentiment_score": round(row.avg_sentiment_score, 4),
            "top_pain_point": row.top_pain_point,
        }
        for row in bundle.snapshot.segment_summary
    ]
    if rows:
        segment_chart = px.scatter(
            rows,
            x="record_count",
            y="avg_sentiment_score",
            size="record_count",
            color="segment",
            title="Segment volume vs sentiment",
        )
        segment_chart.update_layout(
            xaxis_title="Relevant records", yaxis_title="Avg sentiment score"
        )
        st.plotly_chart(segment_chart, use_container_width=True)
        st.dataframe(rows, use_container_width=True)
    else:
        st.info("No segment rows available for current filters.")
