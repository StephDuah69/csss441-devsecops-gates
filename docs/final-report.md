# CSSS 441 Software Security I: Final Technical Report
## Project 2: DevSecOps Continuous Integration Pipeline with Automated Security Gates

**Course**: CSSS 441 Software Security I  
**Semester**: Fall 2026  
**Repository**: `csss441-devsecops-gates`  
**Team Members**:
- **Hannah Amoaba Larbi** (Index: `1700237691`) — Team Lead & Release Verification
- **Stephen Kwadwo Duah** (Index: `1696334280`) — Source Security & Secrets
- **Othniel Kpakpo Saka** (Index: `1705408739`) — AppSec & Static Analysis
- **Fred Nkrumah** (Index: `1703603625`) — Container & SCA Security
- **Benjamin Essibo Ofori** (Index: `1693417365`) — DAST & Vulnerability Operations  
**Target Application**: Hardened Book Catalog & DevSecOps Security Operations Dashboard  
**Submission Date**: October 2026  

---

## Executive Summary

Modern software organizations face growing risks from software supply chain attacks, vulnerable open-source dependencies, embedded hardcoded credentials, and configuration drifts in cloud-native infrastructure. The objective of **Project 2** was to design, implement, and rigorously verify an end-to-end DevSecOps continuous integration and release pipeline that automatically enforces automated security gates at every stage of the Software Development Life Cycle (SDLC).

This report presents the architecture, threat modeling, security engineering controls, automated verification evidence, and operational results of the `csss441-devsecops-gates` system. Using a real, production-ready FastAPI book catalog application backed by an SQLite/PostgreSQL persistent database with Alembic migrations, our pipeline demonstrates automated defense-in-depth:
1. **Pre-commit and Developer Workstation**: Local Gitleaks secret detection and Ruff formatting/linting hooks.
2. **Static Application Security Testing (SAST)**: GitHub CodeQL and 5 custom-engineered Semgrep rules addressing injection, unsafe deserialization, command execution, and CORS misconfigurations.
3. **Software Composition Analysis (SCA)**: Dual-layer dependency verification with Google OSV-Scanner, pip-audit, and Aqua Trivy filesystem scanning.
4. **Container & Infrastructure-as-Code Hardening**: Checkov IaC security inspection and multi-stage, non-root (`appuser:10001`), read-only container rootfs builds generating CycloneDX Software Bills of Materials (SBOMs) via Anchore Syft.
5. **Dynamic Application Security Testing (DAST)**: Automated ephemeral staging cluster launching with health probes, baseline OWASP ZAP vulnerability assessments, and automated cleanup.
6. **Supply Chain Integrity & Provenance**: Sigstore Cosign keyless digital signing via GitHub Actions OIDC identity tokens, SLSA build provenance attestations, and immutable SHA-256 digest release gates.
7. **Vulnerability Operations**: Automated ingestion of machine-readable telemetry into DefectDojo.

The pipeline successfully satisfies the course's strict security bar: commits containing planted secrets, known-vulnerable dependencies, or unsigned container images are stopped automatically with clear root-cause diagnostic feedback.

---

## 1. System Architecture & Design

### 1.1 Target Application Architecture
The target application is a responsive, hardened Book Catalog and DevSecOps Security Dashboard built with FastAPI, SQLAlchemy 2.x, Alembic, and Jinja2 templates styled with Tailwind CSS. The system provides:
- **Catalog Management (`/`)**: Parameterized search (by title, author, genre, ISBN), allowlisted sorting, server-side pagination, and role-protected CRUD endpoints (`/api/books`).
- **DevSecOps Security Dashboard (`/security`)**: Real-time rendering of automated security scorecard metrics, gate status summaries, and vulnerability severity counts.
- **Reliability & Observability**: Kubernetes-standard health probes (`/health/live` process check, `/health/ready` database ping) and Prometheus scraping metrics (`/metrics`).
- **Defensive HTTP Middleware**: Automated injection of `Content-Security-Policy`, `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Strict-Transport-Security`, double-submit CSRF cookie protection, and SlowAPI rate limiting (60 requests/minute).

### 1.2 Multi-Stage Pipeline Architecture & Trust Boundaries
The pipeline defines four distinct trust zones across the SDLC:

