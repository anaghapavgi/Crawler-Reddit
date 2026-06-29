from __future__ import annotations

from pathlib import Path

from scripts import validate_workflows


def test_repository_workflow_validation_passes_for_current_files() -> None:
    errors = validate_workflows.validate_repository_workflows(Path.cwd())
    assert errors == []


def test_pipeline_requires_demo_mode_defaults() -> None:
    payload: dict[object, object] = {
        "name": "Pipeline",
        "on": {"workflow_dispatch": {"inputs": {}}, "schedule": [{"cron": "0 0 * * *"}]},
        "concurrency": {"group": "pipeline-main", "cancel-in-progress": False},
        "jobs": {"run-pipeline": {"steps": []}},
    }
    errors = validate_workflows.validate_workflow_payload("pipeline.yml", payload)
    assert "pipeline.yml: demo_mode dispatch input is required" in errors


def test_pipeline_enforces_timeout_bounds() -> None:
    payload: dict[object, object] = {
        "name": "Pipeline",
        "on": {
            "workflow_dispatch": {
                "inputs": {
                    "demo_mode": {"default": "true", "options": ["true", "false"]},
                }
            }
        },
        "concurrency": {"group": "pipeline-main", "cancel-in-progress": False},
        "jobs": {
            "run-pipeline": {
                "timeout-minutes": 999,
                "steps": [
                    {"name": "Resolve runtime input defaults"},
                    {"name": "Validate live mode secret requirements"},
                    {"name": "Verify environment"},
                    {"name": "Run crawl stage"},
                    {"name": "Run analysis stage"},
                    {"name": "Run aggregate stage"},
                    {"name": "Process retry queue"},
                ],
            }
        },
    }
    errors = validate_workflows.validate_workflow_payload("pipeline.yml", payload)
    assert "pipeline.yml: job 'run-pipeline' timeout-minutes must be between 15 and 45" in errors


def test_daily_maintenance_requires_critical_steps() -> None:
    payload: dict[object, object] = {
        "name": "Daily Maintenance",
        "on": {
            "workflow_dispatch": {
                "inputs": {
                    "demo_mode": {"default": "true", "options": ["true", "false"]},
                }
            }
        },
        "concurrency": {"group": "daily-main", "cancel-in-progress": False},
        "jobs": {
            "maintenance": {
                "timeout-minutes": 20,
                "steps": [
                    {"name": "Resolve runtime input defaults"},
                    {"name": "Verify environment"},
                ],
            }
        },
    }
    errors = validate_workflows.validate_workflow_payload("daily-maintenance.yml", payload)
    assert (
        "daily-maintenance.yml: job 'maintenance' missing required step "
        "'Validate live mode secret requirements'"
    ) in errors


def test_ci_requires_setup_python_312() -> None:
    payload: dict[object, object] = {
        "name": "CI",
        "on": {"pull_request": {"branches": ["main"]}},
        "concurrency": {"group": "ci-main", "cancel-in-progress": True},
        "jobs": {
            "quality-gates": {
                "timeout-minutes": 25,
                "steps": [
                    {"name": "Checkout"},
                    {
                        "name": "Setup Python",
                        "uses": "actions/setup-python@v5",
                        "with": {"python-version": "3.11"},
                    },
                    {"name": "Install dependencies"},
                    {
                        "name": "Validate workflow definitions",
                        "run": "python scripts/validate_workflows.py",
                    },
                    {"name": "Ruff format check"},
                    {"name": "Ruff lint check"},
                    {"name": "MyPy type check"},
                    {"name": "Pytest with coverage"},
                    {"name": "Smoke test"},
                ],
            }
        },
    }
    errors = validate_workflows.validate_workflow_payload("ci.yml", payload)
    assert "ci.yml: job 'quality-gates' step 'Setup Python' python-version must be '3.12'" in errors
