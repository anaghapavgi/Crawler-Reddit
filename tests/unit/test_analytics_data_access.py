from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

import reddit_intelligence.analytics.data_access as data_access_module
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


class _FakeQuery:
    def __init__(self, client: _FakeClient, table_name: str) -> None:
        self.client = client
        self.table_name = table_name
        self.range_args: tuple[int, int] | None = None
        self.limit_arg: int | None = None
        self.gte_args: tuple[str, str] | None = None

    def select(self, _columns: str) -> _FakeQuery:
        return self

    def gte(self, column: str, value: str) -> _FakeQuery:
        self.gte_args = (column, value)
        return self

    def range(self, start: int, end: int) -> _FakeQuery:
        self.range_args = (start, end)
        return self

    def limit(self, size: int) -> _FakeQuery:
        self.limit_arg = size
        return self

    def execute(self) -> SimpleNamespace:
        data = self.client.table_rows.get(self.table_name, [])
        return SimpleNamespace(data=data)


class _FakeClient:
    def __init__(self) -> None:
        self.queries: dict[str, _FakeQuery] = {}
        self.table_rows: dict[str, list[dict[str, object]]] = {
            "v_analysed_content": [
                {
                    "source_type": "comment",
                    "source_created_utc": "2026-01-20T00:00:00+00:00",
                    "subreddit": "spotify",
                    "source_reddit_id": "abc",
                    "sentiment_label": "negative",
                    "sentiment_score": -0.45,
                    "theme": "pricing",
                    "subtheme": "monthly",
                    "feature": "Search",
                    "user_segment": "unknown",
                    "pain_point": "Too expensive",
                    "severity": 4,
                    "confidence": 0.81,
                    "sarcasm_detected": False,
                    "relevant": True,
                }
            ],
            "v_pipeline_health": [
                {
                    "computed_at": "2026-01-21T00:00:00+00:00",
                    "latest_crawl_run_id": "crawl-1",
                    "latest_crawl_status": "success",
                    "latest_crawl_finished_at": "2026-01-20T22:00:00+00:00",
                    "latest_analysis_run_id": "analysis-1",
                    "latest_analysis_status": "partial",
                    "latest_analysis_finished_at": "2026-01-20T22:30:00+00:00",
                    "pending_records": 3,
                    "failed_records": 1,
                    "stale_records": 1,
                    "complete_records": 12,
                    "cumulative_estimated_cost_inr": 12.3,
                    "crawl_success_rate_30d": 0.8,
                }
            ],
        }

    def table(self, table_name: str) -> _FakeQuery:
        query = _FakeQuery(self, table_name)
        self.queries[table_name] = query
        return query


def test_live_adapter_applies_bounded_pagination(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_client = _FakeClient()
    monkeypatch.setattr(data_access_module, "get_supabase_client", lambda _settings: fake_client)
    settings = Settings.model_validate(
        {
            "demo_mode": False,
            "supabase_url": "https://example.supabase.co",
            "supabase_service_role_key": "service-role-key",
        }
    )
    adapter = data_access_module.SupabaseViewAnalyticsAdapter(settings, max_rows=124)
    records = adapter.load_records(days=21)
    assert len(records) == 1
    assert fake_client.queries["v_analysed_content"].range_args == (0, 123)
    assert fake_client.queries["v_analysed_content"].gte_args is not None


def test_live_bundle_loader_uses_sql_view_adapter(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_client = _FakeClient()
    monkeypatch.setattr(data_access_module, "get_supabase_client", lambda _settings: fake_client)
    settings = Settings.model_validate(
        {
            "demo_mode": False,
            "supabase_url": "https://example.supabase.co",
            "supabase_service_role_key": "service-role-key",
        }
    )
    bundle = load_dashboard_analytics_bundle(settings=settings, days=30, max_rows=77)
    assert bundle.source == "live_sql_views"
    assert fake_client.queries["v_analysed_content"].range_args == (0, 76)
    assert fake_client.queries["v_pipeline_health"].limit_arg == 1
    assert bundle.pipeline_health.latest_crawl_status == "success"
