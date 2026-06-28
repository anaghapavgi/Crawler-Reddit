from __future__ import annotations

from reddit_intelligence.pipeline import run_demo_pipeline


def test_run_demo_pipeline_returns_success() -> None:
    summary = run_demo_pipeline()
    assert summary.status == "success"
    assert summary.message
