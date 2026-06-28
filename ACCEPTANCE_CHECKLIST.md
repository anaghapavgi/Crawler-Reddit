# Final Acceptance Checklist

## Installation and configuration

- [ ] Clean clone installs successfully.
- [ ] Demo mode launches without external credentials.
- [ ] Invalid configuration fails with actionable messages.
- [ ] Secrets are ignored by git and never logged.

## Reddit collection

- [ ] Read-only OAuth client verified.
- [ ] Configured subreddit/query search works.
- [ ] Posts and comments are mapped correctly.
- [ ] Comment count is capped.
- [ ] Duplicate crawl creates no duplicate rows.
- [ ] Active posts refresh correctly.
- [ ] Rate-limit information is recorded.
- [ ] Transient failures retry safely.
- [ ] Permanent failures stop clearly.

## Privacy and deletion

- [ ] No author/user fields are stored.
- [ ] Deleted/removed text is not retained.
- [ ] Deletion sync removes downstream evidence.
- [ ] Dashboard and CSV exclude deleted records.
- [ ] Privacy/compliance documentation is complete.

## AI analysis

- [ ] VADER baseline works.
- [ ] Structured output validates against Pydantic.
- [ ] Labels are restricted to taxonomy.
- [ ] Prompt-injection fixtures are safely analyzed.
- [ ] Unchanged text is not re-analyzed.
- [ ] Prompt-version change permits re-analysis.
- [ ] Partial batch failure is recoverable.
- [ ] Token use and cost are stored.
- [ ] Budget guard stops cleanly.

## Analytics

- [ ] Core metric formulas match documentation.
- [ ] Emerging-theme score handles zero baseline.
- [ ] Priority score components are visible.
- [ ] Evidence sampling is diverse and non-duplicative.
- [ ] Low sample sizes generate warnings.

## Dashboard

- [ ] All nine pages render.
- [ ] Global filters persist and work.
- [ ] KPI cards match filtered data.
- [ ] Charts update correctly.
- [ ] Empty states do not crash.
- [ ] Freshness indicator is accurate.
- [ ] Demo/live indicator is accurate.
- [ ] CSV export is sanitized.
- [ ] Assistant is evidence-bound and filter-aware.
- [ ] Pipeline health shows coverage and spend.
- [ ] Desktop and narrow-width layouts are usable.

## Automation and deployment

- [ ] CI passes.
- [ ] Scheduled pipeline supports manual dispatch.
- [ ] Workflows use concurrency and timeouts.
- [ ] Schedule avoids the top of the hour.
- [ ] Daily maintenance performs deletion sync.
- [ ] Streamlit deployment instructions work.

## Quality

- [ ] Ruff format check passes.
- [ ] Ruff lint passes.
- [ ] MyPy passes.
- [ ] Pytest passes.
- [ ] Core coverage is at least 80% or gaps are justified.
- [ ] Smoke test passes.
- [ ] Verification report distinguishes live and mocked checks.
- [ ] Known limitations are documented.
