from __future__ import annotations

from pathlib import Path

import pytest

from reddit_intelligence.analytics.data_access import load_dashboard_analytics_bundle
from reddit_intelligence.config import Settings
from reddit_intelligence.db.repositories import InMemoryContentRepository, InMemoryRunRepository


def test_dashboard_analytics_bundle_uses_demo_adapter() -> None:
    settings = Settings.model_validate({"demo_mode": True})
    bundle = load_dashboard_analytics_bundle(
        settings=settings,
        days=30,
        demo_dataset_path=Path("data/demo/demo_dataset.csv"),
        content_repository=InMemoryContentRepository(),
        run_repository=InMemoryRunRepository(),
    )
    assert bundle.source == "demo_csv"
    assert len(bundle.records) > 0
    assert bundle.kpis.total_relevant_records > 0


def test_dashboard_analytics_bundle_live_mode_requires_supabase_credentials() -> None:
    settings = Settings.model_validate({"demo_mode": False})
    with pytest.raises(RuntimeError, match="Supabase credentials are required"):
        load_dashboard_analytics_bundle(
            settings=settings,
            days=30,
            content_repository=InMemoryContentRepository(),
            run_repository=InMemoryRunRepository(),
        )
