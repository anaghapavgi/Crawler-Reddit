"""Pain-points page grouped by segment and top issues."""

from __future__ import annotations

import streamlit as st

from reddit_intelligence.analytics import DashboardAnalyticsBundle


def render(bundle: DashboardAnalyticsBundle) -> None:
    """Render top pain points by user segment."""
    st.subheader("Pain Points")
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
        st.dataframe(rows, use_container_width=True)
    else:
        st.info("No segment pain-point data available for current filters.")
