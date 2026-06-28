# BUILD_STATUS

Last updated: 2026-06-28 (UTC)  
Branch: `cursor/full-build-plan-32d4`  
Mode: Phase 0/1/2 completed; Phase 3 in progress  
Authoritative spec: `MASTER_BUILD_PROMPT.md`  
Persistent rules checked: `AGENTS.md`, `reddit-intelligence.mdc` (and `.cursor` check)

## Current overall status

- Repository state: planning docs plus Phase 0 scaffold created (`src/`, `tests/`, `config/`, `data/`, `scripts/`, toolchain files).
- Current phase: **Phase 3 - AI analysis**
- Current phase status: **in_progress**
- Acceptance gate for current phase:
  - strict schema validation for malformed model payloads ✅
  - prompt-injection fixture tests enforce non-instruction-following prompt boundaries ✅
  - budget guard halts analysis when caps are reached ✅
  - taxonomy-safe coercion + deterministic demo provider path verified ✅
  - analysis outputs persisted through repository adapters with idempotent dedup keys ✅
  - analysis run metadata + retry queue scaffolding wired into CLI flow ✅
- Immediate blockers: none for demo-mode progress.
- Required operating mode: keep `DEMO_MODE=true` until full local demo path is working.

---

## Phase tracker (master specification phases)

| Phase | Name | Status | Acceptance Gate | External Dependencies | Blockers |
|---|---|---|---|---|---|
| 0 | Plan and scaffold | completed | Tooling install works; `ruff`/`mypy`/placeholder tests pass; CLI help works | None (demo-first) | None |
| 1 | Config, models, database | completed | Config validation, migration review, repository tests, demo seed success | Supabase optional for live path | None |
| 2 | Reddit collection | completed | Fixture crawler tests, idempotency, rate-limit capture, live verification only if creds exist | Reddit credentials for live verification | Live verification awaiting credentials |
| 3 | AI analysis | in_progress | Structured output validation, injection resistance, unchanged skip logic, budget stop behavior | AI provider credentials for live verification | Live OpenAI verification awaiting credentials |
| 4 | Analytics and views | pending | Metric fixtures match expected values; zero-volume/deleted exclusion behavior | None for demo; DB needed for live SQL execution | None |
| 5 | Dashboard | pending | All pages render in demo mode; filters, export, empty states, browser verification | Streamlit runtime; optional live DB | None |
| 6 | Scheduling and deployment | pending | Workflow YAML valid; dispatch/concurrency/timeouts/schedules correct | GitHub repo settings/secrets; Streamlit Cloud setup | Awaiting manual platform setup |
| 7 | Compliance, hardening, final QA | pending | Full checks pass; secret hygiene; clean demo launch; DoD checklist complete | Credentials required for live end-to-end verification | Awaiting credentials and platform access |

---

## Phase-by-phase implementation plan summary

### Phase 0 - Plan and scaffold
- Deliverables:
  - Project skeleton per spec, package config, toolchain (`ruff`, `mypy`, `pytest`), `.gitignore`, CLI skeleton, docs scaffold, demo-mode skeleton.
- Files to create/modify:
  - `pyproject.toml`, `Makefile`, `.gitignore`, `.pre-commit-config.yaml`, `README.md`, `BUILD_STATUS.md`, `src/...`, `tests/...`, `docs/...`, `.streamlit/config.toml`.
- Dependencies:
  - Python 3.11/3.12, package manager (`uv` and pip-compatible install path).
- Commands to run:
  - `uv sync` (or pip equivalent), `ruff format --check .`, `ruff check .`, `mypy src`, `pytest -q`.
- Tests to write:
  - CLI import/help smoke, skeleton unit test, environment bootstrap sanity test.
- Acceptance criteria:
  - Local install and quality gates pass; CLI launches.
- Possible failure points:
  - Dependency resolution conflicts; import path misconfiguration; type-check baseline failures.

### Phase 1 - Configuration, models, and database
- Deliverables:
  - Pydantic settings and env validation, YAML loaders, domain schemas, Supabase adapter, SQL migration, repository layer, demo repository/seed.
