"""Environment verification helper."""

from __future__ import annotations

import typer

from reddit_intelligence.config import (
    load_research_config,
    load_settings,
    load_taxonomy_config,
    missing_required_env_vars,
)


def main() -> None:
    """Verify required environment for current mode."""
    settings = load_settings()
    research = load_research_config()
    taxonomy = load_taxonomy_config()
    missing = missing_required_env_vars(settings)
    typer.echo(
        "Environment OK. "
        f"demo_mode={settings.demo_mode} "
        f"subreddits={len(research.reddit.subreddits)} "
        f"themes={len(taxonomy.themes)} "
        f"missing_live_vars={len(missing)}"
    )


if __name__ == "__main__":
    main()
