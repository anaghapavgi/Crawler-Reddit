"""Feature page for feature-level sentiment and top themes."""

from __future__ import annotations

import streamlit as st

from reddit_intelligence.analytics import DashboardAnalyticsBundle


def render(bundle: DashboardAnalyticsBundle) -> None:
    """Render feature summary table."""
    st.subheader("Features")
    rows = [
        {
            "feature": row.feature,
            "record_count": row.record_count,
            "avg_sentiment_score": round(row.avg_sentiment_score, 4),
            "negative_rate": round(row.negative_rate, 4),
            "top_theme": row.top_theme,
        }
        for row in bundle.snapshot.feature_summary
    ]
    if rows:
        st.dataframe(rows, use_container_width=True)
    else:
        st.info("No feature summary rows available for current filters.")
