# Manual Setup Checklist

These are the account-level steps a coding agent cannot reliably complete on your behalf.

## Local tools

- [ ] Install Git.
- [ ] Install Python 3.11 or 3.12.
- [ ] Install `uv` or use Python `venv` and `pip`.
- [ ] Clone or create the GitHub repository.

## Reddit

- [ ] Review current Reddit Data API and Developer Terms.
- [ ] Create a dedicated Reddit account for the application.
- [ ] Register an API application suitable for a read-only script.
- [ ] Copy the client ID and client secret.
- [ ] Set a distinctive user agent containing app name, version, and Reddit username.
- [ ] Confirm the intended prototype or commercial use is permitted.

## Supabase

- [ ] Create a Supabase project.
- [ ] Record the project URL and current server-side secret/service key.
- [ ] Run `migrations/001_initial_schema.sql` in the SQL editor or through the chosen migration process.
- [ ] Confirm tables, indexes, views, and RLS are present.
- [ ] Never place the privileged key in client-side code.

## AI provider

- [ ] Create an API project and key.
- [ ] Add prepaid credit only if needed.
- [ ] Choose a low-cost model that supports strict structured output.
- [ ] Put the model in `AI_MODEL`; do not hardcode it.
- [ ] Set a conservative monthly INR budget.
- [ ] Review whether sending Reddit text to the provider is permitted for the intended use.

## Local environment

- [ ] Copy `.env.example` to `.env`.
- [ ] Fill credentials locally.
- [ ] Keep `DEMO_MODE=true` until the demo works.
- [ ] Run `verify-env`.
- [ ] Run tests.
- [ ] Seed and launch demo dashboard.
- [ ] Switch to live mode and run a small crawler test.
- [ ] Run AI analysis on no more than 10 records initially.

## GitHub Actions

Add repository secrets:

- [ ] `REDDIT_CLIENT_ID`
- [ ] `REDDIT_CLIENT_SECRET`
- [ ] `REDDIT_USER_AGENT`
- [ ] `SUPABASE_URL`
- [ ] `SUPABASE_SERVICE_ROLE_KEY` or current equivalent
- [ ] `OPENAI_API_KEY`
- [ ] `AI_MODEL`
- [ ] `MONTHLY_AI_BUDGET_INR`
- [ ] `USD_INR_RATE`

Then:

- [ ] Run CI manually or via a push.
- [ ] Run the pipeline with `workflow_dispatch`.
- [ ] Inspect the database run records.
- [ ] Enable scheduled workflows.
- [ ] Confirm no overlapping runs.

## Streamlit Community Cloud

- [ ] Connect the GitHub repository.
- [ ] Select the dashboard entry point.
- [ ] Add server-side secrets in Streamlit settings.
- [ ] Deploy.
- [ ] Confirm every page renders.
- [ ] Confirm the app never displays a secret or environment dump.
- [ ] Confirm freshness and demo/live labels are accurate.

## Final compliance review

- [ ] No usernames are stored.
- [ ] Deleted content is removed from raw and derived evidence.
- [ ] No Reddit HTML scraping is used.
- [ ] No model training or fine-tuning uses the collected data.
- [ ] Public exports contain only sanitized fields.
- [ ] Commercial deployment has appropriate Reddit permission/agreement.
