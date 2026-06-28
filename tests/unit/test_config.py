from __future__ import annotations

from pathlib import Path

import pytest

from reddit_intelligence.config import (
    load_research_config,
    load_settings,
    load_taxonomy_config,
)


def _clear_live_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for key in (
        "REDDIT_CLIENT_ID",
        "REDDIT_CLIENT_SECRET",
        "REDDIT_USER_AGENT",
        "SUPABASE_URL",
        "SUPABASE_SERVICE_ROLE_KEY",
        "OPENAI_API_KEY",
        "AI_MODEL",
    ):
        monkeypatch.delenv(key, raising=False)


def test_load_settings_allows_missing_live_credentials_in_demo_mode(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _clear_live_env(monkeypatch)
    monkeypatch.setenv("DEMO_MODE", "true")
    settings = load_settings()
    assert settings.demo_mode is True


def test_load_settings_fails_fast_when_live_mode_missing_credentials(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _clear_live_env(monkeypatch)
    monkeypatch.setenv("DEMO_MODE", "false")
    with pytest.raises(RuntimeError, match="Missing required environment variables"):
        load_settings()


def test_load_research_and_taxonomy_configs_from_defaults() -> None:
    research = load_research_config()
    taxonomy = load_taxonomy_config()
    assert research.project.product_name == "Spotify"
    assert "repetitive_recommendations" in taxonomy.themes


def test_taxonomy_rejects_duplicate_values(tmp_path: Path) -> None:
    taxonomy_file = tmp_path / "taxonomy.yml"
    taxonomy_file.write_text(
        "themes:\n"
        "  - one\n"
        "  - one\n"
        "features:\n"
        "  - a\n"
        "behavioral_segments:\n"
        "  - s\n"
        "journey_stages:\n"
        "  - j\n"
        "emotions:\n"
        "  - e\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError):
        load_taxonomy_config(taxonomy_file)
