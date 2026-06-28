from __future__ import annotations

from typer.testing import CliRunner

from reddit_intelligence.cli import app


def test_cli_help_displays_commands() -> None:
    runner = CliRunner()
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "verify-env" in result.stdout
    assert "run-pipeline" in result.stdout
