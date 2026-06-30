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

Latest execution result:

- PASS: `76 passed`, total coverage `82%`, smoke test status `success`.

## Phase 7 hardening evidence scaffold

The following evidence blocks are completed/planned during Phase 7:

- compliance checks (data minimization, deletion propagation, and export safety)
- secret hygiene checks for local and CI logs/artifacts
- final demo-vs-live verification matrix with explicit credential boundaries
- final acceptance checklist traceability to tests, commands, and artifacts

## Phase 7 QA execution matrix (acceptance traceability)

This matrix links `ACCEPTANCE_CHECKLIST.md` items to concrete verification commands and
evidence sources. Live-only items remain marked **AWAITING_CREDENTIALS** until executed
with real credentials.

| Acceptance area | Checklist items | Verification command(s) / tests | Evidence source | Current status |
|---|---|---|---|---|
| Installation and configuration | Clean clone install; demo launch; invalid config failure | `python3 -m pip install -e ".[dev]"`; `python3 -m reddit_intelligence.cli verify-env`; `python3 scripts/smoke_test.py`; `python3 -m pytest tests/unit/test_config.py -q tests/unit/test_cli.py -q` | CLI output, smoke test output, unit tests | Demo validated |
| Installation and configuration | Secrets ignored by git and never logged | `python3 -m pytest tests/unit/test_dashboard_pages.py -q`; `python3 scripts/validate_workflows.py`; log/artifact checklist in `docs/deployment.md` | `.gitignore`, workflow guard steps, sanitizer tests, run logs | Demo validated; live log review pending |
| Reddit collection | OAuth client, search, mapping, comment cap, idempotency, active refresh, rate limits, retry behavior | `python3 -m pytest tests/unit/test_reddit_mapper.py -q tests/unit/test_relevance.py -q tests/unit/test_cleaning.py -q`; `python3 -m pytest tests/unit/test_reddit_collector_errors.py -q tests/integration/test_reddit_collector.py -q` | Unit/integration test reports | Demo validated; OAuth live check awaiting credentials |
| Privacy and deletion | No author storage; deleted text not retained; deletion sync and downstream exclusion | `python3 -m pytest tests/unit/test_deletion_sync.py -q tests/unit/test_repositories.py -q`; `python3 -m pytest tests/unit/test_dashboard_data_access.py -q tests/unit/test_dashboard_pages.py -q` | Tests and schema/repository behavior | Demo validated |
| AI analysis | VADER, structured schema, taxonomy constraints, injection safety, reanalysis logic, partial failures, token/cost, budget guard | `python3 -m pytest tests/unit/test_sentiment_baseline.py -q tests/unit/test_ai_schemas.py -q tests/unit/test_ai_prompts.py -q tests/unit/test_ai_budget.py -q tests/unit/test_ai_classifier.py -q` | AI unit test reports | Demo validated; live provider check awaiting credentials |
| Analytics | Formula parity, zero baseline, priority visibility, evidence diversity, low sample warnings | `python3 -m pytest tests/unit/test_analytics_aggregates.py -q tests/unit/test_analytics_trends.py -q tests/unit/test_analytics_data_access.py -q tests/unit/test_pipeline_health.py -q` | Analytics unit test reports, `docs/dashboard-metrics.md` | Demo validated |
| Dashboard | Nine pages render; filters; KPI parity; charts; empty states; freshness/demo-live labels; CSV sanitize; assistant evidence bounds; pipeline health | `python3 -m pytest tests/unit/test_dashboard_pages.py -q tests/unit/test_dashboard_data_access.py -q tests/unit/test_cli.py -q`; manual `streamlit run src/reddit_intelligence/dashboard/app.py` | Unit tests + manual page checks | Demo validated (manual cloud check awaiting deployment) |
| Automation and deployment | CI pass, manual dispatch, concurrency/timeouts, off-hour schedule, deletion maintenance, deployment instructions | `python3 scripts/validate_workflows.py`; `python3 -m pytest tests/unit/test_validate_workflows.py -q`; inspect `.github/workflows/*.yml` | Validator output, workflow tests, workflow files, deployment docs | Demo/static validated; live scheduled run awaiting credentials |
| Quality | Ruff format/lint, MyPy, Pytest, coverage >= 80, smoke test, live-vs-mocked separation, limitations | `python3 -m ruff format --check .`; `python3 -m ruff check .`; `python3 -m mypy src`; `python3 -m pytest --cov=src/reddit_intelligence --cov-report=term-missing`; `python3 scripts/smoke_test.py` | Command output, coverage summary, this report + docs | Validated per latest run |

