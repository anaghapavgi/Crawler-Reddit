"""Trends page for volume and sentiment deltas."""

from __future__ import annotations

import streamlit as st

from reddit_intelligence.analytics import DashboardAnalyticsBundle


def _format_percent(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{value:.2%}"


def render(bundle: DashboardAnalyticsBundle) -> None:
    """Render trend cards for volume and sentiment shifts."""
    st.subheader("Trends")
    col1, col2 = st.columns(2)
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
