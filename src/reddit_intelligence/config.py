"""Application settings and YAML configuration loaders."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class ProjectResearch(BaseModel):
    """Top-level project metadata for the research target."""

    name: str
    product_name: str
    timezone: str


class RedditResearch(BaseModel):
    """Crawler search strategy configuration."""

    subreddits: list[str]
    search_queries: list[str]
    time_filter: str
    sort: str
    posts_per_query: int = Field(ge=1)
    max_comments_per_post: int = Field(ge=0)
    minimum_post_score: int
    refresh_active_posts_days: int = Field(ge=1)


class RelevanceResearch(BaseModel):
    """Rule-based relevance threshold and keyword controls."""

    minimum_text_length: int = Field(ge=1)
    minimum_rule_score: int
    include_terms: list[str]
    exclude_terms: list[str]


class AIResearch(BaseModel):
    """Pipeline-level AI controls from research config."""

    enabled: bool = True
    batch_size: int = Field(ge=1)
    max_records_per_run: int = Field(ge=1)
    min_relevance_score: int
    min_text_length: int = Field(ge=1)
    prompt_version: str


class DashboardResearch(BaseModel):
    """Dashboard runtime defaults."""

    cache_ttl_seconds: int = Field(ge=1)
    default_days: int = Field(ge=1)
    show_ai_assistant: bool = True


class ResearchConfig(BaseModel):
    """Research config file model."""

    project: ProjectResearch
    reddit: RedditResearch
    relevance: RelevanceResearch
    ai: AIResearch
    dashboard: DashboardResearch


class TaxonomyConfig(BaseModel):
    """Taxonomy file model used by AI schema constraints."""

    themes: list[str]
    features: list[str]
    behavioral_segments: list[str]
    journey_stages: list[str]
    emotions: list[str]

    @field_validator(
        "themes", "features", "behavioral_segments", "journey_stages", "emotions", mode="after"
    )
    @classmethod
    def validate_unique_values(cls, value: list[str]) -> list[str]:
        """Require non-empty, unique labels in each taxonomy list."""
        stripped = [item.strip() for item in value if item.strip()]
        if not stripped:
            msg = "taxonomy categories must contain at least one value"
            raise ValueError(msg)
        if len(set(stripped)) != len(stripped):
            msg = "taxonomy categories must not contain duplicate values"
            raise ValueError(msg)
        return stripped


class Settings(BaseSettings):
    """Environment-backed application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True,
        populate_by_name=True,
    )

    app_env: str = Field(default="development", alias="APP_ENV")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    demo_mode: bool = Field(default=True, alias="DEMO_MODE")
    reddit_client_id: str | None = Field(default=None, alias="REDDIT_CLIENT_ID")
    reddit_client_secret: str | None = Field(default=None, alias="REDDIT_CLIENT_SECRET")
    reddit_user_agent: str | None = Field(default=None, alias="REDDIT_USER_AGENT")
    supabase_url: str | None = Field(default=None, alias="SUPABASE_URL")
    supabase_service_role_key: str | None = Field(default=None, alias="SUPABASE_SERVICE_ROLE_KEY")
    ai_provider: str = Field(default="openai", alias="AI_PROVIDER")
    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    ai_model: str | None = Field(default=None, alias="AI_MODEL")
    ai_temperature: float = Field(default=0, alias="AI_TEMPERATURE")
    ai_max_output_tokens: int = Field(default=1200, ge=1, alias="AI_MAX_OUTPUT_TOKENS")
    usd_inr_rate: float = Field(default=95, gt=0, alias="USD_INR_RATE")
    monthly_ai_budget_inr: float = Field(default=250, ge=0, alias="MONTHLY_AI_BUDGET_INR")
    max_ai_records_per_run: int = Field(default=250, ge=1, alias="MAX_AI_RECORDS_PER_RUN")
    max_ai_calls_per_run: int = Field(default=50, ge=1, alias="MAX_AI_CALLS_PER_RUN")
    dashboard_timezone: str = Field(default="Asia/Kolkata", alias="DASHBOARD_TIMEZONE")
    dashboard_cache_ttl_seconds: int = Field(default=60, ge=1, alias="DASHBOARD_CACHE_TTL_SECONDS")
    admin_password: str | None = Field(default=None, alias="ADMIN_PASSWORD")


