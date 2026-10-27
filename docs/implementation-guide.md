# Academic Implementation & Reproducibility Guide

## 1. Introduction

This guide provides exact, step-by-step instructions to reproduce the entire **CSSS 441 Software Security DevSecOps Pipeline** from a clean workstation or grading environment.

---

## 2. Prerequisites

- **Python**: 3.11, 3.12, or 3.13
- **Git**: 2.30+
- **Docker & Docker Compose**: (Required for containerization and dynamic ZAP testing)
- **GitHub Account & Repository**: For running GitHub Actions workflows with GHCR package publishing permissions.

---

## 3. Quickstart: 3-Minute Setup

### Step 1: Clone and Enter Repository
```bash
git clone <repository-url> csss441-devsecops-gates
cd csss441-devsecops-gates
```

### Step 2: Automated Environment Setup
On Linux / macOS / Git Bash:
```bash
bash scripts/setup.sh
```
Or manually using Python:
```bash
python -m venv .venv
# On Windows:
.\.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate

pip install --upgrade pip
pip install -r requirements-dev.txt
```

### Step 3: Run Application Test Suite
```bash
pytest -v
```
Expected output: 10 passed tests, 100% test coverage for health and book catalogue endpoints.

### Step 4: Run Code Quality & Security Linter
```bash
ruff check .
ruff format --check .
```
Expected output: All checks passed.

---

## 4. Running Local Security Scanners

### Semgrep Custom Rule Testing
Verify that custom Semgrep rules pass both positive (must trigger) and negative (must not trigger) assertions:
```bash
semgrep --test --config .semgrep/custom_rules.yml tests/semgrep/
```
Expected output: All 5 custom rules report `reported: 1, expected: 1` on positive lines and `0` on `# ok` lines.

### Semgrep Application Scan
Scan the production application code:
```bash
semgrep scan --config .semgrep/custom_rules.yml --error app/
```
Expected output: 0 violations, clean scan.

### Gitleaks Secret Detection
```bash
gitleaks detect --verbose --config .gitleaks.toml
```
Expected output: No leaks found.

### Checkov Container Configuration Scan
```bash
checkov -f Dockerfile -f compose.yaml --compact
```
Expected output: Passed checks for unprivileged user, dropped capabilities, and read-only filesystem.

---

## 5. Docker Container Build & Local Execution

### Build Hardened Image
```bash
docker build -t csss441-book-catalog:local .
```

### Launch Container via Docker Compose
```bash
docker compose up -d
```

### Verify Container Health
```bash
curl -i http://127.0.0.1:8000/health
```
Response:
```json
HTTP/1.1 200 OK
content-type: application/json
x-content-type-options: nosniff
x-frame-options: DENY

{"status":"healthy","app":"csss441-book-catalog","version":"1.0.0"}
```

### Clean Up Staging
```bash
docker compose down -v
```

---

## 6. GitHub Actions Configuration

1. **Repository Settings -> Actions -> General**:
   - Workflow permissions: Read and write permissions (or Read permissions with explicit job-level grants).
2. **GitHub Container Registry (GHCR)**:
   - Ensure package creation is enabled for workflows.
3. **Branch Protection Rules**:
   - Require status checks to pass before merging:
     - `Lint, Unit Tests & Secrets`
     - `Semgrep SAST & Rule Tests`
     - `OSV-Scanner, Trivy & Checkov`
     - `Container Build & Image Scan`
     - `Ephemeral Staging & ZAP DAST`
     - `Security Gate Policy Evaluation`

---

## 7. Protected Release & Provenance Verification

When a release tag (e.g., `v1.0.0`) is pushed:
1. `release.yml` triggers.
2. The image is built and pushed to GHCR.
3. The exact SHA-256 digest is signed using Sigstore Cosign (keyless OIDC with GitHub Actions).
4. GitHub's `actions/attest-build-provenance` produces a cryptographic SLSA provenance attestation.
5. `scripts/verify_release.sh` executes pre-release verification:
   ```bash
   bash scripts/verify_release.sh <image-digest-reference>
   ```
6. The release is approved only after both signature and provenance pass verification.

---

## 8. DefectDojo Vulnerability Management Setup

To run DefectDojo locally via Docker:
```bash
git clone https://github.com/DefectDojo/django-DefectDojo
cd django-DefectDojo
./dc-build.sh
./dc-up-d.sh
```
Retrieve the initial admin password from container logs, navigate to `http://localhost:8080`, generate an API v2 token, and import scanner reports:
```bash
export DEFECTDOJO_URL="http://localhost:8080"
export DEFECTDOJO_TOKEN="<your-api-key>"
export DEFECTDOJO_ENGAGEMENT_ID="1"

python scripts/import_reports.py --reports-dir reports/
```
