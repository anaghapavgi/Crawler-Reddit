"""Repository smoke test scaffold."""

from __future__ import annotations

import typer

from reddit_intelligence.pipeline import run_demo_pipeline


def main() -> None:
    """Run basic smoke checks for scaffold."""
    summary = run_demo_pipeline()
    typer.echo(f"Smoke test status={summary.status} message={summary.message}")


if __name__ == "__main__":
    main()
