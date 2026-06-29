"""Explorer page for raw filtered records."""

from __future__ import annotations

import csv
from io import StringIO

import streamlit as st

from reddit_intelligence.analytics import DashboardAnalyticsBundle

_DANGEROUS_CSV_PREFIXES = ("=", "+", "-", "@")


def sanitize_csv_cell(value: object) -> str:
    """Sanitize CSV cell values to avoid spreadsheet formula execution."""
    text = str(value)
    stripped = text.lstrip()
    if not stripped:
        return text
    if text[0] in {"\t", "\r"} or stripped[0] in _DANGEROUS_CSV_PREFIXES:
        return f"'{text}"
    return text


def build_explorer_rows(
    bundle: DashboardAnalyticsBundle, *, max_rows: int = 500
) -> list[dict[str, object]]:
    """Build bounded explorer rows from filtered records."""
    return [
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
            "pain_point": record.pain_point,
        }
        for record in bundle.records[:max_rows]
    ]


def build_explorer_export_csv(rows: list[dict[str, object]]) -> str:
    """Build sanitized CSV payload for download/export."""
    if not rows:
        return ""
    fields = list(rows[0].keys())
    buffer = StringIO()
    writer = csv.DictWriter(buffer, fieldnames=fields)
    writer.writeheader()
    for row in rows:
        writer.writerow({key: sanitize_csv_cell(row.get(key, "")) for key in fields})
    return buffer.getvalue()


def render(bundle: DashboardAnalyticsBundle) -> None:
    """Render record-level explorer table with bounded rows."""
    st.subheader("Explorer")
    rows = build_explorer_rows(bundle, max_rows=500)
    if rows:
        st.dataframe(rows, use_container_width=True)
        csv_payload = build_explorer_export_csv(rows)
        st.download_button(
            "Download filtered rows (CSV)",
            data=csv_payload,
            file_name="reddit_intelligence_explorer.csv",
            mime="text/csv",
        )
        st.caption("CSV export sanitizes spreadsheet formula-like cell values.")
        st.caption(f"Showing {len(rows)} rows (bounded to 500).")
    else:
        st.info("No explorer rows available for current filters.")
