# Troubleshooting

## CI failures

### MyPy fails in GitHub Actions with NumPy stub syntax errors

Symptom example:

`numpy/__init__.pyi: ... Type statement is only supported in Python 3.12 and greater`

Cause:

- CI runs Python 3.12 but MyPy was configured for an older target version.

Resolution:

- keep `[tool.mypy].python_version` aligned with CI Python version in `pyproject.toml`
- re-run:
  - `python3 -m mypy src`
  - full quality gates

## Pipeline and maintenance workflow failures

### `Missing required secrets for live mode`

Cause:

- manual dispatch used `demo_mode=false` without all required live secrets configured.

Resolution:

1. Configure repository secrets:
   - `REDDIT_CLIENT_ID`
   - `REDDIT_CLIENT_SECRET`
   - `REDDIT_USER_AGENT`
   - `SUPABASE_URL`
   - `SUPABASE_SERVICE_ROLE_KEY`
   - `OPENAI_API_KEY`
   - `AI_MODEL`
2. Re-run manual dispatch.
3. If live execution is not required, run with `demo_mode=true`.

### `verify-env` fails in live mode

Cause:

- runtime settings validation detected missing required env vars.

Resolution:

- confirm the same live secrets list above
- ensure secrets are set in the repository running the workflow
- re-dispatch with `demo_mode=false` only after secrets are present

## Dashboard Explorer export issues

### Exported CSV looks "prefixed" with single quotes

Cause:

- expected behavior from formula-injection sanitization.

Why:

- spreadsheet software can execute formulas from cells beginning with dangerous prefixes.
- export intentionally writes values as literal text to avoid execution.

Validation:

- run unit tests:
  - `python3 -m pytest tests/unit/test_dashboard_pages.py -q`
- verify manual export output from dashboard Explorer page.