- Files to create/modify:
  - `src/reddit_intelligence/config.py`, `models.py`, `db/client.py`, `db/repositories.py`, `migrations/001_initial_schema.sql`, `config/research.yml`, `config/taxonomy.yml`, `scripts/seed_demo.py`.
- Dependencies:
  - `pydantic`, `pydantic-settings`, `PyYAML`, `supabase`, PostgreSQL SQL compatibility.
- Commands to run:
  - `python -m reddit_intelligence.cli verify-env`, `python -m reddit_intelligence.cli init-db` (demo/local validation), lint/type/test suite.
- Tests to write:
  - Settings validation matrix; taxonomy/research schema tests; upsert idempotency payload tests; migration static checks.
- Acceptance criteria:
  - Invalid config fails clearly; migration is reviewable and consistent with required schema/views; demo seed path succeeds without credentials.
- Possible failure points:
  - Env fallback precedence bugs; schema drift; RLS/view syntax issues.

### Phase 2 - Reddit collection
- Deliverables:
  - Read-only PRAW client, collector, mapper, cleaning/relevance/hash pipeline, incremental refresh, crawl run logging, retry/rate-limit handling, deletion detection.
- Files to create/modify:
  - `src/reddit_intelligence/reddit/client.py`, `collector.py`, `mapper.py`, `processing/cleaning.py`, `processing/relevance.py`, `processing/deduplication.py`, pipeline orchestration modules.
- Dependencies:
  - `praw`, `tenacity`, network timeouts/retries, repository upsert interfaces.
- Commands to run:
  - `python -m reddit_intelligence.cli crawl --mode incremental` (demo fixtures first), test commands.
- Tests to write:
  - Fixture mapping tests; idempotent re-run tests; retry classification tests; rate-limit metadata persistence tests.
- Acceptance criteria:
  - No duplicate inserts on re-run; capped comments; robust transient error handling; live verification only when credentials supplied.
- Possible failure points:
  - API pagination assumptions; unsafe `replace_more`; private/banned subreddit handling; stale-state transitions.

### Phase 3 - AI analysis
- Deliverables:
  - Provider abstraction, OpenAI-compatible structured output adapter, strict schemas, prompt templates, batch execution, VADER baseline, budget guard, token/cost accounting, failure queue.
- Files to create/modify:
  - `src/reddit_intelligence/ai/*.py`, `processing/sentiment_baseline.py`, analysis orchestration and DB persistence modules.
- Dependencies:
  - `openai`, `vaderSentiment`, pricing config, taxonomy definitions, analysis tables.
- Commands to run:
  - `python -m reddit_intelligence.cli analyze --limit 100` (demo/mocked first), full quality gate commands.
- Tests to write:
  - Schema validation and malformed response retries; prompt-injection fixtures; unchanged hash skip logic; budget cap stop behavior.
- Acceptance criteria:
  - Strict validated outputs; budget/cap enforcement; no instruction-following from Reddit text; traceable usage metadata.
- Possible failure points:
  - Provider schema mismatch; retry storms; over-budget estimation errors; taxonomy label leakage.

### Phase 4 - Analytics and views
- Deliverables:
  - SQL aggregate views, Python metrics/trends, emerging-theme scoring, priority scoring, evidence sampling, data-quality checks.
- Files to create/modify:
  - `migrations/001_initial_schema.sql` (views/indexes), `src/reddit_intelligence/analytics/*.py`, `db/queries.py`, docs metrics definitions.
- Dependencies:
  - Completed analysis schema, cleaned/deleted filtering rules.
- Commands to run:
  - `python -m reddit_intelligence.cli aggregate`, test suite with deterministic fixtures.
- Tests to write:
  - Formula parity tests; zero-baseline emergence tests; deleted exclusion tests; evidence dedup/diversity tests.
- Acceptance criteria:
  - Metrics match documented formulas and handle sparse data safely.
- Possible failure points:
  - Division-by-zero; inconsistent date bucketing; deleted rows leaking into aggregates.

### Phase 5 - Dashboard
- Deliverables:
  - Multi-page Streamlit app (9 pages), global filters/state, Plotly visuals, explorer export, assistant with evidence-bound responses, pipeline health page.
