# Testing Strategy (Pre-Implementation)

## 1. Quality gates (global)

The following commands are mandatory before completion:

```bash
ruff format --check .
ruff check .
mypy src
pytest --cov=src/reddit_intelligence --cov-report=term-missing
python scripts/smoke_test.py
```

Additional phase-local tests are run earlier as each subsystem is introduced.

## 2. Test pyramid and scope

- **Unit tests**: deterministic logic (config, cleaning, relevance, hash, scoring, budget).
- **Integration tests**: adapter boundaries and orchestration with mocks/fakes.
- **Workflow/static tests**: CI/pipeline YAML validity and command invocation sanity.
- **UI smoke tests**: import/render-level confidence for Streamlit pages.
- **Acceptance tests**: checklist-driven verification across end-to-end flows.

Coverage target: at least 80% for non-UI core modules, with justified gaps.

## 3. Phase-by-phase tests and acceptance mapping

### Phase 0 - Scaffold and tooling

- Tests to write:
  - project import smoke;
  - CLI `--help` smoke;
  - placeholder unit test.
- Commands:
  - `ruff format --check .`
  - `ruff check .`
  - `mypy src`
  - `pytest -q`
- Acceptance criteria:
  - quality gates pass and scaffolded CLI is executable.
- Failure points:
  - package discovery/import path errors, linter rule conflicts.

### Phase 1 - Config/models/database

- Tests to write:
  - settings validation (required/optional and demo/live mode behavior);
  - YAML schema validation for research/taxonomy;
  - migration smoke checks (syntax/static assertions);
  - repository upsert idempotency and merge behavior.
- Commands:
  - `python -m reddit_intelligence.cli verify-env`
  - `python -m reddit_intelligence.cli init-db` (safe mode/demo-safe checks)
  - quality gates.
- Acceptance criteria:
  - invalid config errors are actionable; core schema/repository tests pass.
- Failure points:
  - env precedence mistakes, schema mismatches, poor error messages.

### Phase 2 - Reddit collection

- Tests to write:
  - submission/comment mapper fixtures;
  - deleted/removed detection;
  - comment cap and `replace_more` bounded behavior;
  - retry logic for transient vs permanent failures;
  - duplicate crawl idempotency.
- Commands:
  - `python -m reddit_intelligence.cli crawl --mode incremental` (fixtures/demo)
  - optional live crawl only when credentials exist.
- Acceptance criteria:
  - re-runs do not duplicate rows; rate-limit metadata captured.
- Failure points:
  - unbounded API expansion, missing error classification, stale data merge bugs.

### Phase 3 - AI analysis

- Tests to write:
  - strict schema validation and malformed response handling;
  - prompt-injection resistance fixtures;
  - taxonomy label constraint enforcement;
  - unchanged hash skip behavior;
  - budget and per-run cap enforcement;
  - VADER baseline mapping tests.
- Commands:
  - `python -m reddit_intelligence.cli analyze --limit 100` (mocked/demo-first)
- Acceptance criteria:
  - safe, structured, bounded analysis with usage/cost metadata.
- Failure points:
  - schema drift, partial batch retry loops, budget accounting errors.

### Phase 4 - Analytics and views

- Tests to write:
  - deterministic metric outputs against fixtures;
  - emergence-score zero-baseline handling;
  - deleted-content exclusion;
  - evidence diversity/non-duplication.
- Commands:
  - `python -m reddit_intelligence.cli aggregate`
  - quality gates.
- Acceptance criteria:
  - formulas match documentation and are robust to sparse datasets.
- Failure points:
  - divide-by-zero, grouping/timestamp bucket mistakes.

### Phase 5 - Dashboard

- Tests to write:
  - import/smoke tests for all pages;
  - filter persistence/combination logic;
  - empty-state and single-record handling;
  - CSV sanitization (no deleted text/user fields);
  - assistant evidence-bound responses via mocked provider.
- Commands:
  - Streamlit launch command and smoke checks.
- Acceptance criteria:
  - all pages render and react correctly in demo mode.
- Failure points:
  - session-state bugs, export leakage, chart failures for edge cases.

### Phase 6 - Automation and deployment

- Tests to write:
  - workflow syntax/static validation;
  - command smoke tests for CI/pipeline/maintenance commands;
  - timeout/concurrency presence checks.
- Commands:
  - run quality gates in CI-equivalent environment.
- Acceptance criteria:
  - workflows are valid, dispatchable, and non-overlapping.
- Failure points:
  - YAML schema errors, missing secret mappings, failing setup steps.

### Phase 7 - Compliance and final QA

- Tests to write:
  - deletion propagation/invalidation end-to-end;
  - secret hygiene checks in tracked files;
  - full smoke test over demo path;
  - final acceptance checklist walk-through.
- Commands:
  - full required command set plus manual acceptance verifications.
- Acceptance criteria:
  - all checklist items satisfied, with explicit live-vs-mocked evidence.
- Failure points:
  - hidden secret leaks, incomplete deletion cleanup, unverified live integrations.

## 4. Test data strategy

- Keep deterministic JSON/CSV fixtures under `tests/fixtures/` and `data/fixtures/`.
- Include prompt-injection and malformed-structure samples.
- Include deleted/removed content samples and near-duplicate text variants.
- Include both high-confidence and low-confidence cases for analytics and assistant evaluation.

## 5. Live verification policy

- Live external checks are optional during build until credentials are available.
- Any unverified integration must be explicitly documented as unverified.
- Never claim live Reddit/Supabase/AI success based only on mocked tests.
