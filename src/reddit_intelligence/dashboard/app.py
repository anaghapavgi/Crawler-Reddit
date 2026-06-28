"""Dashboard entrypoint scaffold."""

from __future__ import annotations

import streamlit as st

from reddit_intelligence.dashboard.data_access import dashboard_default_days, load_dashboard_bundle


def main() -> None:
    """Render dashboard home with initial analytics snapshot."""
    st.set_page_config(page_title="Reddit Product Intelligence", layout="wide")
    st.title("Reddit Product Intelligence")
    try:
        days = dashboard_default_days()
        bundle = load_dashboard_bundle(days=days)
    except Exception as exc:  # noqa: BLE001
        st.error(f"Dashboard data load failed: {exc}")
        st.info("Run `python3 -m reddit_intelligence.cli seed-demo` to refresh demo data.")
        return

    st.caption(f"Analytics source: {bundle.source}")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Relevant Records", str(bundle.kpis.total_relevant_records))
    col2.metric("Avg Sentiment", f"{bundle.kpis.avg_sentiment_score:.3f}")
    col3.metric("Negative Rate", f"{bundle.kpis.negative_rate:.1%}")
    col4.metric("Crawl Success (30d)", f"{bundle.pipeline_health.crawl_success_rate_30d:.1%}")

    st.subheader("Pipeline Health")
    st.write(
        {
            "pending_records": bundle.pipeline_health.pending_records,
            "failed_records": bundle.pipeline_health.failed_records,
            "stale_records": bundle.pipeline_health.stale_records,
            "complete_records": bundle.pipeline_health.complete_records,
            "cumulative_estimated_cost_inr": round(
                bundle.pipeline_health.cumulative_estimated_cost_inr,
                4,
            ),
        }
    )
    st.subheader("Emerging Themes")
    emerging_rows = [
        {
            "theme": row.theme,
            "recent_weekly_volume": row.recent_weekly_volume,
            "baseline_weekly_volume": round(row.baseline_weekly_volume, 3),
            "emergence_score": round(row.emergence_score, 3),
            "recent_negative_rate": round(row.recent_negative_rate, 3),
        }
        for row in bundle.snapshot.emerging_themes[:10]
    ]
    if emerging_rows:
        st.dataframe(emerging_rows, use_container_width=True)
    else:
        st.info("No emerging themes crossed thresholds in current window.")


if __name__ == "__main__":
    main()