- Files to create/modify:
  - `src/reddit_intelligence/dashboard/*.py`, `pages/*.py`, `.streamlit/config.toml`, UI docs.
- Dependencies:
  - Stable analytics/query layer and demo dataset.
- Commands to run:
  - `python -m reddit_intelligence.cli dashboard` (or Streamlit entry command), UI smoke tests.
- Tests to write:
  - Page import/render smoke tests, filter logic tests, CSV sanitization tests, assistant evidence-bounded behavior tests.
- Acceptance criteria:
  - All pages render in demo mode, filters are correct, no crashes on empty states, near-live labeling accurate.
- Possible failure points:
  - State synchronization bugs, heavy queries, inconsistent KPI denominator logic.

### Phase 6 - Scheduling and deployment
- Deliverables:
  - GitHub Actions CI, pipeline, maintenance workflows; deployment docs; secret setup instructions; timeout/concurrency protections.
- Files to create/modify:
  - `.github/workflows/ci.yml`, `pipeline.yml`, `daily-maintenance.yml`, `docs/deployment.md`, `docs/troubleshooting.md`.
- Dependencies:
  - CLI commands stable, test suite stable, secret names finalized.
- Commands to run:
  - Local workflow lint/validation where possible; quality/test commands; smoke pipeline command.
- Tests to write:
  - Workflow static validation checks; command-level smoke tests for scheduled jobs.
- Acceptance criteria:
  - Workflows support manual dispatch, off-hour schedules, concurrency control, and clear failure semantics.
- Possible failure points:
  - YAML syntax/regression, missing secrets mapping, schedule overlap, runaway job duration.

### Phase 7 - Compliance, hardening, final QA
- Deliverables:
  - Deletion reconciliation end-to-end, compliance docs, security hardening notes, dependency audit, verification report, final QA pass.
- Files to create/modify:
  - `src/reddit_intelligence/reddit/deletion_sync.py`, `docs/privacy-and-compliance.md`, `docs/verification-report.md`, final README updates, smoke script.
- Dependencies:
  - All prior phases complete; credentialed systems for live verification steps.
- Commands to run:
  - Full required gate:
    - `ruff format --check .`
    - `ruff check .`
    - `mypy src`
    - `pytest --cov=src/reddit_intelligence --cov-report=term-missing`
    - `python scripts/smoke_test.py`
- Tests to write:
  - Deletion propagation tests; secret-hygiene checks; full integration smoke tests.
- Acceptance criteria:
  - Acceptance checklist fully satisfied with explicit live-vs-mocked evidence.
- Possible failure points:
  - Undetected secret leakage, incomplete deletion invalidation, incomplete live verification artifacts.

---

## Demo-mode vs credential-required boundaries

Integrations and features that can be completed in demo mode (no external credentials):
- Project structure, CLI, config validation, taxonomy/research loaders.
- Domain models, repository interfaces, idempotency logic tests.
- Synthetic data seeding and full dashboard rendering.
- AI pipeline with mocked provider responses and VADER baseline.
- SQL definition authoring/static validation and analytics logic tests.
- Workflow authoring and static checks.

Integrations requiring manual setup/credentials for live verification:
- Reddit OAuth/PRAW live read checks.
- Supabase database connectivity and real migration application.
- OpenAI-compatible provider live structured-output analysis.
- GitHub Actions secret-backed scheduled runs.
- Streamlit Community Cloud deployment with server-side secrets.

---

## Manual setup dependencies (do not request now)

- Reddit app credentials and compliant user agent.
- Supabase project URL and service role key.
- AI provider API key and model selection.
- GitHub repository secrets configuration.
- Streamlit Community Cloud app/secrets configuration.

All are deferred until demo-mode path is complete and validated locally.

---

## Commands run and results (planning + Phase 0/1)

