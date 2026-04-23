# Contributor Setup Runbook

This runbook describes how to get AnimeRec running locally for backend tests, frontend development, and optional integration/E2E validation.

## 1. Prerequisites

- Python 3.11+
- Node.js 18+
- npm
- Bash (Git Bash on Windows is fine)
- Terraform 1.4+
- AWS CLI configured (only needed for infra/deploy or live integration checks)

## 2. Clone and create virtual environment

```bash
git clone <repo-url>
cd animerec
python -m venv .venv
```

Activate the virtual environment:

```bash
# Windows (Git Bash)
source .venv/Scripts/activate

# Windows (PowerShell)
.\.venv\Scripts\Activate.ps1

# macOS/Linux
source .venv/bin/activate
```

## 3. Install local dependencies

```bash
python -m pip install --upgrade pip
pip install pytest
cd frontend
npm ci
cd ..
```

## 4. Configure environment variables

- Copy [.env.example](../.env.example) to `.env` if you plan to run optional live integration checks.
- Copy [frontend/.env.example](../frontend/.env.example) to `frontend/.env.development` if you need a local API base override.

## 5. Run local validation

### Backend unit tests

```bash
pytest -q backend
```

### Frontend unit tests

```bash
cd frontend
npm test -- --watch=false --passWithNoTests
```

### Frontend E2E (opt-in)

```bash
cd frontend
E2E_TESTS=1 E2E_BASE_URL=http://localhost:3001 npm run test:e2e
```

### Live integration chain (opt-in)

```bash
INTEGRATION_TESTS=1 API_BASE=<api-base-url> pytest -q backend/tests/integration/test_live_auth_flow.py
```

## 6. Package Lambda artifacts locally

```bash
bash scripts/package_lambdas.sh
```

Expected output: zip artifacts under `build/lambdas/` for each Lambda directory that contains a `handler.py` file.

## 7. Infrastructure checks

```bash
terraform -chdir=infrastructure/terraform fmt -check -recursive
terraform -chdir=infrastructure/terraform validate
terraform -chdir=infrastructure/terraform plan -var-file=envs/dev.tfvars
```

## 8. Common issues

- If E2E tests are skipped, ensure `E2E_TESTS=1` is set.
- If live integration test is skipped, set both `INTEGRATION_TESTS=1` and `API_BASE`.
- If Lambda packaging fails due to missing `zip`, the script falls back to Python `zipfile`; verify `python3` is on your PATH.
