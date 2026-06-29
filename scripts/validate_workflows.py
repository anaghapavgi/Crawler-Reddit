"""Static validation checks for GitHub Actions workflow files."""

from __future__ import annotations

from pathlib import Path

import yaml

WORKFLOW_FILES: tuple[str, ...] = (
    ".github/workflows/ci.yml",
    ".github/workflows/pipeline.yml",
    ".github/workflows/daily-maintenance.yml",
)


def _mapping(value: object) -> dict[object, object] | None:
    if isinstance(value, dict):
        return value
    return None


def _get_mapping_key(mapping: dict[object, object], key: str) -> object | None:
    """Read YAML mapping keys while handling YAML 1.1 bool coercion for 'on'."""
    if key in mapping:
        return mapping[key]
    if key == "on" and True in mapping:
        return mapping[True]
    return None


def load_workflow_yaml(path: Path) -> dict[object, object]:
    """Load workflow YAML into a mapping."""
    with path.open("r", encoding="utf-8") as handle:
        payload = yaml.safe_load(handle)
    parsed = _mapping(payload)
    if parsed is None:
        msg = f"{path}: expected top-level mapping"
        raise ValueError(msg)
    return parsed


def validate_workflow_payload(name: str, payload: dict[object, object]) -> list[str]:
    """Validate expected workflow structure and policy controls."""
    errors: list[str] = []

    display_name = _get_mapping_key(payload, "name")
    if not isinstance(display_name, str) or not display_name.strip():
        errors.append(f"{name}: missing non-empty workflow name")

    on_section = _mapping(_get_mapping_key(payload, "on"))
    if on_section is None:
        errors.append(f"{name}: missing 'on' mapping")

    jobs = _mapping(_get_mapping_key(payload, "jobs"))
    if jobs is None or not jobs:
        errors.append(f"{name}: missing jobs mapping")

    concurrency = _mapping(_get_mapping_key(payload, "concurrency"))
    if concurrency is None:
        errors.append(f"{name}: missing concurrency mapping")
    else:
        if "group" not in concurrency:
            errors.append(f"{name}: concurrency.group is required")
        if "cancel-in-progress" not in concurrency:
            errors.append(f"{name}: concurrency.cancel-in-progress is required")

    if name == "ci.yml" and isinstance(jobs, dict):
        quality_job = _mapping(jobs.get("quality-gates"))
        if quality_job is None:
            errors.append("ci.yml: quality-gates job is required")
        else:
            steps = quality_job.get("steps")
            if not isinstance(steps, list):
                errors.append("ci.yml: quality-gates.steps must be a list")
            elif not any(
                isinstance(step, dict)
                and isinstance(step.get("run"), str)
                and "scripts/validate_workflows.py" in step["run"]
                for step in steps
            ):
                errors.append("ci.yml: must run scripts/validate_workflows.py in CI")

    if name in {"pipeline.yml", "daily-maintenance.yml"} and isinstance(on_section, dict):
        dispatch = _mapping(on_section.get("workflow_dispatch"))
        if dispatch is None:
            errors.append(f"{name}: workflow_dispatch mapping is required")
        else:
            inputs = _mapping(dispatch.get("inputs"))
            if inputs is None:
                errors.append(f"{name}: workflow_dispatch.inputs mapping is required")
            else:
                demo_mode = _mapping(inputs.get("demo_mode"))
                if demo_mode is None:
                    errors.append(f"{name}: demo_mode dispatch input is required")
                else:
                    default_value = demo_mode.get("default")
                    if default_value != "true":
                        errors.append(f"{name}: demo_mode default must be 'true'")
                    options = demo_mode.get("options")
                    if not isinstance(options, list) or {"true", "false"} - {
                        str(item) for item in options
                    }:
                        errors.append(f"{name}: demo_mode options must include 'true' and 'false'")

    return errors


def validate_repository_workflows(repo_root: Path) -> list[str]:
    """Validate all required workflow files in repository root."""
    errors: list[str] = []
    for relative in WORKFLOW_FILES:
        workflow_path = repo_root / relative
        if not workflow_path.exists():
            errors.append(f"{relative}: file not found")
            continue
        try:
            payload = load_workflow_yaml(workflow_path)
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{relative}: failed to parse YAML ({exc})")
            continue
        errors.extend(validate_workflow_payload(Path(relative).name, payload))
    return errors


def main() -> int:
    """CLI entrypoint for workflow validation checks."""
    repo_root = Path(__file__).resolve().parents[1]
    errors = validate_repository_workflows(repo_root)
    if errors:
        print("Workflow validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Workflow validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