| Command | Result |
|---|---|
| `pwd && ls && git rev-parse --is-inside-work-tree && git branch --show-current && git status --short --branch` | Repo confirmed, on `main`, clean status at inspection time |
| `ls -a` | Verified top-level files including `.env.example`, `.git`, prompt docs |
| `git checkout -b cursor/full-build-plan-32d4` | Created/switched to planning branch |
| File inspections via tooling (`README_START_HERE.md`, `MASTER_BUILD_PROMPT.md`, `AGENTS.md`, `PHASE_PROMPTS.md`, `MANUAL_SETUP_CHECKLIST.md`, `ACCEPTANCE_CHECKLIST.md`, `OFFICIAL_REFERENCES.md`, `.env.example`, `README.md`, `reddit-intelligence.mdc`) | Completed |
| `.cursor` directory presence check | `.cursor` is currently missing |
| Tree and directory glob checks (`src`, `tests`, `docs`, `config`, `.github`) | No implementation directories currently present |
| `python3 --version && python3 -m pip --version` | Python 3.12.3 detected |
| `python3 -m pip install -e ".[dev]"` (first attempt) | Failed due missing Hatch wheel package mapping in `pyproject.toml` |
| Added `[tool.hatch.build.targets.wheel] packages = ["src/reddit_intelligence"]` | Packaging fix applied |
| `python3 -m pip install -e ".[dev]"` (second attempt) | Succeeded |
| `python3 -m ruff format --check .` (first run) | Failed: `cli.py` required formatting |
| `python3 -m ruff format .` | Applied formatting |
| `python3 -m ruff check .` (first run after format) | Failed: `pipeline.py` `timezone.utc` lint (`UP017`) |
| Updated `pipeline.py` to use `datetime.UTC` | Lint fix applied |
| `python3 -m ruff format --check . && python3 -m ruff check . && python3 -m mypy src && python3 -m pytest -q && python3 -m reddit_intelligence.cli --help` | All checks passed; 2 tests passed; CLI help displayed expected commands |
| `python3 scripts/smoke_test.py` | Passed (`status=success`) |
| Implemented Phase 1 core artifacts (`config.py`, `models.py`, `db/*`, migration SQL, tests) | Completed |
| `python3 -m ruff format . && python3 -m ruff format --check . && python3 -m ruff check . && python3 -m mypy src && python3 -m pytest -q && python3 -m reddit_intelligence.cli verify-env` (first run) | Failed tests due Streamlit secrets lookup exception when no secrets file exists |
| Updated `_load_streamlit_secrets()` to safely return empty mapping when no Streamlit secrets are configured | Fix applied |
| `python3 -m ruff format --check . && python3 -m ruff check . && python3 -m mypy src && python3 -m pytest -q && python3 -m reddit_intelligence.cli verify-env` (second run) | All checks passed; 9 tests passed; verify-env succeeded |
| `python3 scripts/smoke_test.py` | Passed (`status=success`) |
| Added `.cursor/environment.json` and `.cursor/Dockerfile` to pre-provision Cloud Agent Python 3.12 + editable dev install | Completed |
| `python3 -m json.tool .cursor/environment.json >/dev/null && python3 -m ruff format --check . && python3 -m ruff check . && python3 -m mypy src && python3 -m pytest -q` | Passed (env config valid JSON; quality gates green) |
| Implemented deterministic demo seeding module and CLI/script wiring (`src/reddit_intelligence/demo/seeding.py`) | Completed |
| `python3 -m reddit_intelligence.cli seed-demo` | Passed; generated `data/demo/demo_dataset.csv` (1552 records), `data/demo/demo_run_history.csv` (180 runs), and `data/demo/demo_cost_metrics.json` |
| `python3 -m ruff format --check . && python3 -m ruff check . && python3 -m mypy src && python3 -m pytest --cov=src/reddit_intelligence --cov-report=term-missing && python3 scripts/smoke_test.py` (first run) | Failed format check (`seeding.py`, `test_demo_seeding.py`) |
| `python3 -m ruff format .` | Applied formatting fixes |
| `python3 -m ruff format --check . && python3 -m ruff check . && python3 -m mypy src && python3 -m pytest --cov=src/reddit_intelligence --cov-report=term-missing && python3 scripts/smoke_test.py` (second run) | Passed; 12 tests, total coverage 85%, smoke test passed |
| Implemented Phase 2 modules (`reddit/client.py`, `reddit/mapper.py`, `reddit/collector.py`, `processing/*`) and fixture-based crawl wiring | Completed |
| `python3 -m ruff format --check . && python3 -m ruff check . && python3 -m mypy src && python3 -m pytest --cov=src/reddit_intelligence --cov-report=term-missing && python3 scripts/smoke_test.py` (first run after Phase 2 edits) | Failed format check (`cli.py`, `reddit/__init__.py`, `reddit/collector.py`) |
| `python3 -m ruff format .` | Applied formatting fixes |
| `python3 -m ruff format --check . && python3 -m ruff check . && python3 -m mypy src && python3 -m pytest --cov=src/reddit_intelligence --cov-report=term-missing && python3 scripts/smoke_test.py` (second run after Phase 2 edits) | Failed lint line-length in `cli.py` |
| Updated `cli.py` output formatting for lint compliance | Fix applied |
| `python3 -m ruff format --check . && python3 -m ruff check . && python3 -m mypy src && python3 -m pytest --cov=src/reddit_intelligence --cov-report=term-missing && python3 scripts/smoke_test.py` (third run after Phase 2 edits) | Passed; 24 tests, total coverage 83%, smoke test passed |
| Added crawl-run persistence hooks (`InMemoryRunRepository`), deletion-sync integration module, and expanded error classification coverage | Completed |
| `python3 -m ruff format --check . && python3 -m ruff check . && python3 -m mypy src && python3 -m pytest --cov=src/reddit_intelligence --cov-report=term-missing && python3 scripts/smoke_test.py` (first run after hook updates) | Failed format check (`test_reddit_collector_errors.py`) |
| `python3 -m ruff format .` | Applied formatting fix |
| `python3 -m ruff check . --fix` | Applied import-order fixes; line-length issue remained in `cli.py` |
| Updated `cli.py` crawl output string wrapping for lint compliance | Fix applied |
| Updated `db/repositories.py` metric parsing helpers (`_as_int`, `_as_float`) to satisfy MyPy strict typing | Fix applied |
| `python3 -m ruff format --check . && python3 -m ruff check . && python3 -m mypy src && python3 -m pytest --cov=src/reddit_intelligence --cov-report=term-missing && python3 scripts/smoke_test.py` (second run after hook updates) | Passed; 31 tests, total coverage 83%, smoke test passed |
| Implemented Phase 3 AI foundations (`src/reddit_intelligence/ai/*`, `processing/sentiment_baseline.py`, `cli analyze` wiring) with deterministic demo provider + budget guard | Completed |
| Added Phase 3 fixtures/tests (`tests/fixtures/ai_malformed_response.json`, `tests/fixtures/prompt_injection_input.txt`, `tests/unit/test_ai_*`, `tests/unit/test_sentiment_baseline.py`) | Completed |
| Updated `docs/verification-report.md` with explicit `AWAITING_CREDENTIALS` status for live OAuth/DB/OpenAI checks while keeping demo path default | Completed |
| `python3 -m ruff format --check . && python3 -m ruff check . && python3 -m mypy src && python3 -m pytest --cov=src/reddit_intelligence --cov-report=term-missing && python3 scripts/smoke_test.py` (after Phase 3 edits) | Passed; 44 tests, total coverage 81%, smoke test passed |
| Implemented Phase 3 persistence continuation (`models.py`, `db/repositories.py`, `cli.py`) for `analysis_runs`, `content_analysis` adapters, and `pipeline_failures` retry queue | Completed |
| Added/updated tests for analysis persistence and retry queue behavior (`test_repositories.py`, `test_run_repository.py`, `test_cli.py`) | Completed |
| `python3 -m ruff format --check . && python3 -m ruff check . && python3 -m mypy src && python3 -m pytest --cov=src/reddit_intelligence --cov-report=term-missing && python3 scripts/smoke_test.py` (after persistence continuation) | Passed; 49 tests, total coverage 86%, smoke test passed |

