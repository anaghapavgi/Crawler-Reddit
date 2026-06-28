"""Demo seed entrypoint."""

from __future__ import annotations

from pathlib import Path

import typer

from reddit_intelligence.demo.seeding import write_demo_artifacts


def main(
    days: int = 90,
    seed: int = 42,
    output_dir: Path = Path("data/demo"),
) -> None:
    """Generate deterministic demo files."""
    result = write_demo_artifacts(output_dir=output_dir, days=days, seed=seed)
    typer.echo(
        "Demo seed complete: "
        f"records={result.record_count}, runs={result.run_count}, "
        f"dataset={result.records_path}"
    )


if __name__ == "__main__":
    typer.run(main)
