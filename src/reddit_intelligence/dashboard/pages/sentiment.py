"""Sentiment page for daily and aggregate sentiment views."""

from __future__ import annotations

from collections import defaultdict

import plotly.express as px  # type: ignore[import-untyped]
import streamlit as st

from reddit_intelligence.analytics import DashboardAnalyticsBundle


def _sentiment_timeseries_rows(bundle: DashboardAnalyticsBundle) -> list[dict[str, float | str]]:
    """Build weighted daily sentiment rows for charting."""
    daily_weighted_score: dict[str, float] = defaultdict(float)
    daily_record_count: dict[str, int] = defaultdict(int)
    for row in bundle.snapshot.daily_sentiment:
        key = row.day.isoformat()
        daily_weighted_score[key] += row.avg_sentiment_score * float(row.record_count)
        daily_record_count[key] += row.record_count
    output: list[dict[str, float | str]] = []
    for day in sorted(daily_record_count):
        total = daily_record_count[day]
        avg = daily_weighted_score[day] / float(total) if total else 0.0
        output.append({"day": day, "avg_sentiment_score": avg, "record_count": float(total)})
    return output


def render(bundle: DashboardAnalyticsBundle) -> None:
    """Render sentiment summary table and trend visual."""
    st.subheader("Sentiment")
    trend_rows = _sentiment_timeseries_rows(bundle)
    if trend_rows:
        line_chart = px.line(
            trend_rows,
            x="day",
            y="avg_sentiment_score",
            markers=True,
            title="Daily weighted sentiment trend",
        )
        line_chart.update_layout(
            xaxis_title="Day",
            yaxis_title="Avg sentiment",
            yaxis=dict(range=[-1.0, 1.0]),
        )
        st.plotly_chart(line_chart, use_container_width=True)

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
