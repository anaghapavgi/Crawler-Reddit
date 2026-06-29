# Verification Report

## Phase 6 verification snapshot (demo-first)

Status: **PASSING in demo mode**

Evidence summary:

- CI quality gates include workflow static validation (`python scripts/validate_workflows.py`).
- Workflow guardrails are in place:
  - dispatch `demo_mode` defaults to `true`
  - live-mode runs (`demo_mode=false`) fail fast when required secrets are missing
- Workflow validation currently checks:
  - required workflow files and top-level structure
  - concurrency controls
  - timeout bounds for critical jobs
  - required operational step names
  - `Setup Python` consistency (`python-version: 3.12`) across validated jobs
- Explorer CSV export sanitization behavior is documented and test-covered.

Local validation commands last executed:

1. `python3 scripts/validate_workflows.py`
2. `python3 -m pytest tests/unit/test_validate_workflows.py -q`
3. `python3 -m ruff format --check .`
4. `python3 -m ruff check .`
5. `python3 -m mypy src`
6. `python3 -m pytest --cov=src/reddit_intelligence --cov-report=term-missing`
7. `python3 scripts/smoke_test.py`

## Phase 7 hardening evidence scaffold

The following evidence blocks are planned for completion during Phase 7:

- compliance checks (data minimization, deletion propagation, and export safety)
- secret hygiene checks for local and CI logs/artifacts
- final demo-vs-live verification matrix with explicit credential boundaries
- final acceptance checklist traceability to tests, commands, and artifacts

## Live integration verification status

- Reddit OAuth + PRAW live verification: **AWAITING_CREDENTIALS**
- Supabase live connectivity verification: **AWAITING_CREDENTIALS**
- OpenAI live structured-output verification: **AWAITING_CREDENTIALS**

## Demo-mode verification status

- Default runtime mode remains `DEMO_MODE=true`.
- Demo fixture crawl path is exercised and tested.
- Deterministic seeded dataset generation is exercised and tested.
- AI Phase 3 foundation path currently runs through deterministic provider in demo mode.
