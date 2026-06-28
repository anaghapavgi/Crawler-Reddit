"""Repository smoke test scaffold."""

from __future__ import annotations

import typer

from reddit_intelligence.demo.seeding import write_demo_artifacts
from reddit_intelligence.pipeline import run_demo_pipeline


def main() -> None:
    """Run basic smoke checks for scaffold."""
    summary = run_demo_pipeline()
    seed_result = write_demo_artifacts()
    typer.echo(
        "Smoke test "
        f"status={summary.status} message={summary.message} "
        f"records={seed_result.record_count} runs={seed_result.run_count}"
    )


if __name__ == "__main__":
    main()
