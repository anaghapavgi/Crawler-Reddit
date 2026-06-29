# Privacy and Compliance

## Scope

This checklist captures the Phase 7 compliance hardening evidence required before final sign-off.

## Required controls checklist

### Data minimization and handling

- [ ] No Reddit usernames are stored in persisted analytics records.
- [ ] No sensitive-trait inference logic exists in prompts, models, or outputs.
- [ ] Deleted/removed content is excluded from dashboards, exports, and derived evidence.
- [ ] Public/exported fields are sanitized and bounded.

### Collection and platform policy compliance

- [ ] Reddit data access uses official API client flow (no HTML scraping).
- [ ] User-agent format is explicit and policy-compliant.
- [ ] Live-mode verification logs do not include secret values.

### AI and budget governance

- [ ] AI responses are validated with strict schemas before persistence.
- [ ] Prompt version/model/tokens/cost metadata is stored per analysis run.
- [ ] Budget caps (per-run and monthly) are enforced and test-covered.

### Secrets and environment hygiene

- [ ] `.env` and secret files are excluded from version control.
- [ ] CI workflows use repository secrets for live-mode paths.
- [ ] Workflow live-mode guard fails fast when secrets are missing.

## Evidence placeholders

Record links or outputs for each item above during final Phase 7 verification:

1. Command/test output references:
   - `ruff`, `mypy`, `pytest --cov`, `scripts/smoke_test.py`
2. Workflow run references:
   - CI run URL(s)
   - pipeline/manual dispatch run URL(s)
3. Documentation references:
   - `docs/verification-report.md`
   - `docs/deployment.md`
   - `docs/troubleshooting.md`
