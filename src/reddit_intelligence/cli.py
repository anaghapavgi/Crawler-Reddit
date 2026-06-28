"""Typer CLI entry point."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from reddit_intelligence.config import (
    RelevanceResearch,
    load_research_config,
    load_settings,
    load_taxonomy_config,
    missing_required_env_vars,
)
from reddit_intelligence.db.repositories import InMemoryContentRepository, InMemoryRunRepository
from reddit_intelligence.demo.seeding import write_demo_artifacts
from reddit_intelligence.logging_config import configure_logging
from reddit_intelligence.pipeline import run_demo_pipeline
from reddit_intelligence.processing.relevance import RelevanceScorer
from reddit_intelligence.reddit.client import create_reddit_client
from reddit_intelligence.reddit.collector import RedditCollector
from reddit_intelligence.reddit.deletion_sync import sync_deleted_content

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
def seed_demo(
    days: Annotated[int, typer.Option(min=90)] = 90,
    seed: Annotated[int, typer.Option()] = 42,
    output_dir: Annotated[Path, typer.Option()] = Path("data/demo"),
) -> None:
    """Generate deterministic demo fixtures for local dashboard runs."""
    try:
        result = write_demo_artifacts(output_dir=output_dir, days=days, seed=seed)
    except Exception as exc:
        typer.echo(f"Demo seed failed: {exc}")
        raise typer.Exit(code=1) from exc
    typer.echo(
        "Demo seed complete: "
        f"records={result.record_count}, runs={result.run_count}, days={result.days}, "
        f"dataset={result.records_path}, run_history={result.runs_path}, "
        f"metrics={result.metrics_path}"
    )


@app.command("crawl")
def crawl(mode: str = "incremental", days: int = 30) -> None:
    """Run collector scaffold."""
    try:
        settings = load_settings()
        research = load_research_config()
        repository = InMemoryContentRepository()
        run_repository = InMemoryRunRepository()
        relevance = RelevanceScorer(
            config=RelevanceResearch.model_validate(research.relevance.model_dump()),
            feature_terms=load_taxonomy_config().features,
        )
        collector = RedditCollector(
            repository=repository,
            relevance_scorer=relevance,
            max_comments_per_post=research.reddit.max_comments_per_post,
            minimum_post_score=research.reddit.minimum_post_score,
            run_repository=run_repository,
        )

        if settings.demo_mode:
            metrics = collector.collect_from_fixture(
                posts_path=Path("data/fixtures/reddit_posts.json"),
                comments_path=Path("data/fixtures/reddit_comments.json"),
                matched_query=f"demo-{mode}-{days}",
            )
            deletion_sync = sync_deleted_content(
                content_repository=repository,
                run_repository=run_repository,
                run_id=metrics.crawl_run_id,
            )
            typer.echo(
                "Demo crawl complete: "
                f"run_id={metrics.crawl_run_id}, "
                f"posts_seen={metrics.posts_seen}, comments_seen={metrics.comments_seen}, "
                f"posts_upserted={metrics.posts_upserted}, "
                f"comments_upserted={metrics.comments_upserted}, "
                f"queued_for_analysis={metrics.records_queued_for_analysis}, "
                f"deletion_events="
                f"{metrics.deletion_events_recorded + deletion_sync.events_recorded}"
            )
            return

        reddit_client = create_reddit_client(settings)
        if reddit_client is None:
            raise RuntimeError("Reddit client unavailable in live mode.")
        metrics = collector.collect_incremental(
            reddit_client=reddit_client, research=research.reddit
        )
        deletion_sync = sync_deleted_content(
            content_repository=repository,
            run_repository=run_repository,
            run_id=metrics.crawl_run_id,
        )
        typer.echo(
            "Live crawl complete: "
            f"run_id={metrics.crawl_run_id}, "
            f"posts_seen={metrics.posts_seen}, comments_seen={metrics.comments_seen}, "
            f"errors={metrics.errors_count}, rate_limit_remaining={metrics.rate_limit_remaining}, "
            f"deletion_events={metrics.deletion_events_recorded + deletion_sync.events_recorded}"
        )
    except Exception as exc:
        typer.echo(f"Crawl failed: {exc}")
        raise typer.Exit(code=1) from exc


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
