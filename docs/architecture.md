# Architecture Plan (Pre-Implementation)

## 1. Planning context

This document is a planning artifact derived from:
- `MASTER_BUILD_PROMPT.md` (authoritative specification)
- `AGENTS.md` and `reddit-intelligence.mdc` (persistent implementation rules)
- `ACCEPTANCE_CHECKLIST.md` and `MANUAL_SETUP_CHECKLIST.md` (completion and setup constraints)

No production implementation code changes are made in this step.

## 2. Current repository state

- Present: prompt/specification files and environment template.
- Missing (to be built): application source, tests, config YAML, migrations, GitHub workflows, Streamlit app, and operational scripts.
- `.cursor` directory is currently absent and will be created to host persistent project rules.

## 3. Target architecture (logical)

```text
CLI / GitHub Actions triggers
            |
            v
Reddit Collector (PRAW read-only, OAuth)
            |
            v
Cleaning + Relevance + Dedup/Hashing
            |
            v
Supabase/PostgreSQL (raw + run logs)
            |
            v
AI Analyzer (structured output + budget guard + VADER baseline)
            |
            v
Analysis tables + SQL views + analytics service
            |
            v
Streamlit multipage dashboard + Plotly + evidence-bounded assistant
```

## 4. Design constraints enforced across all phases

1. No Reddit HTML scraping; official API only via read-only PRAW.
2. No username storage and no sensitive trait inference.
3. Deleted/removed content must be excluded from downstream views, exports, and evidence.
4. AI outputs must pass strict Pydantic validation.
5. Idempotency via Reddit IDs, content hashes, and upserts.
6. Budget and volume caps must stop AI safely when exceeded.
7. Demo mode must work end-to-end without external credentials.
8. Dashboard never calls Reddit directly.

## 5. Repository dependency order

The build proceeds in this dependency order:

1. **Foundation**: project packaging, lint/type/test, settings skeleton, CLI scaffold.
2. **Configuration and data contracts**: Pydantic settings, YAML config, domain models.
3. **Persistence layer**: migration schema, DB client/repositories, idempotent upserts.
4. **Collection pipeline**: Reddit client, mapping, processing, crawl logging.
5. **AI pipeline**: baseline sentiment, provider abstraction, structured analysis, budget guard.
6. **Analytics layer**: SQL views + Python metrics/trends/evidence samplers.
7. **Dashboard/UI layer**: pages, charts, explorer, assistant, pipeline health.
8. **Automation/deployment**: CI and scheduled workflows.
9. **Hardening/final QA**: deletion sync, compliance docs, full verification.

## 6. Phase implementation plan (detailed)

### Phase 0 - Plan and scaffold

- Deliverables:
  - Complete repo skeleton, packaging/tooling, initial docs, and CLI skeleton.
- Files to create/modify:
  - `.cursor/rules/reddit-intelligence.mdc`
  - `pyproject.toml`, `.gitignore`, `Makefile`, `.pre-commit-config.yaml`
  - `src/reddit_intelligence/{__init__.py,cli.py,logging_config.py}`
  - `tests/{unit,integration,fixtures}/`, `tests/conftest.py`
  - `docs/` baseline docs and `BUILD_STATUS.md`
- Dependencies:
  - Python toolchain and package manager.
- Commands:
  - `uv sync` (or pip equivalent)
  - `ruff format --check .`
  - `ruff check .`
  - `mypy src`
  - `pytest -q`
- Tests to write:
  - CLI invocation/help smoke and placeholder sanity tests.
- Acceptance criteria:
  - Toolchain and quality gates pass with scaffold.
- Possible failure points:
  - Packaging/import path issues, default mypy strictness noise, misconfigured test discovery.

### Phase 1 - Configuration, models, and database

- Deliverables:
  - Validated settings, research/taxonomy loaders, domain models, migration, repositories, demo seed repository.
- Files to create/modify:
  - `config/research.yml`, `config/taxonomy.yml`
  - `src/reddit_intelligence/config.py`, `models.py`
  - `src/reddit_intelligence/db/{client.py,repositories.py,queries.py}`
  - `migrations/001_initial_schema.sql`
  - `scripts/{verify_environment.py,seed_demo.py,bootstrap.py}`
- Dependencies:
  - Phase 0 scaffolding and dependency install.
- Commands:
  - `python -m reddit_intelligence.cli verify-env`
  - `python -m reddit_intelligence.cli init-db`
  - quality gates.
- Tests to write:
  - env/config validation matrix; taxonomy validation; upsert payload/idempotency tests.
- Acceptance criteria:
  - invalid config errors are actionable; migration and repositories align with schema requirements.
- Possible failure points:
  - schema mismatch between SQL and Python models; env fallback edge cases.

### Phase 2 - Reddit collection

- Deliverables:
  - OAuth read-only PRAW client, collector, mapper, cleaner/relevance/hash flow, incremental refresh, run logging, retry handling.
- Files to create/modify:
  - `src/reddit_intelligence/reddit/{client.py,collector.py,mapper.py}`
  - `src/reddit_intelligence/processing/{cleaning.py,relevance.py,deduplication.py}`
  - `src/reddit_intelligence/pipeline.py`
- Dependencies:
  - Phase 1 settings/models/repository interfaces.
- Commands:
  - `python -m reddit_intelligence.cli crawl --mode incremental`
  - `python -m reddit_intelligence.cli crawl --mode backfill --days 30`
- Tests to write:
  - fixture-based collector tests; duplicate-run idempotency; transient/permanent error classification.
