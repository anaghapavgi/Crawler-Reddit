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

## Live integration verification status

- Reddit OAuth + PRAW live verification: **AWAITING_CREDENTIALS**
- Supabase live connectivity verification: **AWAITING_CREDENTIALS**
- OpenAI live structured-output verification: **AWAITING_CREDENTIALS**

## Demo-mode verification status

- Default runtime mode remains `DEMO_MODE=true`.
- Demo fixture crawl path is exercised and tested.
- Deterministic seeded dataset generation is exercised and tested.
- AI Phase 3 foundation path currently runs through deterministic provider in demo mode.
