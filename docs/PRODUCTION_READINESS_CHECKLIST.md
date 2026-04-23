# Production Readiness Checklist

Use this checklist before running production deployment workflows.

## 1. Prerequisites

- [ ] AWS credentials are valid and scoped to least privilege
- [ ] Required GitHub secrets are configured:
  - [ ] `AWS_ACCESS_KEY_ID`
  - [ ] `AWS_SECRET_ACCESS_KEY`
  - [ ] `AWS_REGION`
  - [ ] `API_BASE_URL`
  - [ ] `S3_BUCKET_NAME`
  - [ ] `CLOUDFRONT_DISTRIBUTION_ID`
  - [ ] `PROJECT_NAME`
- [ ] Terraform variables for target environment are reviewed

## 2. Pre-deploy Validation

- [ ] Backend tests pass: `pytest -q backend`
- [ ] Frontend unit tests pass: `cd frontend && npm test -- --watch=false --passWithNoTests`
- [ ] Lambda artifacts package successfully: `bash scripts/package_lambdas.sh`
- [ ] Terraform format check passes: `terraform -chdir=infrastructure/terraform fmt -check -recursive`
- [ ] Terraform validate passes: `terraform -chdir=infrastructure/terraform validate`
- [ ] Terraform plan is reviewed for route, permission, and state changes

## 3. Deploy Order

1. Run `.github/workflows/deploy-infra.yml` (manual dispatch).
2. Review uploaded Terraform plan artifact before apply.
3. Apply infrastructure changes with appropriate approvals.
4. Run `.github/workflows/deploy-app.yml` (manual dispatch).

## 4. Post-deploy Verification

- [ ] CloudFront root URL returns `200`
- [ ] Lambda `LastUpdateStatus` is `Successful` for:
  - [ ] auth
  - [ ] onboarding
  - [ ] recommendation-api
  - [ ] recommendation-worker
  - [ ] anime-getter
  - [ ] interactions
  - [ ] lists
  - [ ] data-ingest
- [ ] Core user flows verified manually:
  - [ ] Signup/login
  - [ ] Onboarding submit
  - [ ] Recommendations trigger + fetch
  - [ ] Anime profile load
  - [ ] Similar anime section load
  - [ ] Add/remove list item
  - [ ] Rating submit and persistence

## 5. Rollback Verification

- [ ] Previous frontend build is available in S3 version history
- [ ] Previous Lambda zip artifacts are retained and identifiable
- [ ] Terraform state snapshot is available before apply
- [ ] Rollback owner is assigned and reachable

## 6. Release Notes Gate

- [ ] Delivered scope is captured
- [ ] Deferred items are listed
- [ ] Known risks and follow-ups are documented
