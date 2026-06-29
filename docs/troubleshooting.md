# Troubleshooting

## CI failures

### `scripts/validate_workflows.py` fails

Cause:

- workflow YAML syntax issues
- missing required workflow policy fields (e.g., concurrency controls, `demo_mode` inputs)
- missing required timeout bounds or critical operational step names
- CI workflow no longer runs workflow validation step

Resolution:

1. Run locally:
   - `python3 scripts/validate_workflows.py`
2. Fix reported workflow YAML issues.
3. Re-run quality gates.

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

### Suspected secret exposure in logs or artifacts

Symptoms:

- API keys, service role values, tokens, or connection strings appear in job logs.
- Workflow artifacts include `.env`, shell history, or environment dumps.
- Debug output contains unredacted provider credentials.

Immediate containment:

1. Stop re-running affected workflows until secrets are rotated.
2. Rotate exposed credentials at provider side:
   - Reddit app secret
   - Supabase service role key
   - OpenAI API key
3. Remove or expire affected workflow artifacts where possible.
4. Revoke any leaked tokens/sessions and reissue least-privilege credentials.

Root-cause checklist:

1. Check for accidental `echo`/print of env vars in workflow `run` blocks.
2. Check for commands that pass secrets as CLI arguments rather than environment variables.
3. Check for debug scripts dumping `os.environ` or full settings objects.
4. Check for local `.env` files accidentally included in artifacts.

Recovery validation:

1. Run in `demo_mode=true` and verify no secrets are needed or printed.
2. Re-run `python3 scripts/validate_workflows.py`.
3. Re-run full quality gates locally.
4. Re-dispatch live-mode workflow after rotation and confirm logs are clean.

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
