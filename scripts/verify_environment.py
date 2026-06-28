"""Environment verification helper."""

from __future__ import annotations

import typer

from reddit_intelligence.config import load_settings


def main() -> None:
    """Verify required environment for current mode."""
    settings = load_settings()
    typer.echo(f"Environment OK. demo_mode={settings.demo_mode}")


if __name__ == "__main__":
    main()