## Cross-reference checklist coverage

- Primary acceptance criteria: `ACCEPTANCE_CHECKLIST.md`
- Manual setup dependency boundary: `docs/manual-setup.md` and `MANUAL_SETUP_CHECKLIST.md`
- Compliance controls: `docs/privacy-and-compliance.md`
- Deployment/runtime secret guard behavior: `docs/deployment.md`
- Failure handling and incident workflow: `docs/troubleshooting.md`

## Phase 7 DoD status summary (validated vs awaiting)

Status legend:

- `VALIDATED_DEMO`: verified in local/demo mode with passing tests and/or commands
- `AWAITING_CREDENTIALS`: requires live credentials/platform access not available in demo mode
- `AWAITING_MANUAL_UI`: requires interactive visual/browser verification

| Acceptance section | Current status | Notes |
|---|---|---|
| Installation and configuration | `VALIDATED_DEMO` | Demo bootstrap, env validation, and failure behavior covered by CLI/tests. |
| Reddit collection | `VALIDATED_DEMO` + `AWAITING_CREDENTIALS` | Fixture/integration behavior validated; live OAuth execution pending credentials. |
| Privacy and deletion | `VALIDATED_DEMO` | Deletion propagation and deleted-content exclusion are test-covered in repository and dashboard layers. |
| AI analysis | `VALIDATED_DEMO` + `AWAITING_CREDENTIALS` | Schema/prompt/budget behaviors validated in deterministic mode; live provider verification pending. |
| Analytics | `VALIDATED_DEMO` | Aggregate/trend/pipeline-health formulas validated against deterministic fixtures. |
| Dashboard | `VALIDATED_DEMO` + `AWAITING_MANUAL_UI` | Page/filter/export helpers are test-covered; interactive multi-viewport visual pass requires browser execution. |
| Automation and deployment | `VALIDATED_DEMO` + `AWAITING_CREDENTIALS` | Workflow policies are statically validated; live scheduled/secret-backed runs pending credentialed dispatch. |
| Quality | `VALIDATED_DEMO` | Ruff/MyPy/Pytest/coverage/smoke pass in latest local evidence run. |

## Manual dashboard verification evidence notes

Desktop and narrow-width manual verification target:

- desktop viewport: all pages render and filter interactions remain stable
- narrow-width viewport: layout remains usable without blocking core actions

Current evidence:

1. Non-visual dashboard behavior covered by unit tests:
   - `tests/unit/test_dashboard_pages.py`
   - `tests/unit/test_dashboard_data_access.py`
2. Data/aggregation behavior covered by analytics tests and CLI smoke path.
3. CSV sanitization behavior covered by unit tests and deployment runbook.

Pending manual evidence:

- interactive browser pass for desktop and narrow-width layouts in Streamlit runtime
- capture operator notes for page-by-page UI behavior under filtered and empty-state conditions
- note: this cloud coding environment does not provide an interactive browser viewport, so
  final layout validation remains an operator/manual step

## Item-level acceptance checklist traceability

The entries below map every `ACCEPTANCE_CHECKLIST.md` line item to explicit status and
evidence.

### Installation and configuration

- `[VALIDATED_DEMO]` Clean clone installs successfully.
  - Evidence: editable install command history and passing quality-gate runs in `BUILD_STATUS.md`.
- `[VALIDATED_DEMO]` Demo mode launches without external credentials.
  - Evidence: `python3 scripts/smoke_test.py` and demo-seeding command evidence.
- `[VALIDATED_DEMO]` Invalid configuration fails with actionable messages.
  - Evidence: `tests/unit/test_config.py` and CLI/env validation behavior.
