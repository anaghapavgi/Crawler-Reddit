"""Dashboard entrypoint scaffold."""

from __future__ import annotations

from collections.abc import Callable

import streamlit as st

from reddit_intelligence.analytics import DashboardAnalyticsBundle
from reddit_intelligence.dashboard.data_access import (
    DashboardFilters,
    apply_dashboard_filters,
    build_filter_options,
    dashboard_default_days,
    load_dashboard_bundle,
)
from reddit_intelligence.dashboard.pages import (
    assistant,
    explorer,
    features,
    overview,
    pain_points,
    pipeline_health,
    segments,
    sentiment,
    trends,
)

PAGE_RENDERERS: dict[str, Callable[[DashboardAnalyticsBundle], None]] = {
    "Overview": overview.render,
    "Sentiment": sentiment.render,
    "Pain Points": pain_points.render,
    "Features": features.render,
    "Segments": segments.render,
    "Trends": trends.render,
    "Explorer": explorer.render,
    "Assistant": assistant.render,
    "Pipeline Health": pipeline_health.render,
}


def empty_state_message() -> str:
    """Message shown when filters produce no records."""
    return "No records match current dashboard filters."


def main() -> None:
    """Render dashboard with page navigation and shared filters."""
    st.set_page_config(page_title="Reddit Product Intelligence", layout="wide")
    st.title("Reddit Product Intelligence")
    try:
        default_days = dashboard_default_days()
        days = int(
            st.sidebar.number_input(
                "Lookback days",
                min_value=7,
                max_value=180,
                value=default_days,
                step=1,
            )
        )
        bundle = load_dashboard_bundle(days=days)
    except Exception as exc:  # noqa: BLE001
        st.error(f"Dashboard data load failed: {exc}")
        st.info("Run `python3 -m reddit_intelligence.cli seed-demo` to refresh demo data.")
        return

    options = build_filter_options(bundle)
    selected_subreddits = st.sidebar.multiselect("Subreddits", options["subreddits"])
    selected_themes = st.sidebar.multiselect("Themes", options["themes"])
    selected_features = st.sidebar.multiselect("Features", options["features"])
    selected_segments = st.sidebar.multiselect("Segments", options["segments"])
    selected_sentiments = st.sidebar.multiselect("Sentiment labels", options["sentiment_labels"])
    filters = DashboardFilters(
        days=days,
        subreddits=tuple(selected_subreddits),
        themes=tuple(selected_themes),
        features=tuple(selected_features),
        segments=tuple(selected_segments),
        sentiment_labels=tuple(selected_sentiments),
    )
    filtered_bundle = apply_dashboard_filters(bundle=bundle, filters=filters)
    page_name = st.sidebar.selectbox("Page", list(PAGE_RENDERERS))

    st.caption(
        f"Analytics source: {filtered_bundle.source} | "
        f"Filtered records: {len(filtered_bundle.records)}"
    )
    if not filtered_bundle.records:
        st.warning(empty_state_message())
        return
    PAGE_RENDERERS[page_name](filtered_bundle)


if __name__ == "__main__":
    main()