FALLBACK_SECRET_KEYS: dict[str, str] = {
    "reddit_client_id": "REDDIT_CLIENT_ID",
    "reddit_client_secret": "REDDIT_CLIENT_SECRET",
    "reddit_user_agent": "REDDIT_USER_AGENT",
    "supabase_url": "SUPABASE_URL",
    "supabase_service_role_key": "SUPABASE_SERVICE_ROLE_KEY",
    "openai_api_key": "OPENAI_API_KEY",
    "ai_model": "AI_MODEL",
    "admin_password": "ADMIN_PASSWORD",
}


def _missing(value: object) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return value.strip() == ""
    return False


def _load_streamlit_secrets() -> dict[str, str]:
    """Read Streamlit secrets when available, otherwise return empty mapping."""
    try:
        import streamlit as st
    except Exception:
        return {}
    try:
        secrets_obj = st.secrets
    except Exception:
        return {}

    try:
        secrets_dict = dict(secrets_obj)
    except Exception:
        return {}

    values: dict[str, str] = {}
    for secret_key in FALLBACK_SECRET_KEYS.values():
        if secret_key in secrets_dict:
            values[secret_key] = str(secrets_dict[secret_key])
    return values


def missing_required_env_vars(settings: Settings) -> list[str]:
    """List required env vars missing for live mode."""
    required = [
        "REDDIT_CLIENT_ID",
        "REDDIT_CLIENT_SECRET",
        "REDDIT_USER_AGENT",
        "SUPABASE_URL",
        "SUPABASE_SERVICE_ROLE_KEY",
    ]
    if settings.ai_provider.lower() == "openai":
        required.extend(["OPENAI_API_KEY", "AI_MODEL"])

    current_values = {
        "REDDIT_CLIENT_ID": settings.reddit_client_id,
        "REDDIT_CLIENT_SECRET": settings.reddit_client_secret,
        "REDDIT_USER_AGENT": settings.reddit_user_agent,
        "SUPABASE_URL": settings.supabase_url,
        "SUPABASE_SERVICE_ROLE_KEY": settings.supabase_service_role_key,
        "OPENAI_API_KEY": settings.openai_api_key,
        "AI_MODEL": settings.ai_model,
    }
    return [name for name in required if _missing(current_values[name])]


def validate_runtime_settings(settings: Settings) -> None:
    """Enforce non-demo requirements without exposing secret values."""
    if settings.demo_mode:
        return

    missing = missing_required_env_vars(settings)
    if missing:
        missing_csv = ", ".join(missing)
        msg = f"Missing required environment variables for live mode: {missing_csv}"
        raise RuntimeError(msg)


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        msg = f"Configuration file not found: {path}"
        raise FileNotFoundError(msg)
    with path.open("r", encoding="utf-8") as config_file:
        raw = yaml.safe_load(config_file) or {}
    if not isinstance(raw, dict):
        msg = f"Configuration file must contain a mapping at top level: {path}"
        raise ValueError(msg)
    return raw


def load_research_config(path: Path = Path("config/research.yml")) -> ResearchConfig:
    """Load and validate research configuration file."""
    return ResearchConfig.model_validate(_load_yaml(path))


def load_taxonomy_config(path: Path = Path("config/taxonomy.yml")) -> TaxonomyConfig:
    """Load and validate taxonomy configuration file."""
    return TaxonomyConfig.model_validate(_load_yaml(path))


def load_settings() -> Settings:
    """Load settings with Streamlit secrets fallback and runtime validation."""
    settings = Settings()
    streamlit_secrets = _load_streamlit_secrets()

    updates: dict[str, str] = {}
    for field_name, env_name in FALLBACK_SECRET_KEYS.items():
        current = getattr(settings, field_name)
        if _missing(current) and env_name in streamlit_secrets:
            updates[field_name] = streamlit_secrets[env_name]

    if updates:
        settings = settings.model_copy(update=updates)

    validate_runtime_settings(settings)
    return settings