- Acceptance criteria:
  - repeat crawl is idempotent; rate-limit metadata captured; comment caps enforced.
- Possible failure points:
  - unbounded comment expansion, bad retry policy, stale hash state handling.

### Phase 3 - AI analysis

- Deliverables:
  - AI provider protocol, OpenAI adapter, strict schemas/prompts, batching/retries, VADER baseline, budget guard and cost tracking.
- Files to create/modify:
  - `src/reddit_intelligence/ai/{provider.py,openai_provider.py,schemas.py,prompts.py,classifier.py,summarizer.py,budget.py}`
  - `src/reddit_intelligence/processing/sentiment_baseline.py`
- Dependencies:
  - Phase 1 schema/storage and Phase 2 cleaned content outputs.
- Commands:
  - `python -m reddit_intelligence.cli analyze --limit 100`
- Tests to write:
  - schema validation and malformed response retries; prompt-injection fixtures; budget stop tests; unchanged hash skip tests.
- Acceptance criteria:
  - strict validated outputs and safe budget enforcement.
- Possible failure points:
  - provider structured-output drift; partial batch retry bugs; cost accounting inconsistencies.

### Phase 4 - Analytics and SQL views

- Deliverables:
  - aggregate views and deterministic metric/trend/evidence services.
- Files to create/modify:
  - `migrations/001_initial_schema.sql` (view definitions)
  - `src/reddit_intelligence/analytics/{metrics.py,trends.py,aggregates.py}`
  - `src/reddit_intelligence/db/queries.py`
- Dependencies:
  - analyzed data availability and deletion handling.
- Commands:
  - `python -m reddit_intelligence.cli aggregate`
- Tests to write:
  - formula tests, emergence zero-baseline tests, deleted-content exclusion tests.
- Acceptance criteria:
  - outputs match documented formulas and safety constraints.
- Possible failure points:
  - divide-by-zero, duplicate evidence, timezone/date bucketing errors.

### Phase 5 - Streamlit dashboard

- Deliverables:
  - multipage app (overview, sentiment, pain points, features, segments, trends, explorer, assistant, pipeline health).
- Files to create/modify:
  - `src/reddit_intelligence/dashboard/{app.py,data_access.py,filters.py,components.py,theme.py}`
  - `src/reddit_intelligence/dashboard/pages/*.py`
  - `.streamlit/config.toml`
- Dependencies:
  - Phase 4 analytics queries and demo seed data.
- Commands:
  - `python -m reddit_intelligence.cli dashboard`
- Tests to write:
  - page import smoke tests, filter behavior tests, CSV sanitization tests, assistant evidence-bound tests.
- Acceptance criteria:
  - all pages render in demo mode; empty states handled; filters/charts synchronized.
- Possible failure points:
  - state inconsistency across pages, slow queries, unsanitized export fields.

### Phase 6 - Scheduling and deployment

- Deliverables:
  - CI workflow, scheduled pipeline workflow, daily maintenance workflow, deployment docs.
- Files to create/modify:
  - `.github/workflows/{ci.yml,pipeline.yml,daily-maintenance.yml}`
  - `docs/{deployment.md,troubleshooting.md}`
- Dependencies:
  - stable CLI commands and tests.
- Commands:
  - run quality gates and any local workflow lints/smoke checks.
- Tests to write:
  - workflow static checks and command smoke tests.
- Acceptance criteria:
  - schedules avoid top-of-hour, have concurrency/timeouts, and support manual dispatch.
- Possible failure points:
  - bad secret wiring, overlap of runs, fragile workflow steps.

### Phase 7 - Compliance, hardening, final QA

- Deliverables:
  - deletion sync and downstream invalidation, privacy/security docs, final verification report, complete quality gate pass.
- Files to create/modify:
  - `src/reddit_intelligence/reddit/deletion_sync.py`
  - `docs/{privacy-and-compliance.md,verification-report.md,dashboard-metrics.md}`
  - final README and smoke test scripts.
- Dependencies:
  - all previous phases complete.
- Commands:
  - `ruff format --check .`
  - `ruff check .`
  - `mypy src`
  - `pytest --cov=src/reddit_intelligence --cov-report=term-missing`
  - `python scripts/smoke_test.py`
- Tests to write:
  - deletion propagation/invalidation, end-to-end smoke paths, secret hygiene checks.
- Acceptance criteria:
  - acceptance checklist satisfied with explicit mocked vs live verification evidence.
- Possible failure points:
  - latent secret leakage, partial deletion handling, gaps between docs and actual behavior.

## 7. Demo-mode-ready vs credential-required components

### Fully completable in demo mode

- CLI, configuration, validation, and schema logic.
- Processing, hashing, relevance, and baseline sentiment.
- AI schema/prompt/budget behavior using mocks/fixtures.
- Analytics and dashboard behavior with synthetic seeded data.
- Local tests and static quality gates.
- Workflow authoring and static validation.

### Requires manual setup for live verification

- Reddit OAuth live crawling.
- Supabase live migrations and storage validation.
- AI provider live call behavior and usage billing accuracy.
- GitHub Actions secrets-backed scheduled execution.
- Streamlit Community Cloud deployment checks.

## 8. Manual setup checkpoints (deferred)

No credentials requested in this planning stage. Live verification gates remain blocked by:
- Reddit app credentials and user agent.
- Supabase URL/service role key.
- AI provider API key + model.
- GitHub secrets.
- Streamlit deployment secrets.