- `[VALIDATED_DEMO + AWAITING_CREDENTIALS]` Secrets are ignored by git and never logged.
  - Evidence: `.gitignore` coverage and secret-hygiene runbook; live credentialed log review pending.

### Reddit collection

- `[AWAITING_CREDENTIALS]` Read-only OAuth client verified.
  - Evidence target: live crawl run with Reddit credentials.
- `[VALIDATED_DEMO + AWAITING_CREDENTIALS]` Configured subreddit/query search works.
  - Evidence: fixture-path collector tests; live API verification pending.
- `[VALIDATED_DEMO]` Posts and comments are mapped correctly.
  - Evidence: `tests/unit/test_reddit_mapper.py`.
- `[VALIDATED_DEMO]` Comment count is capped.
  - Evidence: collector integration/unit behavior in collector tests.
- `[VALIDATED_DEMO]` Duplicate crawl creates no duplicate rows.
  - Evidence: repository/idempotency and collector integration tests.
- `[VALIDATED_DEMO + AWAITING_CREDENTIALS]` Active posts refresh correctly.
  - Evidence: fixture-path refresh logic validated; live refresh pending.
- `[VALIDATED_DEMO + AWAITING_CREDENTIALS]` Rate-limit information is recorded.
  - Evidence: collector error/rate-limit tests; live metadata capture pending.
- `[VALIDATED_DEMO]` Transient failures retry safely.
  - Evidence: `tests/unit/test_reddit_collector_errors.py`.
- `[VALIDATED_DEMO]` Permanent failures stop clearly.
  - Evidence: collector error-classification test coverage.

### Privacy and deletion

- `[VALIDATED_DEMO]` No author/user fields are stored.
  - Evidence: models/repository schema and mapping behavior.
- `[VALIDATED_DEMO]` Deleted/removed text is not retained.
  - Evidence: cleaning + deletion tests (`test_cleaning.py`, `test_deletion_sync.py`).
- `[VALIDATED_DEMO]` Deletion sync removes downstream evidence.
  - Evidence: `tests/unit/test_deletion_sync.py`, dashboard filtering tests.
- `[VALIDATED_DEMO]` Dashboard and CSV exclude deleted records.
  - Evidence: dashboard data-access/page tests plus explorer sanitization coverage.
- `[VALIDATED_DEMO]` Privacy/compliance documentation is complete.
  - Evidence: `docs/privacy-and-compliance.md`.

### AI analysis

- `[VALIDATED_DEMO]` VADER baseline works.
  - Evidence: `tests/unit/test_sentiment_baseline.py`.
- `[VALIDATED_DEMO]` Structured output validates against Pydantic.
  - Evidence: `tests/unit/test_ai_schemas.py`.
- `[VALIDATED_DEMO]` Labels are restricted to taxonomy.
  - Evidence: schema/prompt/classifier test coverage.
- `[VALIDATED_DEMO]` Prompt-injection fixtures are safely analyzed.
  - Evidence: `tests/unit/test_ai_classifier.py`, prompt fixtures.
- `[VALIDATED_DEMO]` Unchanged text is not re-analyzed.
  - Evidence: classifier/reanalysis tests.
- `[VALIDATED_DEMO]` Prompt-version change permits re-analysis.
  - Evidence: classifier prompt-version behavior tests.
- `[VALIDATED_DEMO]` Partial batch failure is recoverable.
  - Evidence: classifier/retry-queue tests in CLI and repository suites.
- `[VALIDATED_DEMO]` Token use and cost are stored.
  - Evidence: analysis persistence/repository tests and budget accounting tests.
- `[VALIDATED_DEMO]` Budget guard stops cleanly.
  - Evidence: `tests/unit/test_ai_budget.py`.

### Analytics

- `[VALIDATED_DEMO]` Core metric formulas match documentation.
  - Evidence: `tests/unit/test_analytics_aggregates.py`, `docs/dashboard-metrics.md`.
- `[VALIDATED_DEMO]` Emerging-theme score handles zero baseline.
  - Evidence: analytics aggregate tests.
- `[VALIDATED_DEMO]` Priority score components are visible.
  - Evidence: aggregate output and dashboard metric documentation/tests.
