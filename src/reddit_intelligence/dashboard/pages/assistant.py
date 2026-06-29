"""Assistant page placeholder with evidence-bound guidance."""

from __future__ import annotations

import streamlit as st

from reddit_intelligence.analytics import DashboardAnalyticsBundle


def build_evidence_snippets(
    bundle: DashboardAnalyticsBundle, *, limit: int = 8
) -> list[dict[str, str]]:
    """Build deterministic evidence snippets from filtered records."""
    ranked_records = sorted(
        [record for record in bundle.records if record.relevant and not record.is_deleted],
        key=lambda record: (-record.severity, -record.confidence, record.source_reddit_id),
    )
    snippets: list[dict[str, str]] = []
    for record in ranked_records[:limit]:
        evidence = record.pain_point.strip()
        if not evidence:
            evidence = f"{record.theme} friction reported for {record.feature}"
        snippets.append(
            {
                "source_id": record.source_reddit_id,
                "subreddit": record.subreddit,
                "theme": record.theme,
                "feature": record.feature,
                "snippet": evidence[:240],
            }
        )
    return snippets


def render(bundle: DashboardAnalyticsBundle) -> None:
    """Render assistant placeholder bounded by analytics evidence."""
    st.subheader("Assistant")
    st.info(
        "Assistant responses are currently evidence-bounded placeholders. "
        "Use Explorer and Theme summaries for grounding."
    )
    top_themes = [row.theme for row in bundle.snapshot.emerging_themes[:5]]
    st.markdown("**Suggested focus themes**")
    if top_themes:
        st.write({"top_emerging_themes": top_themes})
    else:
        st.write({"top_emerging_themes": []})

    evidence_rows = build_evidence_snippets(bundle)
    st.markdown("**Evidence snippets (bounded to filtered data)**")
    if evidence_rows:
        st.dataframe(evidence_rows, use_container_width=True)
    else:
        st.info("No evidence snippets available for current filters.")
