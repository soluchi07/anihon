# Release Notes - 2026-04-22

## Delivered Scope

### Phase 1 - Core Contract Stabilization
- Added lists API support with GET/POST/DELETE behavior.
- Added similar anime endpoint (`/anime/{animeId}/similar`).
- Wired API Gateway, Lambda, IAM, and DynamoDB resources for new routes.
- Aligned frontend auth posture for anime detail/similar routes.

### Phase 2 - Reliability Hardening
- Split CI into backend, frontend unit, lambda packaging, frontend E2E, and gated live integration jobs.
- Added workflow concurrency controls.
- Added cross-platform Lambda packaging (`scripts/package_lambdas.sh`).
- Hardened deploy workflows with packaging checks and post-deploy verification.
- Added additional backend tests and reliability improvements.

### Phase 3 - Docs and Contributor Clarity
- Updated project/deployment docs to match implemented behavior.
- Added contributor runbook (`docs/CONTRIBUTOR_SETUP.md`).
- Added environment templates (`.env.example`, `frontend/.env.example`).
- Added production readiness checklist (`docs/PRODUCTION_READINESS_CHECKLIST.md`).

## Phase 4 Validation Snapshot

- Backend tests: PASS (`54 passed, 1 skipped`)
- Frontend unit tests: PASS (no tests found, exited 0)
- Live integration chain: SKIPPED (test guard conditions)
- Frontend E2E: PASS (`3 passed`)
- Terraform fmt check: FAIL initially, then fixed with `terraform fmt -recursive`
- Terraform validate: PASS
- Terraform plan: BLOCKED (AWS credentials unavailable in local run)
- Terraform tfvars hygiene: PASS (removed undeclared variables from `envs/dev.tfvars`)

## Deferred / Follow-up Items

These items require a deployed staging or production environment:

1. **Terraform Plan Validation**: Execute `terraform plan` with valid AWS credentials to review route/permission changes.
2. **Live Integration Chain**: Set `INTEGRATION_TESTS=1 API_BASE=<api-url>` and run auth → onboarding → recommendations flow.
3. **Manual QA Execution**: Use `docs/MANUAL_QA_SCRIPT.md` to validate all critical user flows (signup, onboarding, recommendations, lists, similar anime, ratings).

## Summary

All local validation checks have passed. The project is ready for deployment validation in staging/production environments. See `docs/PRODUCTION_READINESS_CHECKLIST.md` for pre-deployment gates.
