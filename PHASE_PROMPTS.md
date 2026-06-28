# Phase-by-Phase Prompts

Use these prompts if the coding agent performs better with smaller missions. Paste one phase at a time after placing `MASTER_BUILD_PROMPT.md` and `AGENTS.md` in the repository.

## Phase 0 - Plan and scaffold

Read `MASTER_BUILD_PROMPT.md` and `AGENTS.md`. Implement Phase 0 only. Inspect the repository, create the target structure, Python project configuration, lint/type/test tooling, environment template, CLI skeleton, demo-mode skeleton, architecture document, README skeleton, and `BUILD_STATUS.md`. Run the Phase 0 acceptance gate. Do not start Reddit, Supabase, or AI integration yet. Report exact commands and test results.

## Phase 1 - Configuration and data layer

Implement Phase 1 from `MASTER_BUILD_PROMPT.md`. Add validated settings, research/taxonomy YAML loading, domain models, Supabase adapter, SQL migration, repositories, idempotent upsert behavior, and a credential-free demo repository. Add tests for validation, payloads, and demo seeding. Run all quality gates and update `BUILD_STATUS.md`.

## Phase 2 - Reddit collection

Implement Phase 2. Use read-only PRAW through an adapter. Add search, mapping, comment collection, cleaning, rule-based relevance, hashing, incremental refresh, rate-limit logging, retry policy, run status, and deletion detection. Use fixture-based tests and mocks. Test live only when credentials are present. Do not scrape HTML. Run all quality gates and update status.

## Phase 3 - AI analysis

Implement Phase 3. Add provider abstraction, OpenAI structured-output adapter, strict Pydantic result schemas, prompt-injection-resistant prompts, VADER baseline, batching, retries, failure queue, state transitions, model/prompt/hash tracking, token usage, INR cost estimate, and budget guard. Add malformed-output and prompt-injection tests. Run all quality gates.

## Phase 4 - Analytics

Implement Phase 4. Create database views and Python metric functions for sentiment, themes, features, segments, coverage, priority, emergence, evidence sampling, data quality, pipeline health, and cost. Add deterministic fixture tests including zero-volume and deleted-content cases.

## Phase 5 - Dashboard

Implement all dashboard pages from the master prompt using `st.Page`, `st.navigation`, Plotly, global filters, short-TTL caching, synthetic demo data, and polished empty states. Verify every page in a browser, test narrow and desktop widths, test filters and CSV export, and record screenshots or observations in `docs/verification-report.md`. Do not expose secrets or usernames.

## Phase 6 - Scheduling and deployment

Implement CI, scheduled pipeline, and daily maintenance GitHub Actions. Include manual dispatch, concurrency, timeouts, non-top-of-hour schedules, environment secrets, and clear job failures. Write exact Supabase, GitHub, Reddit, OpenAI, and Streamlit setup/deployment instructions. Validate workflow syntax and run local smoke tests.

## Phase 7 - Hardening and final QA

Implement deletion synchronization and downstream invalidation, retry handling, security review, dependency checks, full documentation, clean-environment setup, test coverage, and final browser verification. Search tracked files for secrets. Complete the definition-of-done checklist and provide an honest list of live integrations not verified due to missing credentials.
