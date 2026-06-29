# Deployment Guide

## Scope

This repository currently supports:

- local/demo deployment for development validation
- GitHub Actions automation for CI quality gates
- scheduled and manually-dispatched pipeline/maintenance workflow runs

Live production deployment (credentialed Reddit + Supabase + OpenAI runs and hosted dashboard)
remains controlled by manual setup steps and secrets management.

## GitHub Actions workflows

### `ci.yml`

Runs on pushes to `main` and `cursor/**`, plus pull requests targeting `main`.

Quality gates:

1. `python scripts/validate_workflows.py`
2. `ruff format --check .`
3. `ruff check .`
4. `mypy src`
5. `pytest --cov=src/reddit_intelligence --cov-report=term-missing`
6. `python scripts/smoke_test.py`

Workflow validation currently checks file presence, core structure, concurrency controls,
timeout bounds, and critical step coverage for operational jobs.

### `pipeline.yml`

Purpose: run crawl/analyze/aggregate/retry stages.

- scheduled nightly (`15 2 * * *`)
- supports manual dispatch inputs:
  - `demo_mode` (`true` default)
  - `crawl_days` (`30` default)
  - `analyze_limit` (`100` default)
- includes per-branch concurrency and timeout bounds

### `daily-maintenance.yml`

Purpose: run deletion-sync and retry/aggregate maintenance flow.

- scheduled daily (`45 3 * * *`)
- supports manual dispatch input:
  - `demo_mode` (`true` default)
- includes per-branch concurrency and timeout bounds

## Demo mode and live mode behavior

Both operational workflows default to `demo_mode=true` to preserve safe, credential-free behavior.

If a workflow is manually dispatched with `demo_mode=false`, workflow guards enforce the
required secrets before runtime commands execute:

- `REDDIT_CLIENT_ID`
- `REDDIT_CLIENT_SECRET`
- `REDDIT_USER_AGENT`
- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`
- `OPENAI_API_KEY`
- `AI_MODEL`

Missing live-mode secrets fail fast with a clear error message.

## Secrets matrix by mode and command

| Command / Workflow Stage | Demo mode (`DEMO_MODE=true`) | Live mode (`DEMO_MODE=false`) |
|---|---|---|
| `python -m reddit_intelligence.cli verify-env` | No external secrets required; reports missing live secrets as expected | Requires Reddit + Supabase (+ OpenAI when `AI_PROVIDER=openai`) |
| `python -m reddit_intelligence.cli crawl` | Uses fixture data; no secrets required | Requires `REDDIT_CLIENT_ID`, `REDDIT_CLIENT_SECRET`, `REDDIT_USER_AGENT` |
| `python -m reddit_intelligence.cli analyze` | Uses deterministic demo provider; no secrets required | Requires `OPENAI_API_KEY`, `AI_MODEL` when OpenAI path enabled |
| `python -m reddit_intelligence.cli aggregate` | Uses demo CSV/in-memory state | Requires Supabase credentials for live SQL-view path |
| `pipeline.yml` manual dispatch | Default path (`demo_mode=true`) does not require live secrets | Guard requires all listed live secrets before execution |
| `daily-maintenance.yml` manual dispatch | Default path (`demo_mode=true`) does not require live secrets | Guard requires all listed live secrets before execution |

Live-mode secrets currently expected by workflow guards:

- `REDDIT_CLIENT_ID`
- `REDDIT_CLIENT_SECRET`
- `REDDIT_USER_AGENT`
- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`
- `OPENAI_API_KEY`
- `AI_MODEL`

## Operator runbook: manual dispatch examples

### Demo-mode dispatch (safe default)

Pipeline workflow:

1. GitHub UI -> Actions -> **Pipeline** -> **Run workflow**
2. Set:
   - `demo_mode=true`
   - optionally adjust `crawl_days` / `analyze_limit`
3. Run workflow.

Equivalent GitHub CLI example:

```bash
gh workflow run pipeline.yml -f demo_mode=true -f crawl_days=30 -f analyze_limit=100
```

Maintenance workflow:

```bash
gh workflow run daily-maintenance.yml -f demo_mode=true
```

### Live-mode dispatch (credentialed)

Before running:

1. Confirm all required repository secrets are present.
2. Ensure live credentials are valid and rotated according to policy.

Dispatch examples:

```bash
gh workflow run pipeline.yml -f demo_mode=false -f crawl_days=30 -f analyze_limit=100
gh workflow run daily-maintenance.yml -f demo_mode=false
```

If secrets are incomplete, workflow guard checks fail immediately with a missing-secrets list.

## Explorer CSV export verification

Explorer CSV export now includes formula-injection sanitization. Verify with:

1. Run dashboard with demo data:
   - `python3 -m reddit_intelligence.cli seed-demo`
   - `streamlit run src/reddit_intelligence/dashboard/app.py`
2. Open **Explorer** page and export CSV.
3. Confirm formula-like cells are prefixed with `'` in exported file, including values starting
   with:
   - `=`
   - `+`
   - `-`
   - `@`
   - tab/carriage-return prefixed values

## Phase 7 secret-hygiene verification checklist

Use this checklist for each live-mode run (`demo_mode=false`) and before enabling schedules.

### 1) Pre-run checks

1. Confirm secrets are configured only as repository/environment secrets, never in tracked files:
   - `REDDIT_CLIENT_ID`
   - `REDDIT_CLIENT_SECRET`
   - `REDDIT_USER_AGENT`
   - `SUPABASE_URL`
   - `SUPABASE_SERVICE_ROLE_KEY`
   - `OPENAI_API_KEY`
   - `AI_MODEL`
2. Confirm `.env` is local-only and not tracked by git.
3. Confirm `demo_mode=true` remains default for manual dispatch forms.

### 2) In-run log review (GitHub Actions)

After each run, inspect job logs and verify:

1. No secret values are echoed (including partial or base64-encoded forms).
2. Failure output lists only secret **names**, not values.
3. `verify-env` output does not print credential values.
4. Command invocations do not include inline secrets.

Recommended checks:

- Review logs in Actions UI for pipeline/maintenance jobs.
- Search logs for suspicious key markers (`BEGIN PRIVATE`, `sk-`, `service_role`, `token=`).

### 3) Post-run artifact review

1. Confirm uploaded artifacts do not include `.env`, secret dumps, or raw credential snapshots.
2. Confirm exported CSV/content artifacts contain only sanitized user-facing fields.
3. Confirm no debug bundle includes process environment dumps.

### 4) Rotation and incident response trigger

Immediately rotate affected credentials and follow `docs/troubleshooting.md` incident steps if:

- any plaintext credential appears in logs/artifacts;
- a misconfigured run executed with secrets in command arguments; or
- a debug artifact accidentally includes environment variables.
