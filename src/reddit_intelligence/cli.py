"""Typer CLI entry point."""

from __future__ import annotations

from pathlib import Path

import typer

from reddit_intelligence.config import (
    load_research_config,
    load_settings,
    load_taxonomy_config,
    missing_required_env_vars,
)
from reddit_intelligence.logging_config import configure_logging
from reddit_intelligence.pipeline import run_demo_pipeline

app = typer.Typer(add_completion=False, no_args_is_help=True)


@app.callback()
def main() -> None:
    """Initialize CLI context."""
    settings = load_settings()
    configure_logging(settings.log_level)


@app.command("verify-env")
def verify_env() -> None:
    """Validate environment bootstrap."""
    try:
        settings = load_settings()
        research = load_research_config()
        taxonomy = load_taxonomy_config()
    except Exception as exc:
        typer.echo(f"Environment verification failed: {exc}")
        raise typer.Exit(code=1) from exc

    if settings.demo_mode:
        missing = missing_required_env_vars(settings)
        if missing:
            missing_csv = ", ".join(missing)
            typer.echo(f"Demo mode active; live credentials missing (expected): {missing_csv}")

    typer.echo(
        "Environment verified: "
        f"APP_ENV={settings.app_env}, DEMO_MODE={settings.demo_mode}, "
        f"subreddits={len(research.reddit.subreddits)}, themes={len(taxonomy.themes)}"
    )


@app.command("init-db")
def init_db() -> None:
    """Prepare database scaffold."""
    migration_path = Path("migrations/001_initial_schema.sql")
    if not migration_path.exists():
        typer.echo(f"Migration not found: {migration_path}")
        raise typer.Exit(code=1)
    typer.echo(f"Database initialization scaffold complete. Migration: {migration_path}")


@app.command("seed-demo")
def seed_demo() -> None:
    """Seed deterministic demo fixture scaffold."""
    typer.echo("Demo seed scaffold complete.")


@app.command("crawl")
def crawl(mode: str = "incremental", days: int = 30) -> None:
    """Run collector scaffold."""
    typer.echo(f"Crawl scaffold invoked with mode={mode}, days={days}.")


@app.command("analyze")
def analyze(limit: int = 100) -> None:
    """Run analysis scaffold."""
    typer.echo(f"Analyze scaffold invoked with limit={limit}.")


@app.command("aggregate")
def aggregate() -> None:
    """Run analytics aggregation scaffold."""
    typer.echo("Aggregate scaffold complete.")


@app.command("sync-deletions")
def sync_deletions(days: int = 14) -> None:
    """Run deletion sync scaffold."""
    typer.echo(f"Deletion sync scaffold invoked with days={days}.")


@app.command("retry-failures")
def retry_failures(stage: str = "analysis") -> None:
    """Retry failed work items scaffold."""
    typer.echo(f"Retry failures scaffold invoked for stage={stage}.")


@app.command("run-pipeline")
def run_pipeline() -> None:
    """Run end-to-end scaffold pipeline."""
    summary = run_demo_pipeline()
    typer.echo(f"Pipeline {summary.status}: {summary.message}")


@app.command("dashboard")
def dashboard() -> None:
    """Launch dashboard scaffold info."""
    app_path = Path("src/reddit_intelligence/dashboard/app.py")
    typer.echo(f"Dashboard scaffold entrypoint: {app_path}")


def run() -> None:
    """Project script entrypoint."""
    app()


if __name__ == "__main__":
    run()