| Trust Zone | Environment | Components | Trust Level | Security Controls Enforced |
| :--- | :--- | :--- | :--- | :--- |
| **Zone 0** | Developer Machine | Local Git clone, virtualenv, editor | Untrusted / Low | Pre-commit hooks (`gitleaks`, `ruff`), branch protection rules |
| **Zone 1** | GitHub Actions Runner | Ephemeral Ubuntu VM runner | Semi-Trusted | Minimum token permissions (`contents: read`), secret scanning, custom SAST, SCA, IaC linting |
| **Zone 2** | Ephemeral Staging | Containerized API in test sandbox | Controlled Sandbox | Non-root user (`appuser:10001`), read-only rootfs, dropped capabilities, ZAP DAST |
| **Zone 3** | Artifact Registry & Release | GHCR, Sigstore, SLSA attestations | High Trust | Keyless cryptographic signing, immutable SHA-256 digest pinning, provenance verification |
| **Zone 4** | Vulnerability Management | DefectDojo Server | Protected Internal | Role-based access control (RBAC), scoped API tokens, findings deduplication |

```
[Zone 0: Workstation] -> Pre-commit (Gitleaks + Ruff)
       | (Git Push / PR)
       v
[Zone 1: GitHub CI]   -> Pytest (25 Tests) -> Semgrep SAST -> CodeQL -> OSV-Scanner -> Trivy FS -> Checkov IaC
       | (All Gates Pass)
       v
[Zone 2: Staging]     -> Multi-stage Build -> Trivy Image -> Syft CycloneDX SBOM -> Ephemeral Staging -> ZAP DAST
       | (Merge to Main / Release Tag)
       v
[Zone 3: Release]     -> Push GHCR -> Sigstore Cosign (OIDC) -> SLSA Provenance -> scripts/verify_release.sh
       | (Telemetry Stream)
       v
[Zone 4: Ops]         -> DefectDojo Automated Ingestion (scripts/import_reports.py)
```

---

## 2. Threat Modeling & Risk Assessment (STRIDE)

In accordance with course milestones, the system was threat-modeled using the **STRIDE** methodology. Fourteen credible threats were identified, prioritized, and mapped to concrete technical controls:

| Threat ID | Asset | STRIDE Category | Threat Description | Initial Risk | Implemented Technical Control | Residual Risk |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **THREAT-01** | Git Repo | Information Disclosure | Secret leakage in commits | **Critical** | Gitleaks pre-commit + CI gate | Low |
| **THREAT-02** | CI Runner | Tampering / EoP | Malicious fork PR code execution | **High** | Restricted PR permissions (`contents: read`) | Low |
| **THREAT-03** | Workflows | Elevation of Privilege | Excessive GitHub token permissions | **High** | Scoped least-privilege token permissions | Low |
| **THREAT-04** | Python App | Tampering | Outdated / vulnerable dependencies | **Critical** | Pinned lockfiles, OSV-Scanner, pip-audit | Low |
| **THREAT-05** | CI Defs | Tampering | Unauthorized workflow tampering | **Medium** | Protected branch rules on `main` | Low |
| **THREAT-06** | Container | Elevation of Privilege | Root container breakout | **High** | Non-root `appuser:10001`, read-only rootfs, `cap_drop: ALL` | Low |
| **THREAT-07** | Staging | Information Disclosure | Public exposure of staging instance | **Medium** | Localhost binding only (`127.0.0.1:8000`), ephemeral teardown | Low |
| **THREAT-08** | Scanners | Repudiation / Tampering | Silent scanner bypass (`continue-on-error`) | **High** | Fail-closed evaluation gate (`security-gate` job) | Low |
| **THREAT-09** | Registry | Tampering | Container image tampering in registry | **High** | Cosign keyless signature + SHA-256 digest pinning | Low |
| **THREAT-10** | Sigstore | Spoofing | Signing identity spoofing | **Medium** | Regex verification of OIDC workflow identity | Low |
| **THREAT-11** | Build | Tampering | Missing / forged build provenance | **High** | SLSA provenance generation via GitHub Actions attestation | Low |
| **THREAT-12** | API App | Denial of Service | Query string / payload resource exhaustion | **High** | Pydantic regex/length bounds + SlowAPI rate limiting | Low |
| **THREAT-13** | Database | Tampering / Info Disc | SQL Injection via string formatting | **Critical** | Custom Semgrep rule + SQLAlchemy parameterized queries | Low |
| **THREAT-14** | OS Shell | Elevation of Privilege | Remote Command Execution via shell=True | **Critical** | Custom Semgrep rule blocking subprocess `shell=True` | Low |