- `[VALIDATED_DEMO]` Evidence sampling is diverse and non-duplicative.
  - Evidence: aggregate/dash evidence helper tests.
- `[VALIDATED_DEMO]` Low sample sizes generate warnings.
  - Evidence: analytics behavior checks and dashboard rendering tests.

### Dashboard

- `[VALIDATED_DEMO]` All nine pages render.
  - Evidence: `tests/unit/test_dashboard_pages.py`.
- `[VALIDATED_DEMO]` Global filters persist and work.
  - Evidence: `tests/unit/test_dashboard_data_access.py`.
- `[VALIDATED_DEMO]` KPI cards match filtered data.
  - Evidence: dashboard data-access + page render tests.
- `[VALIDATED_DEMO]` Charts update correctly.
  - Evidence: dashboard page tests and deterministic analytics fixtures.
- `[VALIDATED_DEMO]` Empty states do not crash.
  - Evidence: dashboard page empty-state coverage.
- `[VALIDATED_DEMO]` Freshness indicator is accurate.
  - Evidence: pipeline-health and dashboard rendering logic tests.
- `[VALIDATED_DEMO]` Demo/live indicator is accurate.
  - Evidence: dashboard bundle source-path logic tests.
- `[VALIDATED_DEMO]` CSV export is sanitized.
  - Evidence: explorer sanitization tests in `test_dashboard_pages.py`.
- `[VALIDATED_DEMO]` Assistant is evidence-bound and filter-aware.
  - Evidence: assistant helper tests and dashboard filter tests.
- `[VALIDATED_DEMO]` Pipeline health shows coverage and spend.
  - Evidence: `tests/unit/test_pipeline_health.py` and page tests.
- `[AWAITING_MANUAL_UI]` Desktop and narrow-width layouts are usable.
  - Evidence target: browser-based operator pass (not available in this cloud coding runtime).

### Automation and deployment

- `[VALIDATED_DEMO]` CI passes.
  - Evidence: local CI-equivalent gate suite passing.
- `[VALIDATED_DEMO + AWAITING_CREDENTIALS]` Scheduled pipeline supports manual dispatch.
  - Evidence: workflow definitions + validator tests; live dispatch pending.
- `[VALIDATED_DEMO]` Workflows use concurrency and timeouts.
  - Evidence: workflow YAML + `scripts/validate_workflows.py` checks/tests.
- `[VALIDATED_DEMO]` Schedule avoids the top of the hour.
  - Evidence: workflow cron definitions and validator policy checks.
- `[VALIDATED_DEMO + AWAITING_CREDENTIALS]` Daily maintenance performs deletion sync.
  - Evidence: workflow step presence + deletion sync tests; live execution pending.
- `[AWAITING_MANUAL_UI + AWAITING_CREDENTIALS]` Streamlit deployment instructions work.
  - Evidence target: manual cloud deployment runbook execution.

### Quality

- `[VALIDATED_DEMO]` Ruff format check passes.
- `[VALIDATED_DEMO]` Ruff lint passes.
- `[VALIDATED_DEMO]` MyPy passes.
- `[VALIDATED_DEMO]` Pytest passes.
- `[VALIDATED_DEMO]` Core coverage is at least 80% or gaps are justified.
- `[VALIDATED_DEMO]` Smoke test passes.
- `[VALIDATED_DEMO]` Verification report distinguishes live and mocked checks.
- `[VALIDATED_DEMO]` Known limitations are documented.
  - Evidence for all quality items: latest full gate run (`76 passed`, `82%` coverage, smoke success),
    plus this report's live-vs-demo status sections and documented manual/credential boundaries.

## Live integration verification status

- Reddit OAuth + PRAW live verification: **AWAITING_CREDENTIALS**
- Supabase live connectivity verification: **AWAITING_CREDENTIALS**
- OpenAI live structured-output verification: **AWAITING_CREDENTIALS**

## Demo-mode verification status

- Default runtime mode remains `DEMO_MODE=true`.
- Demo fixture crawl path is exercised and tested.
- Deterministic seeded dataset generation is exercised and tested.
- AI Phase 3 foundation path currently runs through deterministic provider in demo mode.
