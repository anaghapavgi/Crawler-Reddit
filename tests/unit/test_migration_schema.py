from __future__ import annotations

from pathlib import Path


def test_initial_migration_contains_required_tables_and_views() -> None:
    sql = Path("migrations/001_initial_schema.sql").read_text(encoding="utf-8")

    required_tables = (
        "create table if not exists crawl_runs",
        "create table if not exists reddit_posts",
        "create table if not exists reddit_comments",
        "create table if not exists analysis_runs",
        "create table if not exists content_analysis",
        "create table if not exists deletion_events",
        "create table if not exists pipeline_failures",
    )
    required_views = (
        "create or replace view v_analysed_content",
        "create or replace view v_daily_sentiment",
        "create or replace view v_theme_summary",
        "create or replace view v_feature_summary",
        "create or replace view v_segment_summary",
        "create or replace view v_pipeline_health",
        "create or replace view v_emerging_themes",
    )

    lower_sql = sql.lower()
    for stmt in (*required_tables, *required_views):
        assert stmt in lower_sql
