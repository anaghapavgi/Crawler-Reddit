# Manual Setup Plan and Boundaries (Pre-Implementation)

## Purpose

This document separates:
- work that can be completed autonomously in demo mode; and
- steps that require human-managed accounts, credentials, or platform settings.

At this stage, `DEMO_MODE=true` remains required.

## 1. What can be completed without credentials

The following implementation and verification tasks can be completed locally in demo mode:

1. Python project scaffolding and dependency setup.
2. Environment schema validation and startup checks.
3. Config loader and taxonomy validation.
4. Database migration authoring and static review.
5. Repository/upsert logic tests against fakes/mocks.
6. Reddit collector logic using fixtures/mocks.
7. Cleaning, relevance, hashing, and idempotency tests.
8. VADER baseline integration.
9. Structured AI pipelines with mocked provider responses.
10. Budget/cost guard logic and tests.
11. SQL analytics definitions and fixture-based validation.
12. Full Streamlit dashboard rendering on synthetic data.
13. GitHub workflow authoring and static validation.
14. Smoke and quality checks in local/demo context.

## 2. Steps requiring manual setup (deferred until demo path passes)

### Reddit API
- Create Reddit app credentials.
- Provide:
  - `REDDIT_CLIENT_ID`
  - `REDDIT_CLIENT_SECRET`
  - `REDDIT_USER_AGENT` (distinctive and policy-compliant)
- Confirm intended usage is compliant with current Reddit Data API terms.

### Supabase
- Create project and record:
  - `SUPABASE_URL`
  - `SUPABASE_SERVICE_ROLE_KEY`
- Apply migration SQL in Supabase.
- Confirm tables, indexes, views, and RLS are correctly created.

### AI provider
- Create provider key:
  - `OPENAI_API_KEY` (or compatible key per configured provider)
  - `AI_MODEL`
- Review provider data handling terms for production use.
- Keep conservative budget settings.

### GitHub Actions runtime
- Configure repository secrets for pipeline workflows.
- Manually run `workflow_dispatch` and verify run artifacts/logs.
- Enable schedules after manual validation.

### Streamlit deployment
- Connect repo to Streamlit Community Cloud.
- Add server-side secrets/settings.
- Validate deployed pages and labels (demo/live, freshness).

## 3. Manual setup checklist by phase

| Phase | Manual setup required to proceed | Can continue in demo mode? |
|---|---|---|
| 0 | None | Yes |
| 1 | Supabase optional (for live DB verification only) | Yes |
| 2 | Reddit credentials for live crawl verification | Yes |
| 3 | AI provider key/model for live structured-output verification | Yes |
| 4 | Supabase live DB preferred for SQL runtime checks | Yes |
| 5 | None for local demo UI; Streamlit account for cloud deployment | Yes |
| 6 | GitHub secrets and repo settings | Partially |
| 7 | All credentials for final live end-to-end verification | Partially |

## 4. Credential handling rules

1. Never commit `.env` or real secrets.
2. Never print secret values in logs.
3. Prefer local `.env` and secure secret stores for CI/deployment.
4. Keep privileged Supabase keys server-side only.
5. Treat missing credentials as expected during demo-first development.

## 5. Deferred verification notes

Until credentials are provided, mark live checks as:
- `AWAITING_CREDENTIALS` in `BUILD_STATUS.md` where applicable.

Do not claim external integration success without real execution evidence.