---

## Files changed in this branch so far

- `BUILD_STATUS.md` (created)
- `docs/architecture.md` (created)
- `docs/data-flow.md` (created)
- `docs/manual-setup.md` (created)
- `docs/testing-strategy.md` (created)
- `.cursor/rules/reddit-intelligence.mdc` (created)
- `.streamlit/config.toml` (created)
- `.gitignore` (created)
- `.pre-commit-config.yaml` (created)
- `pyproject.toml` (created)
- `Makefile` (created)
- `README.md` (updated)
- `CHANGELOG.md` (created)
- `LICENSE` (created)
- `config/research.yml` (created)
- `config/taxonomy.yml` (created)
- `migrations/001_initial_schema.sql` (placeholder scaffold created)
- `scripts/bootstrap.py` (created)
- `scripts/seed_demo.py` (created)
- `scripts/verify_environment.py` (created)
- `scripts/smoke_test.py` (created)
- `src/reddit_intelligence/__init__.py` (created)
- `src/reddit_intelligence/cli.py` (created)
- `src/reddit_intelligence/config.py` (created)
- `src/reddit_intelligence/logging_config.py` (created)
- `src/reddit_intelligence/models.py` (created)
- `src/reddit_intelligence/pipeline.py` (created)
- `src/reddit_intelligence/reddit/__init__.py` (created)
- `src/reddit_intelligence/processing/__init__.py` (created)
- `src/reddit_intelligence/ai/__init__.py` (created)
- `src/reddit_intelligence/db/__init__.py` (created)
- `src/reddit_intelligence/analytics/__init__.py` (created)
- `src/reddit_intelligence/dashboard/__init__.py` (created)
- `src/reddit_intelligence/dashboard/app.py` (created)
- `src/reddit_intelligence/dashboard/pages/__init__.py` (created)
- `tests/conftest.py` (created)
- `tests/unit/test_cli.py` (created)
- `tests/unit/test_pipeline.py` (created)
- `tests/integration/.gitkeep` (created)
- `tests/fixtures/.gitkeep` (created)
- `data/fixtures/reddit_posts.json` (created)
- `data/fixtures/reddit_comments.json` (created)
- `data/fixtures/ai_results.json` (created)
- `data/demo/demo_dataset.csv` (created)
- `docs/database.md` (created)
- `docs/deployment.md` (created)
- `docs/privacy-and-compliance.md` (created)
- `docs/dashboard-metrics.md` (created)
- `docs/troubleshooting.md` (created)
- `docs/verification-report.md` (created)
- `src/reddit_intelligence/config.py` (updated with validated settings + YAML loaders + Streamlit fallback)
- `src/reddit_intelligence/models.py` (updated with normalized post/comment/analysis models)
- `src/reddit_intelligence/cli.py` (updated `verify-env` and `init-db` behavior)
- `src/reddit_intelligence/db/client.py` (created)
- `src/reddit_intelligence/db/repositories.py` (created)
- `src/reddit_intelligence/db/queries.py` (created)
- `src/reddit_intelligence/db/__init__.py` (updated exports)
- `scripts/verify_environment.py` (updated with config/taxonomy verification)
- `migrations/001_initial_schema.sql` (replaced placeholder with full schema/indexes/views)
- `tests/unit/test_config.py` (created)
- `tests/unit/test_repositories.py` (created)
- `tests/unit/test_migration_schema.py` (created)
- `.cursor/environment.json` (created; Cloud Agent repo-level env config)
- `.cursor/Dockerfile` (created; Python 3.12 base image + core OS deps)
- `src/reddit_intelligence/demo/__init__.py` (created)
- `src/reddit_intelligence/demo/seeding.py` (created)
- `src/reddit_intelligence/cli.py` (updated with deterministic `seed-demo` command)
- `scripts/seed_demo.py` (updated to generate deterministic artifacts)
- `scripts/smoke_test.py` (updated to validate demo artifact generation)
- `tests/unit/test_demo_seeding.py` (created)
- `data/demo/demo_dataset.csv` (updated with deterministic 90-day dataset)
- `data/demo/demo_run_history.csv` (created)
- `data/demo/demo_cost_metrics.json` (created)
- `src/reddit_intelligence/processing/cleaning.py` (created)
- `src/reddit_intelligence/processing/deduplication.py` (created)
- `src/reddit_intelligence/processing/relevance.py` (created)
- `src/reddit_intelligence/processing/__init__.py` (updated exports)
- `src/reddit_intelligence/reddit/client.py` (created)
- `src/reddit_intelligence/reddit/mapper.py` (created)
- `src/reddit_intelligence/reddit/collector.py` (created)
- `src/reddit_intelligence/reddit/__init__.py` (updated exports)
- `src/reddit_intelligence/cli.py` (updated `crawl` to run fixture/live paths)
- `src/reddit_intelligence/db/repositories.py` (updated count helpers)
- `data/fixtures/reddit_posts.json` (updated with deterministic crawl fixtures)
- `data/fixtures/reddit_comments.json` (updated with deterministic crawl fixtures)
- `tests/unit/test_cleaning.py` (created)
- `tests/unit/test_deduplication.py` (created)
- `tests/unit/test_relevance.py` (created)
- `tests/unit/test_reddit_mapper.py` (created)
- `tests/integration/test_reddit_collector.py` (created)
- `src/reddit_intelligence/reddit/deletion_sync.py` (created)
- `src/reddit_intelligence/models.py` (updated with `CrawlRunRecord`, `DeletionEvent`, run status types)
- `src/reddit_intelligence/db/repositories.py` (updated with run repository protocol/in-memory implementation and typed metric parsing)
- `src/reddit_intelligence/db/__init__.py` (updated exports for run repository classes)
- `src/reddit_intelligence/reddit/collector.py` (updated run hooks, deletion event recording, expanded error categorization)
- `src/reddit_intelligence/reddit/__init__.py` (updated exports for deletion sync)
- `src/reddit_intelligence/cli.py` (updated crawl flow with run repository + deletion sync integration)
- `tests/unit/test_run_repository.py` (created)
- `tests/unit/test_reddit_collector_errors.py` (created)
- `tests/unit/test_deletion_sync.py` (created)
- `tests/integration/test_reddit_collector.py` (updated for run persistence/deletion sync assertions)
- `tests/unit/test_repositories.py` (updated iterator/count helper coverage)
- `src/reddit_intelligence/ai/budget.py` (created)
- `src/reddit_intelligence/ai/classifier.py` (created)
- `src/reddit_intelligence/ai/openai_provider.py` (created)
- `src/reddit_intelligence/ai/prompts.py` (created)
- `src/reddit_intelligence/ai/provider.py` (created)
- `src/reddit_intelligence/ai/schemas.py` (created)
- `src/reddit_intelligence/ai/__init__.py` (updated exports)
- `src/reddit_intelligence/processing/sentiment_baseline.py` (created)
- `src/reddit_intelligence/processing/__init__.py` (updated exports)
- `src/reddit_intelligence/cli.py` (updated analyze command for demo-safe Phase 3 flow)
- `tests/fixtures/ai_malformed_response.json` (created)
- `tests/fixtures/prompt_injection_input.txt` (created)
- `tests/unit/test_ai_budget.py` (created)
- `tests/unit/test_ai_classifier.py` (created)
- `tests/unit/test_ai_prompts.py` (created)
- `tests/unit/test_ai_schemas.py` (created)
- `tests/unit/test_sentiment_baseline.py` (created)
- `docs/verification-report.md` (updated with live verification status markers)
- `src/reddit_intelligence/models.py` (updated with `AnalysisRunRecord`, `PipelineFailureRecord`, and failure/run status types)
- `src/reddit_intelligence/db/repositories.py` (updated with analysis persistence + retry queue protocols/in-memory methods)
- `src/reddit_intelligence/db/__init__.py` (updated exports for analysis run repository protocol)
- `src/reddit_intelligence/cli.py` (updated analyze persistence hooks and retry-failures queue processing)
- `tests/unit/test_repositories.py` (updated with analysis result idempotency coverage)
- `tests/unit/test_run_repository.py` (updated with analysis run + retry queue lifecycle coverage)
- `tests/unit/test_cli.py` (updated analyze/retry command behavior coverage)

---

## Next action

1. Begin Phase 4 analytics aggregation modules against SQL views (`v_daily_sentiment`, `v_theme_summary`, `v_feature_summary`, `v_segment_summary`, `v_pipeline_health`, `v_emerging_themes`).
2. Implement deterministic analytics computation helpers for dashboard KPIs and trend deltas with deleted-content exclusion guarantees.
3. Add Phase 4 unit tests for formula parity, sparse-data handling, and emerging-theme zero-baseline behavior.
