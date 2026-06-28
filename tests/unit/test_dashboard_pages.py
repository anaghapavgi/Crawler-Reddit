from __future__ import annotations

from reddit_intelligence.dashboard import app
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


def test_dashboard_page_modules_export_render_functions() -> None:
    assert callable(overview.render)
    assert callable(sentiment.render)
    assert callable(pain_points.render)
    assert callable(features.render)
    assert callable(segments.render)
    assert callable(trends.render)
    assert callable(explorer.render)
    assert callable(assistant.render)
    assert callable(pipeline_health.render)


def test_dashboard_empty_state_message_text() -> None:
    assert app.empty_state_message() == "No records match current dashboard filters."