---

## 3. Security Engineering Controls

### 3.1 Pre-Commit Hooks and Secrets Prevention
Secret scanning is shifted left to the developer machine using `.pre-commit-config.yaml` and `.gitleaks.toml`. The hook scans staged diffs for high-entropy tokens, private keys, AWS tokens, and custom synthetic secrets (`csss441-synthetic-test-token`). The identical check is mirrored in CI Job 1, preventing developers from bypassing local hooks.

### 3.2 Custom Semgrep Static Analysis Rules
Five custom Semgrep rules were authored to enforce secure application coding standards:
1. `csss441.python.sql-string-interpolation` (CWE-89): Detects dynamic SQL construction using f-strings or `.format()`.
2. `csss441.python.dangerous-subprocess-shell-true` (CWE-78): Blocks `subprocess.run(..., shell=True)` invocations that permit command chaining.
3. `csss441.python.unsafe-dynamic-eval` (CWE-95): Identifies dangerous usage of `eval()` and `exec()`.
4. `csss441.python.unsafe-pickle-deserialization` (CWE-502): Detects insecure object deserialization via `pickle.loads()`.
5. `csss441.python.wildcard-cors-with-credentials` (CWE-942): Flags wildcard origins (`allow_origins=["*"]`) combined with `allow_credentials=True`.

Each custom rule is verified via `tests/semgrep/rule_tests.py` containing both positive (`# ruleid`) and negative (`# ok`) assertions.

### 3.3 Container Hardening & IaC Compliance
The `Dockerfile` employs multi-stage compilation:
- **Build Stage**: Installs compiler tools, wheels, and compiles dependencies into `/install`.
- **Runtime Stage**: Copies pre-built wheels onto a minimal `python:3.13-slim-bookworm` base. Creates an unprivileged group and user (`appuser:10001`), configures `HEALTHCHECK` with `/health/live`, and drops all shell utilities.
- **Compose Security**: `compose.yaml` enforces `read_only: true`, `security_opt: [no-new-privileges:true]`, `cap_drop: [ALL]`, CPU limits (0.5 cores), and memory limits (256MB). Checkov verifies these controls with 0 violations.

### 3.4 Cryptographic Supply Chain Integrity
Container releases enforce three-factor cryptographic verification before deployment:
1. **Immutable SHA-256 Digest**: Images must be referenced by digest (`@sha256:...`), rejecting mutable tags.
2. **Sigstore Cosign Keyless Signing**: Builds exchange GitHub Actions OIDC identity tokens for short-lived Fulcio certificates recorded in the Rekor transparency log.
3. **SLSA Build Provenance**: GitHub's `actions/attest-build-provenance` signs the build predicate, recording builder identity and source commit.
4. **Pre-Deployment Gate Script (`scripts/verify_release.sh`)**: Verifies signature, issuer, and provenance before container release.

---

## 4. Verification Evidence & Controlled Failure Demonstrations

To satisfy the course security bar, three controlled demonstrations were conducted. In each demo, a security violation was deliberately introduced, verified to fail the automated gate, remediated, and re-verified.

### Demonstration 1: Secret Leakage Gate (Gitleaks)
- **Violation**: Planted synthetic token `csss441_test_token = "csss441-demo-synthetic-credential-value-99"` committed to branch.
- **Outcome**: Gitleaks CI Job 1 immediately failed with Exit Code 1.
- **Remediation**: Token removed and Git history cleaned.
- **Elapsed Time to Fix**: 6.5 minutes.

### Demonstration 2: Known Vulnerable Dependency Gate (OSV-Scanner / pip-audit)
- **Violation**: Artificially downgraded `urllib3==1.26.18` (afflicted by CVE-2024-37891, CVSS 7.5).
- **Outcome**: OSV-Scanner and pip-audit failed the SCA gate with high-severity alert.
- **Remediation**: Pinned `urllib3 >= 2.2.2` in `requirements.in` and recompiled via `pip-compile`.
- **Elapsed Time to Fix**: 14.0 minutes.

### Demonstration 3: Unsigned Container Release Gate (Cosign & SLSA)
- **Violation**: Attempted release of an unsigned container image digest.
- **Outcome**: `scripts/verify_release.sh` rejected the digest with exit code 1 (`Cosign signature verification failed`).
- **Remediation**: Executed official release workflow with OIDC signing and SLSA provenance attestation.
- **Elapsed Time to Fix**: 12.25 minutes.

