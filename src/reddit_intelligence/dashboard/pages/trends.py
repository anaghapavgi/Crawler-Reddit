"""Trends page for volume and sentiment deltas."""

from __future__ import annotations

import plotly.express as px  # type: ignore[import-untyped]
import streamlit as st

from reddit_intelligence.analytics import DashboardAnalyticsBundle


def _format_percent(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{value:.2%}"


def render(bundle: DashboardAnalyticsBundle) -> None:
    """Render trend cards for volume and sentiment shifts."""
    st.subheader("Trends")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric(
        "Volume (Current Window)",
        f"{bundle.volume_trend.current_value:.0f}",
        delta=(
            f"{bundle.volume_trend.delta_absolute:+.0f} "
            f"({_format_percent(bundle.volume_trend.delta_percent)})"
        ),
    )
    col2.metric(
        "Sentiment (Current Window)",
        f"{bundle.sentiment_trend.current_value:.3f}",
        delta=(
            f"{bundle.sentiment_trend.delta_absolute:+.3f} "
            f"({_format_percent(bundle.sentiment_trend.delta_percent)})"
        ),
    )
    col3.metric("Volume (Previous Window)", f"{bundle.volume_trend.previous_value:.0f}")
    col4.metric("Sentiment (Previous Window)", f"{bundle.sentiment_trend.previous_value:.3f}")

    sentiment_mix_rows = [
        {
            "day": row.day.isoformat(),
            "sentiment_label": row.sentiment_label,
            "record_count": row.record_count,
        }
        for row in bundle.snapshot.daily_sentiment
    ]
    if sentiment_mix_rows:
        mix_chart = px.area(
            sentiment_mix_rows,
            x="day",
            y="record_count",
            color="sentiment_label",
            title="Daily sentiment mix by volume",
        )
        mix_chart.update_layout(xaxis_title="Day", yaxis_title="Records")
        st.plotly_chart(mix_chart, use_container_width=True)
