# Team Responsibility Matrix & Individual Contribution Records

## 1. Team Organization & Roles

| Member Name | Assigned Role | Primary Focus Area | Secondary Responsibilities |
| :--- | :--- | :--- | :--- |
| **Alex Rivera** (Lead) | Integration & Release Lead | CI Orchestration, Sigstore Cosign, Provenance, Verification | Overall architectural cohesion, PR reviews, Final Report |
| **Jordan Chen** | Source Security Engineer | Gitleaks, Pre-commit hooks, Secret Management | Secret rotation procedures, Developer setup guide |
| **Morgan Taylor** | AppSec & Static Analysis Engineer | CodeQL workflow, Custom Semgrep Rules, Rule Tests | Rule false-positive tuning, CWE/OWASP mapping |
| **Casey Patel** | Container & SCA Security Engineer | OSV-Scanner, Trivy (FS/Image), Syft SBOMs, Checkov | Dockerfile multi-stage hardening, Compose resource limits |
| **Riley Zhang** | DAST & Vulnerability Operations | Ephemeral Staging, OWASP ZAP Baseline, DefectDojo | ZAP rules tuning, DefectDojo scan ingestion client |

---

## 2. Five-Member Responsibility Matrix

| Task Description | Owner | Dependencies | Expected Files | Acceptance Criteria | Internal Deadline | Evidence Required | Reviewer |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **1. Target Application & Tests** | Alex Rivera | None | `app/main.py`, `tests/test_app.py` | 100% pytest pass rate, input validation, non-root user | Week 2 | Pytest execution logs (10/10 passing) | Jordan Chen |
| **2. Secret Scanning & Hooks** | Jordan Chen | Task 1 | `.gitleaks.toml`, `.pre-commit-config.yaml` | Pre-commit blocks synthetic test secret; CI fails on leak | Week 3 | Demonstration 1 log (`CSSS441-SEC-001`) | Morgan Taylor |
| **3. Semgrep Custom Rules & Tests** | Morgan Taylor | Task 1 | `.semgrep/custom_rules.yml`, `tests/semgrep/` | 5 custom rules with passing positive & negative unit tests | Week 3 | Semgrep `--test` output showing 0 failures | Alex Rivera |
| **4. CodeQL Static Analysis** | Morgan Taylor | Task 1 | `.github/workflows/codeql.yml` | Weekly and PR workflow analyzing Python without permissions creep | Week 4 | GitHub Security tab CodeQL scan summary | Riley Zhang |
| **5. Dependency Scanning (SCA)** | Casey Patel | Task 1 | `requirements.txt`, `.github/workflows/ci.yml` | OSV-Scanner and Trivy block HIGH/CRITICAL CVEs | Week 4 | Demonstration 2 log (`CVE-2024-37891`) | Jordan Chen |
| **6. Hardened Container & Checkov** | Casey Patel | Task 1, 5 | `Dockerfile`, `compose.yaml` | Multi-stage build, unprivileged user 10001, Checkov passes | Week 5 | Checkov clean scan report, non-root verification | Alex Rivera |
| **7. Ephemeral Staging & ZAP DAST**| Riley Zhang | Task 6 | `.zap/rules.tsv`, `.github/workflows/ci.yml` | Ephemeral container launches, ZAP baseline runs, environment torn down | Week 5 | ZAP HTML & JSON reports in `reports/` | Casey Patel |
| **8. DefectDojo Integration** | Riley Zhang | Task 2, 3, 5, 7 | `scripts/import_reports.py` | Scan reports imported into DefectDojo engagement via API | Week 6 | DefectDojo dashboard finding screenshot/logs | Alex Rivera |
| **9. Image Signing & Provenance** | Alex Rivera | Task 6 | `.github/workflows/release.yml`, `scripts/verify_release.sh` | Cosign keyless signing + SLSA provenance verified before release | Week 6 | Demonstration 3 log (`CSSS441-SIG-001`) | Casey Patel |
| **10. Documentation & Defense Pack**| All Members | Tasks 1-9 | `docs/*.md`, `README.md`, presentation plan | Comprehensive documentation covering all course requirements | Week 7 | Complete repository walkthrough & demo script | All Members |

---

## 3. Transparency & Recovery Procedures

1. **Pull Request Protocol**:
   - No direct pushes to `main`.
   - Every pull request requires at least one peer approval from the designated Reviewer.
   - All CI checks (Pytest, Gitleaks, Semgrep, Trivy, Checkov, ZAP) must be green before merge.
2. **Delayed Task Escalation**:
   - If a member is blocked for > 48 hours, an issue is tagged `status: blocked`.
   - The Integration Lead convenes an emergency sync to reassign or pair on the blocker without completing the work silently.
   - Clear recovery commits document all collaborative pair-programming sessions.
