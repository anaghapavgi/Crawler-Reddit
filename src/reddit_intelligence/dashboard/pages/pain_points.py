"""Pain-points page grouped by segment and top issues."""

from __future__ import annotations

import plotly.express as px  # type: ignore[import-untyped]
import streamlit as st

from reddit_intelligence.analytics import DashboardAnalyticsBundle


def render(bundle: DashboardAnalyticsBundle) -> None:
    """Render top pain points by user segment and evidence."""
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
        chart = px.bar(
            rows,
            x="segment",
            y="record_count",
            color="avg_sentiment_score",
            color_continuous_scale="RdYlGn",
            title="Pain-point mentions by segment",
        )
        chart.update_layout(xaxis_title="Segment", yaxis_title="Relevant records")
        st.plotly_chart(chart, use_container_width=True)
        st.dataframe(rows, use_container_width=True)

        evidence_rows = [
            {
                "segment": item.user_segment,
                "theme": item.theme,
                "feature": item.feature,
                "severity": item.severity,
                "confidence": round(item.confidence, 4),
                "evidence": item.pain_point or f"{item.theme} friction in {item.feature}",
            }
            for item in sorted(
                [record for record in bundle.records if record.relevant and not record.is_deleted],
                key=lambda record: (-record.severity, -record.confidence, record.source_reddit_id),
            )[:8]
        ]
        if evidence_rows:
            st.markdown("**High-severity evidence snippets**")
            st.dataframe(evidence_rows, use_container_width=True)
    else:
        st.info("No segment pain-point data available for current filters.")
