# Team Responsibility Matrix & Individual Contribution Records
## CSSS 441 Software Security I — Project 2: DevSecOps Pipeline with Security Gates

---

## 1. Team Organization & Roles

| Member Name | Student Index No. | GitHub Profile | Assigned Role | Primary Focus Area | Secondary Responsibilities |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Hannah Amoaba Larbi** (Lead) | `1700237691` | [@hannahamoaba](https://github.com/hannahamoaba) | Team Lead & Release Verification Engineer | CI/CD Pipeline Orchestration, Sigstore Cosign, SLSA Provenance, Release Verification Gates | Overall architectural cohesion, PR reviews, Final Technical Report |
| **Stephen Kwadwo Duah** | `1696334280` | [@StephDuah69](https://github.com/StephDuah69) | Source Security & Secrets Engineer | Gitleaks Pre-Commit Hooks, Secret Scanning, Repository Administration, CI Hardening | Secret rotation protocols, developer setup automation (`setup.sh`) |
| **Othniel Kpakpo Saka** | `1705408739` | [@thetravelerkweku-ops](https://github.com/thetravelerkweku-ops) | AppSec & Static Analysis Engineer | 5 Custom Semgrep SAST Rules, Positive/Negative Rule Tests, SAST Policies | Rule false-positive tuning, CWE/OWASP mapping, SAST gate policies |
| **Jesu Henry Quaijah** | Group Contributor | [@jesu-henry](https://github.com/jesu-henry) | Static Code Analysis Engineer | GitHub CodeQL Static Analysis, AST Rule Verification, Security Policy Tuning | CodeQL PR workflows, Python security auditing |
| **Fred Nkrumah** | `1703603625` | [@Afrifar055-sketch](https://github.com/Afrifar055-sketch) | Container & SCA Security Engineer | Multi-Stage Hardened Dockerfile, Checkov IaC Policies, OSV-Scanner, Trivy, Syft SBOMs | Compose resource constraints, read-only rootfs compliance, image tagging |
| **Benjamin Essibo Ofori** | `1693417365` | [@ben244294](https://github.com/ben244294) | DAST & Vulnerability Operations Engineer | Ephemeral Staging Deployment, OWASP ZAP Baseline DAST, DefectDojo API Client | ZAP alert tuning (`.zap/rules.tsv`), Remediation Log & MTTF metrics |

---

## 2. Team Responsibility Matrix & Deliverable Sign-Off

| Task Description | Owner | Student Index | Dependencies | Key Deliverables & Files | Acceptance Criteria | Evidence Required | Designated Peer Reviewer |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **1. Target Application & Tests** | Hannah Amoaba Larbi | `1700237691` | None | `app/main.py`, `tests/test_app.py`, `app/routers/` | 100% pytest pass rate, strict input validation, non-root user execution | Pytest execution logs (25/25 passing) | Stephen Kwadwo Duah |
| **2. Secret Scanning & Hooks** | Stephen Kwadwo Duah | `1696334280` | Task 1 | `.gitleaks.toml`, `.pre-commit-config.yaml`, CI Job 1 | Pre-commit blocks synthetic test secret; CI halts on leaked credential | Demonstration 1 log (`CSSS441-SEC-001`) | Othniel Kpakpo Saka |
| **3. Semgrep Custom Rules & Tests** | Othniel Kpakpo Saka | `1705408739` | Task 1 | `.semgrep/custom_rules.yml`, `tests/semgrep/` | 5 custom rules passing positive (`# ruleid`) and negative (`# ok`) assertions | Semgrep `--test` output showing 0 failures | Hannah Amoaba Larbi |
| **4. CodeQL Static Analysis** | Jesu Henry Quaijah | Group Contributor | Task 1 | `.github/workflows/codeql.yml` | Weekly and PR workflows analyzing Python code without permissions creep | GitHub Security tab CodeQL scan summary | Benjamin Essibo Ofori |
| **5. Dependency Scanning (SCA)** | Fred Nkrumah | `1703603625` | Task 1 | `requirements.txt`, `.github/workflows/ci.yml` | OSV-Scanner, Trivy, and pip-audit block HIGH/CRITICAL vulnerabilities | Demonstration 2 log (`CVE-2024-37891`) | Stephen Kwadwo Duah |
| **6. Hardened Container & Checkov** | Fred Nkrumah | `1703603625` | Task 1, 5 | `Dockerfile`, `compose.yaml` | Multi-stage build, unprivileged user `10001`, dropped capabilities, Checkov passes | Checkov clean scan report, non-root verification | Hannah Amoaba Larbi |
| **7. Ephemeral Staging & ZAP DAST** | Benjamin Essibo Ofori | `1693417365` | Task 6 | `.zap/rules.tsv`, `.github/workflows/ci.yml` (Job 5) | Ephemeral container launches, ZAP baseline runs, environment torn down cleanly | ZAP HTML & JSON reports in `reports/` | Fred Nkrumah |
| **8. DefectDojo Integration** | Benjamin Essibo Ofori | `1693417365` | Task 2, 3, 5, 7 | `scripts/import_reports.py` | Multi-tool scan reports imported into DefectDojo engagement via API | DefectDojo dashboard finding logs | Hannah Amoaba Larbi |
| **9. Image Signing & Provenance** | Hannah Amoaba Larbi | `1700237691` | Task 6 | `.github/workflows/release.yml`, `scripts/verify_release.sh` | Cosign keyless signing + SLSA provenance verified cryptographically | Demonstration 3 log (`CSSS441-SIG-001`) | Fred Nkrumah |
| **10. Documentation & Defense Pack**| All Members | Group | Tasks 1–9 | `docs/*.md`, `README.md`, presentation deck | Comprehensive documentation covering all course milestones & rubric | Full repository walkthrough & demo script | All Members |

---

## 3. Team Protocols & Defense Preparation

1. **Pull Request Protocol**:
   - No direct pushes to `main`.
   - Every pull request requires at least one peer approval from the designated Reviewer.
   - All CI checks (Pytest, Gitleaks, Semgrep, Trivy, Checkov, ZAP) must be green before merge.
2. **Delayed Task Escalation & Transparency**:
   - If a member is blocked for > 48 hours, an issue is tagged `status: blocked`.
   - The Team Lead (Hannah Amoaba Larbi) convenes an emergency sync to reassign or pair on the blocker without completing work silently.
   - Transparent git commits document collaborative pair-programming and remediation sessions.
3. **Live Oral Defence Alignment**:
   - Each member is designated as the primary subject-matter expert for their assigned toolchain during the 15-minute live oral presentation and 5-minute Q&A defence.
