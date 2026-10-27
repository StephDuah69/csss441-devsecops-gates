# Automated Security Testing Plan & Verification Matrix

## 1. Scope & Test Objectives

The testing suite verifies both functional application behavior and security policy enforcement across 7 automated gates.

The primary objective is to prove:
1. Valid application functionality works reliably.
2. Insecure code, secrets, and vulnerable dependencies are reliably flagged.
3. Violations deterministically block the build.
4. Cryptographic signatures and build provenance attestations are validated before release.

---

## 2. Comprehensive Test Matrix

| Test Suite | Target | Tool / Framework | Test File / Command | Expected Result | Gate Type |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Unit: Health Endpoint** | `GET /health` | pytest + TestClient | `tests/test_app.py::test_health_endpoint` | 200 OK, `{"status": "healthy"}` | Quality Gate |
| **Unit: Security Headers** | Response Headers | pytest + TestClient | `tests/test_app.py::test_security_headers_present` | `nosniff`, `DENY`, `no-referrer` present | Quality Gate |
| **Integration: Book Listing** | `GET /books` | pytest + TestClient | `tests/test_app.py::test_get_all_books` | 200 OK, list of 6 sample books | Quality Gate |
| **Integration: Search Filter** | `GET /books?q=security` | pytest + TestClient | `tests/test_app.py::test_search_books_with_valid_query` | 200 OK, filtered records returned | Quality Gate |
| **Integration: Input Validation** | `GET /books?q=<script>` | pytest + TestClient | `tests/test_app.py::test_search_books_validation_invalid_characters` | 422 Unprocessable Entity | Quality Gate |
| **Integration: Length Limit** | `GET /books?q={51_chars}` | pytest + TestClient | `tests/test_app.py::test_search_books_validation_max_length` | 422 Unprocessable Entity | Quality Gate |
| **SAST: Custom Rule Tests** | `.semgrep/custom_rules.yml` | Semgrep `--test` | `semgrep --test .semgrep/custom_rules.yml tests/semgrep/` | All positive (# ruleid) and negative (# ok) assertions pass | Security Gate |
| **SAST: Application Scan** | `app/` | Semgrep scan | `semgrep scan --config .semgrep/custom_rules.yml --error app/` | 0 findings, exit code 0 | Security Gate |
| **Secrets: Git & Source** | Working tree | Gitleaks | `gitleaks detect --config .gitleaks.toml` | 0 secrets found, exit code 0 | Security Gate |
| **SCA: Dependencies** | `requirements.txt` | OSV-Scanner | `osv-scanner --lockfile=requirements.txt` | 0 vulnerabilities, exit code 0 | Security Gate |
| **Container Hardening** | `Dockerfile` | Checkov | `checkov -f Dockerfile --framework dockerfile` | Passes unprivileged user, healthcheck, no sudo | Security Gate |
| **DAST: Dynamic Scan** | Staging runtime | OWASP ZAP Baseline | `zaproxy/action-baseline -t http://localhost:8000` | 0 FAIL-level alerts in `.zap/rules.tsv` | Security Gate |
| **Release: Signature & Provenance** | Immutable Image Digest | Cosign + GH Attestation | `bash scripts/verify_release.sh <digest>` | Validates signature and SLSA provenance | Release Gate |
