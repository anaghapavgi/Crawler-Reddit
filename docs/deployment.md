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

1. `ruff format --check .`
2. `ruff check .`
3. `mypy src`
4. `pytest --cov=src/reddit_intelligence --cov-report=term-missing`
5. `python scripts/smoke_test.py`

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
