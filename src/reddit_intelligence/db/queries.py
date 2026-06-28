"""Shared SQL query names/constants."""

from __future__ import annotations

ANALYTICS_VIEWS: tuple[str, ...] = (
    "v_analysed_content",
    "v_daily_sentiment",
    "v_theme_summary",
    "v_feature_summary",
    "v_segment_summary",
    "v_pipeline_health",
    "v_emerging_themes",
)
