"""Database client adapters."""

from __future__ import annotations

from supabase import Client, create_client

from reddit_intelligence.config import Settings


def get_supabase_client(settings: Settings) -> Client | None:
    """Create a Supabase client when credentials are available."""
    if not settings.supabase_url or not settings.supabase_service_role_key:
        if settings.demo_mode:
            return None
        msg = "Supabase credentials are required when DEMO_MODE=false."
        raise RuntimeError(msg)
    return create_client(settings.supabase_url, settings.supabase_service_role_key)
