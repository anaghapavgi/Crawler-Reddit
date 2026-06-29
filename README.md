# Reddit Product Intelligence

AI-powered Reddit review discovery and analytics application focused on product intelligence.

## Current status

Phases 0-4 are implemented in demo mode, and Phase 6 workflow hardening is in progress. The
repository now includes:
- Python package configuration (`pyproject.toml`)
- lint/type/test tooling setup plus CI workflow validation
- CLI commands for crawl/analyze/aggregate/retry and demo seeding
- project rule file under `.cursor/rules`
- planning, architecture, deployment, and troubleshooting documentation

See `BUILD_STATUS.md` for the authoritative phase tracker and command evidence.

## Quick start (demo-first)

### Option A: pip + venv

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
python -m pip install -e ".[dev]"
```

### Option B: uv

```bash
uv sync --all-extras
```

## Basic commands

```bash
python -m reddit_intelligence.cli --help
ruff format --check .
ruff check .
mypy src
pytest
python scripts/smoke_test.py
```

## Environment setup

1. Copy `.env.example` to `.env`.
2. Keep `DEMO_MODE=true` for local development until demo path is fully working.
3. Do not commit `.env` or any secret.

## Manual setup

Credential and deployment steps are documented in:
- `MANUAL_SETUP_CHECKLIST.md`
- `docs/manual-setup.md`

## Workflow runbook quick commands

Use these for manual GitHub workflow dispatch via `gh` CLI.

```bash
# Demo mode (safe default)
gh workflow run pipeline.yml -f demo_mode=true -f crawl_days=30 -f analyze_limit=100
gh workflow run daily-maintenance.yml -f demo_mode=true

# Live mode (requires configured repository secrets)
gh workflow run pipeline.yml -f demo_mode=false -f crawl_days=30 -f analyze_limit=100
gh workflow run daily-maintenance.yml -f demo_mode=false
```

See `docs/deployment.md` for the full mode/secret matrix and operational guidance.
