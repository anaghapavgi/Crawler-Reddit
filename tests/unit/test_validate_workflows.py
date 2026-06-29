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
