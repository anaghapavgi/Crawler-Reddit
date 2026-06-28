"""Assistant page placeholder with evidence-bound guidance."""

from __future__ import annotations

import streamlit as st

from reddit_intelligence.analytics import DashboardAnalyticsBundle


def render(bundle: DashboardAnalyticsBundle) -> None:
    """Render assistant placeholder bounded by analytics evidence."""
    st.subheader("Assistant")
    st.info(
        "Assistant responses are currently evidence-bounded placeholders. "
        "Use Explorer and Theme summaries for grounding."
    )
    top_themes = [row.theme for row in bundle.snapshot.emerging_themes[:3]]
    if top_themes:
        st.write({"top_emerging_themes": top_themes})
    else:
        st.write({"top_emerging_themes": []})
