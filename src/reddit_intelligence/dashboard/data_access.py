"""Dashboard data-access helpers with bounded cached analytics loading."""

from __future__ import annotations

import streamlit as st

from reddit_intelligence.analytics import DashboardAnalyticsBundle, load_dashboard_analytics_bundle
from reddit_intelligence.config import load_research_config, load_settings


@st.cache_data(ttl=60, show_spinner=False)
def load_dashboard_bundle(days: int = 30) -> DashboardAnalyticsBundle:
    """Load dashboard analytics from source adapter with cache bounds."""
    settings = load_settings()
    return load_dashboard_analytics_bundle(
        settings=settings,
        days=days,
    )


def dashboard_default_days() -> int:
    """Read dashboard default lookback days from research config."""
    research = load_research_config()
    return research.dashboard.default_days
