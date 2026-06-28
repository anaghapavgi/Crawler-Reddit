from __future__ import annotations

from typer.testing import CliRunner

from reddit_intelligence.cli import app


def test_cli_help_displays_commands() -> None:
    runner = CliRunner()
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "verify-env" in result.stdout
    assert "run-pipeline" in result.stdout


def test_analyze_command_reports_run_metadata() -> None:
    runner = CliRunner()
    result = runner.invoke(app, ["analyze", "5"])
    assert result.exit_code == 0
    assert "Analyze complete:" in result.stdout
    assert "run_id=" in result.stdout
    assert "persisted=" in result.stdout


def test_retry_failures_command_runs() -> None:
    runner = CliRunner()
    result = runner.invoke(app, ["retry-failures", "analysis", "5"])
    assert result.exit_code == 0
    assert "Retry failures complete:" in result.stdout
