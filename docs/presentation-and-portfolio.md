# CSSS 441 Week 10: Presentation, Demo Script & Portfolio Summaries
## Project 2: DevSecOps Pipeline with Security Gates

---

## 1. Five-Minute Demo Video Script (Minute-by-Minute Guide)

This script is structured to demonstrate all required course elements in exactly 5 minutes:

### [0:00 - 0:45] Introduction & Architecture Overview
- **Visual**: Show `README.md` and `docs/architecture.md` diagram.
- **Narration**:
  > "Hello, this is the demonstration of our CSSS 441 Project 2: an automated DevSecOps continuous integration and release pipeline with automated security gates. Our target application is a hardened Book Catalog with an integrated DevSecOps Security Operations dashboard. Our pipeline enforces defense-in-depth across the entire SDLC: from developer workstation pre-commit hooks, to static analysis with Semgrep and CodeQL, software composition analysis with OSV-Scanner and Trivy, container hardening with Checkov, dynamic DAST with OWASP ZAP, and cryptographic signing with Sigstore Cosign and SLSA provenance."

### [0:45 - 1:45] Target Application & Security Dashboard
- **Visual**: Open browser to `http://localhost:8000/` and `http://localhost:8000/security`.
- **Narration**:
  > "Here is our running application. On the main page, we have our responsive Book Catalog featuring parameterized search, filtering, server-side pagination, and role-protected CRUD modals. On `/security`, we have our live DevSecOps dashboard. It automatically ingests our security scorecard, displaying real-time pass/fail statuses for every gate, scan durations, and vulnerability severities. Notice our health probes at `/health/live` and `/health/ready`, and Prometheus metrics at `/metrics`."

### [1:45 - 3:15] The Security Bar: 3 Blocked Build Demonstrations
- **Visual**: Show GitHub Actions workflow runs or terminal evidence in `evidence/demonstrations/`.
- **Narration**:
  > "Per the course security bar, our pipeline automatically blocks commits with secrets, vulnerable dependencies, or unsigned artifacts:
  > 1. **Secret Scanning (Demo 1)**: When a developer accidentally commits an API key or synthetic token, Gitleaks halts the pipeline at Job 1 with exit code 1.
  > 2. **Vulnerable Dependency (Demo 2)**: When an outdated dependency like `urllib3 1.26.18` is introduced, OSV-Scanner and pip-audit flag CVE-2024-37891 and reject the pull request before any build occurs.
  > 3. **Unsigned Container (Demo 3)**: In our release workflow, our verification gate script cryptographically validates that the image has a valid Sigstore Cosign signature and SLSA provenance attestation. When an unsigned image is supplied, the release halts immediately."

### [3:15 - 4:15] Custom Semgrep Rules & Automated Gates
- **Visual**: Show `.semgrep/custom_rules.yml` and run `python scripts/run_gates.py` or `make gates`.
- **Narration**:
  > "We also engineered 5 custom Semgrep rules specifically targeting application vulnerabilities, including SQL injection, dangerous subprocess invocations with shell=True, dynamic eval execution, unsafe pickle deserialization, and wildcard CORS. Our automated test suite in `tests/semgrep/rule_tests.py` validates positive and negative test cases for every rule. Running our unified gate runner locally with `make gates` executes all linters, unit tests, custom Semgrep rules, SCA, and IaC checks in under 45 seconds."

### [4:15 - 5:00] Conclusion & DefectDojo Integration
- **Visual**: Show `scripts/import_reports.py` and `evidence/security-scorecard.json`.
- **Narration**:
  > "Finally, all scan artifacts—including Syft CycloneDX SBOMs, Trivy reports, and ZAP logs—are aggregated and imported into DefectDojo for centralized vulnerability management. Across our controlled failure scenarios, our Mean Time to Fix (MTTF) was 10.92 minutes. Thank you."

---

## 2. Fifteen-Minute Live Presentation Slide Outline

