"""Explorer page for raw filtered records."""

from __future__ import annotations

import streamlit as st

from reddit_intelligence.analytics import DashboardAnalyticsBundle


def render(bundle: DashboardAnalyticsBundle) -> None:
    """Render record-level explorer table with bounded rows."""
    st.subheader("Explorer")
    rows = [
        {
            "day": record.day.isoformat(),
            "subreddit": record.subreddit,
            "source_type": record.source_type,
            "source_reddit_id": record.source_reddit_id,
            "sentiment_label": record.sentiment_label,
            "sentiment_score": round(record.sentiment_score, 4),
            "theme": record.theme,
            "feature": record.feature,
            "segment": record.user_segment,
            "confidence": round(record.confidence, 4),
        }
        for record in bundle.records[:500]
    ]
    if rows:
        st.dataframe(rows, use_container_width=True)
        st.caption(f"Showing {len(rows)} rows (bounded to 500).")
    else:
        st.info("No explorer rows available for current filters.")