### Mean Time to Fix (MTTF) Metric
$$\text{MTTF} = \frac{6.5 + 14.0 + 12.25}{3} = \mathbf{10.92\text{ minutes (655 seconds)}}$$

---

## 5. Local Unified Gate Runner & Automated Test Suite

A standalone, local unified gate runner (`scripts/run_gates.py` and `make gates`) was created to mirror all CI security checks locally without requiring cloud execution:

```text
=================================================================
                     GATE SUMMARY                     
=================================================================
Check                               Status       Duration
-----------------------------------------------------------------
Gitleaks Secret Scan                PASS/SKIP    0.04s
Ruff Linter                         PASS         0.04s
Ruff Code Formatter                 PASS         0.04s
Pytest Test Suite                   PASS         2.91s
Semgrep Application Scan            PASS         9.04s
pip-audit Dependency Audit          PASS         29.66s
Checkov Container & IaC             PASS         10.50s
-----------------------------------------------------------------
Overall Result: PASS
Scorecard Saved: evidence/security-scorecard.json
=================================================================
```

Automated Pytest suite results: **25 passed, 0 failures in 1.58s** across both baseline and enhanced test suites.

---

## 6. Team Contributions & Responsibilities

| Student Name | Student Index | Primary Role | Key Contributions | Tools Mastered |
| :--- | :--- | :--- | :--- | :--- |
| **Hannah Amoaba Larbi** | `1700237691` | Team Lead & Release Verification Engineer | CI/CD pipeline orchestration, Sigstore Cosign keyless signing, SLSA build provenance attestations, `verify_release.sh`, FastAPI application architecture. | GitHub Actions, Cosign, SLSA, Docker, FastAPI, SQLAlchemy |
| **Stephen Kwadwo Duah** | `1696334280` | Source Security & Secrets Engineer | Gitleaks pre-commit hooks, CI secret scanning configuration, developer environment setup automation (`setup.sh`), secret rotation protocols. | Gitleaks, Pre-commit, Git hooks, Bash, PowerShell |
| **Othniel Kpakpo Saka** | `1705408739` | AppSec & Static Analysis Engineer | 5 custom Semgrep SAST rules, Semgrep positive/negative rule test harness (`rule_tests.py`), GitHub CodeQL static analysis tuning. | Semgrep, CodeQL, AST, Python typing, YAML |
| **Fred Nkrumah** | `1703603625` | Container & SCA Security Engineer | Multi-stage hardened Dockerfile, Compose resource constraints, OSV-Scanner, Trivy (FS/Image) scanning, Checkov IaC policies, Anchore Syft SBOMs. | Dockerfile, Checkov, Trivy, OSV-Scanner, Syft, pip-compile |
| **Benjamin Essibo Ofori** | `1693417365` | DAST & Vulnerability Operations Engineer | Ephemeral staging environment orchestration in CI, OWASP ZAP baseline scan alert policies (`rules.tsv`), DefectDojo API ingestion client (`import_reports.py`), MTTF tracking. | OWASP ZAP, DefectDojo, HTTPX, Docker Compose, Python |

---

## 7. Conclusion & Residual Risk Assessment

The `csss441-devsecops-gates` project successfully achieves all requirements outlined in the CSSS 441 Software Security I specification for Project 2. By enforcing automated, fail-closed gates across every SDLC phase, the pipeline guarantees that code cannot be merged or released if it contains exposed secrets, vulnerable dependencies, insecure IaC templates, or unverified container signatures.

### Residual Risks & Future Work:
1. **Zero-Day Vulnerabilities in Upstream Base Images**: Even minimal base images (`python:3.13-slim`) may contain unpatched vulnerabilities prior to upstream Debian publication. Continuous Trivy scanning on a nightly cron mitigates this risk.
2. **DAST Surface Coverage**: The OWASP ZAP baseline scan runs in passive mode. Future enhancements could implement authenticated active scans covering admin-only endpoints.
3. **Hardware Key Attestations**: The pipeline utilizes cloud OIDC keyless signing. Organizations requiring FIPS 140-2 Level 3 compliance could integrate hardware security modules (HSM) or YubiKey signing.

---
*Report certified complete and verified against live test runs and automated scorecard evidence.*

