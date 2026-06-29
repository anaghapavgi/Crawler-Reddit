"""Overview page for high-level KPIs."""

from __future__ import annotations

import plotly.express as px  # type: ignore[import-untyped]
import streamlit as st

from reddit_intelligence.analytics import DashboardAnalyticsBundle


def render(bundle: DashboardAnalyticsBundle) -> None:
    """Render overview metrics and high-signal comparisons."""
    st.subheader("Overview")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Relevant Records", str(bundle.kpis.total_relevant_records))
    col2.metric("Avg Sentiment", f"{bundle.kpis.avg_sentiment_score:.3f}")
    col3.metric("Negative Rate", f"{bundle.kpis.negative_rate:.1%}")
    col4.metric("Avg Confidence", f"{bundle.kpis.avg_confidence:.1%}")

    compare_left, compare_right = st.columns(2)
    compare_left.metric(
        "Volume: current vs previous window",
        f"{bundle.volume_trend.current_value:.0f}",
        delta=f"{bundle.volume_trend.delta_absolute:+.0f}",
    )
    compare_right.metric(
        "Sentiment: current vs previous window",
        f"{bundle.sentiment_trend.current_value:.3f}",
        delta=f"{bundle.sentiment_trend.delta_absolute:+.3f}",
    )

    top_themes = bundle.snapshot.theme_summary[:10]
    if top_themes:
        chart_rows = [
            {
                "theme": item.theme,
                "records": item.record_count,
                "negative_rate": item.negative_rate,
            }
            for item in top_themes
        ]
        theme_chart = px.bar(
            chart_rows,
            x="theme",
            y="records",
            color="negative_rate",
            color_continuous_scale="Reds",
            title="Top themes by relevant mention volume",
        )
        theme_chart.update_layout(xaxis_title="Theme", yaxis_title="Relevant records")
        st.plotly_chart(theme_chart, use_container_width=True)

    st.caption(
        "Source="
        f"{bundle.source} | Daily points={len(bundle.snapshot.daily_sentiment)} | "
        f"Themes={len(bundle.snapshot.theme_summary)}"
    )