### Slide 1: Title & Team Roles
- Title: CSSS 441 Project 2 — DevSecOps Pipeline with Security Gates
- Presenters:
  1. **Hannah Amoaba Larbi** ([@hannahamoaba](https://github.com/hannahamoaba)) — Index: `1700237691` (Team Lead & Release Verification Engineer)
  2. **Stephen Kwadwo Duah** ([@thetravelerkweku-ops](https://github.com/thetravelerkweku-ops)) — Index: `1696334280` (Source Security & Secrets Engineer)
  3. **Othniel Kpakpo Saka** ([@jesu-henry](https://github.com/jesu-henry)) — Index: `1705408739` (AppSec & Static Analysis Engineer)
  4. **Fred Nkrumah** ([@Afrifar055-sketch](https://github.com/Afrifar055-sketch)) — Index: `1703603625` (Container & SCA Security Engineer)
  5. **Benjamin Essibo Ofori** ([@ben244294](https://github.com/ben244294)) — Index: `1693417365` (DAST & Vulnerability Operations Engineer)

### Slide 2: Problem Statement & DevSecOps Philosophy
- The challenge: Software supply chain attacks, credential leaks, and insecure container deployments.
- The solution: Shift-Left security, automated fail-closed gates, and cryptographic release verification.

### Slide 3: Target Application Architecture
- FastAPI Book Catalog + SQLite/PostgreSQL with Alembic migrations.
- Defensive security: HTTP security headers (CSP, nosniff, DENY), CSRF protection, rate limiting, and Kubernetes health probes.

### Slide 4: Threat Model & STRIDE Register
- Highlight 14 credible threats across 5 trust zones.
- Top mitigations: Gitleaks for THREAT-01, Custom Semgrep for THREAT-13/14, Cosign/SLSA for THREAT-09/10/11.

### Slide 5: The CI/CD Pipeline (GitHub Actions)
- Walkthrough of the 6-stage workflow: Lint & Secrets -> SAST -> SCA & IaC -> Container Build -> DAST -> Security Gate Evaluation.

### Slide 6: Static Application Security Testing (SAST)
- CodeQL workflow + 5 Custom Semgrep rules.
- Demonstrate rule test harness (`tests/semgrep/rule_tests.py`) proving 100% precision.

### Slide 7: Software Composition Analysis (SCA) & SBOMs
- Pinned dependencies with `pip-compile`.
- Dual scanning: OSV-Scanner + pip-audit + Aqua Trivy.
- CycloneDX SBOM generation for both source and container image using Anchore Syft.

### Slide 8: Container Hardening & IaC Security
- Multi-stage Docker build: unprivileged user (`appuser:10001`), read-only root filesystem, dropped Linux capabilities (`cap_drop: ALL`).
- Checkov policy validation on `Dockerfile` and `compose.yaml`.

### Slide 9: Ephemeral Staging & Dynamic DAST
- Automated staging launch via Docker Compose.
- Healthcheck polling before scan initiation.
- OWASP ZAP baseline scan with custom alert threshold rules (`.zap/rules.tsv`).
- Guaranteed cleanup teardown.

### Slide 10: Supply Chain Security (Cosign & SLSA)
- Keyless signing using Sigstore Cosign via GitHub Actions OIDC identity.
- SLSA build provenance attestations.
- Fail-closed verification gate (`scripts/verify_release.sh`).

### Slide 11: Controlled Failure Demonstrations & Security Bar
- Demonstration 1: Secret leak stopped by Gitleaks.
- Demonstration 2: Vulnerable package stopped by OSV-Scanner.
- Demonstration 3: Unsigned image stopped by verification script.

### Slide 12: Remediation Metrics & DefectDojo
- Mean Time to Fix (MTTF) analysis: 10.92 minutes.
- Automated vulnerability aggregation into DefectDojo using `scripts/import_reports.py`.

### Slide 13: Live Demonstration
- 2-minute live run of `make gates` and brief walkthrough of the UI and Security Dashboard.

### Slide 14: Residual Risk & Future Hardening
- Nightly base image scanning, authenticated DAST spidering, hardware token signing (FIPS 140-2).

### Slide 15: Conclusion & Q&A
- Summary of outcomes. Open for 5 minutes of questions.

---

## 3. Individual Portfolio Summaries (Resume Bullets & Student Records)

### Member 1: Hannah Amoaba Larbi (Index No: 1700237691 | [@hannahamoaba](https://github.com/hannahamoaba))
- **Role**: Team Lead & Release Verification Engineer
- **Role Summary**: Architected the multi-stage GitHub Actions CI/CD pipeline, configured Sigstore Cosign keyless container signing and SLSA build provenance attestations, authored the pre-deployment release verification gate (`scripts/verify_release.sh`), and directed overall system architecture.
- **Tools Used**: GitHub Actions, Sigstore Cosign, SLSA, Docker, FastAPI, SQLAlchemy, Alembic, Bash.
- **Resume Bullets**:
  - *Architected a multi-stage GitHub Actions DevSecOps pipeline with automated fail-closed security gates, enforcing keyless Sigstore Cosign signing and SLSA build provenance attestations on production container images.*
  - *Engineered an automated cryptographic release gate (`verify_release.sh`) validating SHA-256 digests and Fulcio OIDC certificates against Rekor transparency logs prior to deployment.*

### Member 2: Stephen Kwadwo Duah (Index No: 1696334280 | [@thetravelerkweku-ops](https://github.com/thetravelerkweku-ops))
- **Role**: Source Security & Secrets Engineer
- **Role Summary**: Implemented workstation pre-commit hooks and CI secret scanning with Gitleaks, established developer environment automation scripts (`scripts/setup.sh`), and authored secret rotation and incident response protocols.
- **Tools Used**: Gitleaks, Pre-commit, Git Hooks, Bash, PowerShell, Python.
- **Resume Bullets**:
  - *Implemented Shift-Left secret detection utilizing Gitleaks pre-commit hooks and mirrored GitHub Actions workflows, eliminating credential exposure risk across Git commit history.*
  - *Developed reproducible environment setup scripts (`setup.sh`) and secret rotation runbooks, automating linter configuration and developer security guardrails.*

### Member 3: Othniel Kpakpo Saka (Index No: 1705408739 | [@jesu-henry](https://github.com/jesu-henry))
- **Role**: AppSec & Static Analysis Engineer
- **Role Summary**: Authored 5 custom Semgrep rules with comprehensive unit test suites covering SQL injection, command execution, unsafe eval/exec, insecure deserialization, and wildcard CORS; tuned GitHub CodeQL workflows.
- **Tools Used**: Semgrep, CodeQL, AST, Python AST, YAML.
- **Resume Bullets**:
  - *Engineered 5 custom Semgrep static analysis rules targeting SQL injection, RCE, unsafe deserialization, and CORS flaws, validated by automated positive and negative test suites.*
  - *Configured and tuned GitHub CodeQL static analysis workflows to achieve zero false-positive alerts on weekly automated repository security scans.*

### Member 4: Fred Nkrumah (Index No: 1703603625 | [@Afrifar055-sketch](https://github.com/Afrifar055-sketch))
- **Role**: Container & SCA Security Engineer
- **Role Summary**: Built hardened multi-stage Docker container images with unprivileged user execution (`appuser:10001`), read-only rootfs, and dropped Linux capabilities; integrated Checkov, OSV-Scanner, Trivy, and Anchore Syft SBOM generation.
- **Tools Used**: Docker, Checkov, Trivy, OSV-Scanner, Anchore Syft, pip-compile, pip-audit.
- **Resume Bullets**:
  - *Hardened production container images through multi-stage builds, non-root user isolation (`appuser:10001`), read-only root filesystems, and Checkov Infrastructure-as-Code compliance.*
  - *Integrated dual-layer Software Composition Analysis (OSV-Scanner, Trivy, pip-audit) and automated CycloneDX SBOM generation into CI builds.*

### Member 5: Benjamin Essibo Ofori (Index No: 1693417365 | [@ben244294](https://github.com/ben244294))
- **Role**: DAST & Vulnerability Operations Engineer
- **Role Summary**: Orchestrated ephemeral staging test environments in CI, integrated automated OWASP ZAP baseline DAST scans, tuned alert threshold policies (`.zap/rules.tsv`), and built the DefectDojo vulnerability ingestion client (`scripts/import_reports.py`).
- **Tools Used**: OWASP ZAP, DefectDojo, Docker Compose, HTTPX, Python.
- **Resume Bullets**:
  - *Automated dynamic application security testing (DAST) by spinning up ephemeral staging containers in CI, executing OWASP ZAP scans, and ensuring clean teardown.*
  - *Built an automated Python vulnerability operations client (`import_reports.py`) to parse and ingest heterogeneous scanner telemetry directly into DefectDojo via REST API.*

---
*Official Course Resume Line*:  
> **"Built a DevSecOps pipeline (Semgrep, CodeQL, Trivy, Syft, ZAP, cosign) that generates SBOMs, signs images and blocks vulnerable or unsigned builds before deployment."**

