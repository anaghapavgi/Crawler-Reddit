"""Overview page for high-level KPIs."""

from __future__ import annotations

import streamlit as st

from reddit_intelligence.analytics import DashboardAnalyticsBundle


def render(bundle: DashboardAnalyticsBundle) -> None:
    """Render overview metrics and quick counts."""
    st.subheader("Overview")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Relevant Records", str(bundle.kpis.total_relevant_records))
    col2.metric("Avg Sentiment", f"{bundle.kpis.avg_sentiment_score:.3f}")
    col3.metric("Negative Rate", f"{bundle.kpis.negative_rate:.1%}")
    col4.metric("Avg Confidence", f"{bundle.kpis.avg_confidence:.1%}")
    st.caption(
        "Source="
        f"{bundle.source} | Daily points={len(bundle.snapshot.daily_sentiment)} | "
        f"Themes={len(bundle.snapshot.theme_summary)}"
    )
