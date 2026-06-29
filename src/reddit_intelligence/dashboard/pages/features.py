"""Feature page for feature-level sentiment and top themes."""

from __future__ import annotations

import plotly.express as px  # type: ignore[import-untyped]
import streamlit as st

from reddit_intelligence.analytics import DashboardAnalyticsBundle


def render(bundle: DashboardAnalyticsBundle) -> None:
    """Render feature summary table and comparisons."""
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
        top_rows = rows[:12]
        feature_chart = px.bar(
            top_rows,
            x="feature",
            y="negative_rate",
            color="record_count",
            title="Negative-rate comparison by feature",
        )
        feature_chart.update_layout(
            xaxis_title="Feature",
            yaxis_title="Negative rate",
            yaxis_tickformat=".0%",
        )
        st.plotly_chart(feature_chart, use_container_width=True)
        st.dataframe(rows, use_container_width=True)
    else:
        st.info("No feature summary rows available for current filters.")
