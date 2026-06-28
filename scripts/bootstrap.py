"""Local bootstrap helper."""

from __future__ import annotations

import typer


def main() -> None:
    """Print bootstrap guidance."""
    typer.echo("Bootstrap scaffold complete. Install dependencies and run verify-env.")


if __name__ == "__main__":
    main()
