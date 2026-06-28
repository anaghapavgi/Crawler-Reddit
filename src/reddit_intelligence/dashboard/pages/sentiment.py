"""Sentiment page for daily and aggregate sentiment views."""

from __future__ import annotations

import streamlit as st

from reddit_intelligence.analytics import DashboardAnalyticsBundle


def render(bundle: DashboardAnalyticsBundle) -> None:
    """Render sentiment summary table."""
    st.subheader("Sentiment")
    rows = [
        {
            "day": row.day.isoformat(),
            "subreddit": row.subreddit,
            "sentiment_label": row.sentiment_label,
            "record_count": row.record_count,
            "avg_sentiment_score": round(row.avg_sentiment_score, 4),
            "avg_severity": round(row.avg_severity, 4),
        }
        for row in bundle.snapshot.daily_sentiment
    ]
    if rows:
        st.dataframe(rows, use_container_width=True)
    else:
        st.info("No sentiment rows available for current filters.")
