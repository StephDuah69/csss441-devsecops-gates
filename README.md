# CSSS 441 Software Security I — Project 2: DevSecOps Pipeline with Security Gates

[![CI Security Pipeline](https://github.com/csss441/csss441-devsecops-gates/actions/workflows/ci.yml/badge.svg)](https://github.com/csss441/csss441-devsecops-gates/actions/workflows/ci.yml)
[![CodeQL Analysis](https://github.com/csss441/csss441-devsecops-gates/actions/workflows/codeql.yml/badge.svg)](https://github.com/csss441/csss441-devsecops-gates/actions/workflows/codeql.yml)
[![Release Verification](https://github.com/csss441/csss441-devsecops-gates/actions/workflows/release.yml/badge.svg)](https://github.com/csss441/csss441-devsecops-gates/actions/workflows/release.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python: 3.13](https://img.shields.io/badge/Python-3.13-brightgreen.svg)](https://www.python.org/)

---

## 1. Project Purpose & Executive Summary

This repository delivers an end-to-end, functional **DevSecOps continuous integration and release pipeline with automated security gates**, developed for **CSSS 441: Software Security I**.

The system demonstrates how security controls can be integrated across every stage of the software delivery lifecycle:
1. **Developer Workstation (Shift-Left)**: Pre-commit secret scanning (Gitleaks) and code quality linting (Ruff).
2. **Static Application Security Testing (SAST)**: 5 custom Python API Semgrep rules with automated unit test suites, plus GitHub CodeQL.
3. **Software Composition Analysis (SCA)**: Pinned lockfile dependency scanning (OSV-Scanner) and filesystem vulnerability checks (Trivy).
4. **Infrastructure-as-Code & Container Security**: Dockerfile and Docker Compose misconfiguration scanning (Checkov), multi-stage hardened Docker image, and Syft CycloneDX SBOM generation.
5. **Dynamic Application Security Testing (DAST)**: Ephemeral staging deployment with automated readiness probing, OWASP ZAP baseline scanning, and guaranteed environment cleanup.
6. **Supply Chain Integrity & Trusted Releases**: Sigstore Cosign keyless container signing, SLSA build provenance attestations, and immutable SHA-256 digest release verification gates.
7. **Vulnerability Operations**: Automated ingestion of scanner reports into DefectDojo.

---

## 2. Architecture Overview

```mermaid
flowchart LR
    DEV[Developer Code] --> PRE[Pre-Commit Hooks]
    PRE --> PR[Pull Request]
    PR --> CI[GitHub Actions CI Gates]
    subgraph Security Gates
        CI --> G1[Gitleaks Secret Gate]
        CI --> G2[Semgrep SAST & Custom Rules]
        CI --> G3[OSV-Scanner & Trivy SCA]
        CI --> G4[Checkov IaC & Hardened Docker]
        CI --> G5[OWASP ZAP Dynamic DAST]
    end
    G1 & G2 & G3 & G4 & G5 --> GATE_EVAL{All Gates Green?}
    GATE_EVAL -->|Yes| MERGE[Merge to Main]
    GATE_EVAL -->|No| BLOCK[Build Blocked]
    MERGE --> REL[Protected Release Workflow]
    REL --> COSIGN[Cosign Keyless Signing]
    REL --> SLSA[SLSA Provenance Attestation]
    COSIGN & SLSA --> VERIFY{Verify Digest & Signature}
    VERIFY -->|Verified| PROD[Production Registry / GHCR]
    VERIFY -->|Failed| ABORT[Release Halted]
```

Detailed architectural diagrams and trust boundaries are documented in [`docs/architecture.md`](docs/architecture.md).

---

## 3. Repository Directory Structure

```text
csss441-devsecops-gates/
├── .github/
│   └── workflows/
│       ├── ci.yml               # Integrated 18-stage DevSecOps CI pipeline
│       ├── codeql.yml           # Scheduled and PR CodeQL static analysis
│       └── release.yml          # Protected release with Cosign & SLSA provenance
├── .semgrep/
│   └── custom_rules.yml         # 5 custom Semgrep rules with CWE/OWASP metadata
├── .zap/
│   └── rules.tsv                # OWASP ZAP baseline scan alert policies
├── alembic/                 # Alembic database schema migrations
│   ├── env.py
│   └── versions/            # Version-controlled schema migrations
├── app/
│   ├── __init__.py
│   ├── main.py              # Application entrypoint & middleware assembly
│   ├── database.py          # SQLAlchemy 2.x engine & session management
│   ├── models.py            # Book entity ORM models
│   ├── schemas.py           # Pydantic v2 validation models
│   ├── security.py          # Security headers, CSRF, admin auth & rate limiting
│   ├── routers/
│   │   ├── books.py         # RESTful catalog endpoints
│   │   ├── catalog_pages.py # HTML server-rendered catalog UI (/)
│   │   ├── security_dashboard.py # DevSecOps dashboard (/security)
│   │   └── health.py        # /health, /health/live, /health/ready probes
│   ├── services/
│   │   ├── book_service.py  # Parameterized DB queries & pagination
│   │   ├── scorecard_service.py # Security scorecard & report parser
│   │   └── seed_service.py  # Idempotent database seeder
│   └── templates/
│       ├── base.html        # Responsive Tailwind layout with security focus
│       ├── index.html       # Book collection, search, filter, and CRUD modals
│       └── security/
│           └── dashboard.html # Security gate matrix & vulnerability charts
├── tests/
│   ├── test_app.py          # Baseline unit & integration tests
│   ├── test_enhanced.py     # Comprehensive UI, CRUD, CSRF, and security tests
│   └── semgrep/
│       └── rule_tests.py    # Positive and negative assertions for custom rules
├── scripts/
│   ├── setup.sh             # Environment initialization script
│   ├── seed_db.py           # CLI database seeder
│   ├── run_gates.py         # Unified security gate runner (make gates)
│   ├── run_security_checks.sh # Bash gate runner
│   ├── verify_release.sh    # Cryptographic signature & provenance verifier
│   └── import_reports.py    # DefectDojo scan ingestion API client
├── docs/
│   ├── architecture.md          # DFD, component flows, and trust zones
│   ├── threat-model.md          # 14 STRIDE threats with risk ratings and controls
│   ├── security-policy.md       # Gate failure thresholds and waiver procedures
│   ├── testing-plan.md          # Comprehensive verification matrix
│   ├── remediation-log.md       # 3 controlled demonstrations and MTTF calculation
│   ├── evidence-log.csv         # Structured timestamps and audit trail
│   ├── implementation-guide.md  # Academic evaluation and reproduction guide
│   └── contribution-records.md  # 5-member team responsibility matrix
├── evidence/
│   └── README.md                # Demonstration evidence index
├── reports/
│   └── .gitkeep                 # Scanner reports destination
├── .dockerignore                # Minimal build context exclusions
├── .gitignore                   # Secrets and build artifact exclusions
├── .gitleaks.toml               # Custom Gitleaks rules and strict allowlist
├── .pre-commit-config.yaml      # Pinned pre-commit hooks
├── Dockerfile                   # Multi-stage hardened non-root container
├── compose.yaml                 # Hardened Compose setup with dropped capabilities
├── Makefile                     # Cross-platform developer shortcuts
├── requirements.in              # Abstract runtime requirements
├── requirements.txt             # Pinned runtime dependencies via pip-compile
├── requirements-dev.in          # Abstract development requirements
├── requirements-dev.txt         # Pinned dev dependencies via pip-compile
└── LICENSE                      # MIT License
```

---

## 4. Prerequisites & Quick Installation

### Prerequisites
- Python 3.11+ (Python 3.13 recommended)
- Git 2.30+
- Docker & Docker Compose

### Quickstart (One-Command Setup)
```bash
# Clone the repository
git clone https://github.com/csss441/csss441-devsecops-gates.git
cd csss441-devsecops-gates

# Setup environment and dependencies
bash scripts/setup.sh
# Or on Windows using make:
make setup
```

---

## 5. Local Testing & Verification Commands

| Command | Tool | Purpose |
| :--- | :--- | :--- |
| `make test` | Pytest | Runs 25 unit, integration, and security tests |
| `make lint` | Ruff | Runs security linter and format validation |
| `make format` | Ruff | Automatically formats Python codebase |
| `make gates` | Unified Runner | Executes all security gates and generates scorecard |
| `make migrate` | Alembic | Applies database migrations (`alembic upgrade head`) |
| `make seed` | Python | Safely seeds sample books into catalog database |
| `make run` | Uvicorn | Starts FastAPI service at `http://localhost:8000` |
| `make docker-build` | Docker | Builds hardened multi-stage container image |
| `make docker-run` | Docker Compose | Starts hardened container with read-only rootfs |

---

## 6. Custom Semgrep Security Rules

Located in [`.semgrep/custom_rules.yml`](.semgrep/custom_rules.yml):
1. **`csss441.python.sql-string-interpolation`**: Detects SQL injection caused by dynamic f-string, format, or % concatenation in database execute statements.
2. **`csss441.python.dangerous-subprocess-shell-true`**: Detects dangerous command injection vectors caused by `subprocess.run(..., shell=True)`.
3. **`csss441.python.unsafe-dynamic-eval`**: Detects arbitrary code execution vulnerabilities via `eval()` and `exec()`.
4. **`csss441.python.unsafe-pickle-deserialization`**: Detects insecure deserialization via `pickle.loads()` or `pickle.load()`.
5. **`csss441.python.wildcard-cors-with-credentials`**: Detects overly permissive CORS origins (`allow_origins=['*']`) paired with `allow_credentials=True`.

Unit tests with positive (`# ruleid`) and negative (`# ok`) assertions are in [`tests/semgrep/rule_tests.py`](tests/semgrep/rule_tests.py).

---

## 7. Controlled Blocked-Build Demonstrations

Three controlled demonstrations prove that security gates deterministically halt unsafe builds:

1. **Demonstration 1 (Exposed Secret)**: Synthetic credential introduced; Gitleaks fails CI job `Lint, Unit Tests & Secrets`; commit removed; build verified green (MTTF: 6.5 min).
2. **Demonstration 2 (Vulnerable Dependency)**: Known CVE package injected; OSV-Scanner fails CI job `OSV-Scanner, Trivy & Checkov`; dependency upgraded; build verified green (MTTF: 14.0 min).
3. **Demonstration 3 (Unsigned Artifact)**: Unsigned container digest supplied; `scripts/verify_release.sh` halts release; Sigstore keyless OIDC signing & SLSA provenance verified; release approved (MTTF: 12.25 min).

Full details and calculations are documented in [`docs/remediation-log.md`](docs/remediation-log.md) and [`docs/evidence-log.csv`](docs/evidence-log.csv).

---

## 8. DefectDojo Vulnerability Ingestion

Run the automated ingestion client to sync scanner outputs to your DefectDojo server:
```bash
export DEFECTDOJO_URL="http://localhost:8080"
export DEFECTDOJO_TOKEN="your-token"
export DEFECTDOJO_ENGAGEMENT_ID="1"

python scripts/import_reports.py --reports-dir reports/
```

---

## 9. Academic Contribution & Team Ownership

This project was developed by a five-member engineering team for **CSSS 441: Software Security I**:

### 👥 Project Contributors

| Contributor | GitHub Profile | Index No. | Assigned Role | Primary Technical Domain |
| :--- | :--- | :--- | :--- | :--- |
| <a href="https://github.com/hannahamoaba"><img src="https://github.com/hannahamoaba.png" width="44" height="44" style="border-radius:50%;" alt="hannahamoaba"/><br/>**Hannah Amoaba Larbi**</a> | [@hannahamoaba](https://github.com/hannahamoaba) | `1700237691` | **Team Lead** | CI/CD Pipeline Orchestration, Cosign, SLSA |
| <a href="https://github.com/thetravelerkweku-ops"><img src="https://github.com/thetravelerkweku-ops.png" width="44" height="44" style="border-radius:50%;" alt="thetravelerkweku-ops"/><br/>**Stephen Kwadwo Duah**</a> | [@thetravelerkweku-ops](https://github.com/thetravelerkweku-ops) | `1696334280` | **Source Security** | Gitleaks Hooks, Secret Detection, Setup |
| <a href="https://github.com/jesu-henry"><img src="https://github.com/jesu-henry.png" width="44" height="44" style="border-radius:50%;" alt="jesu-henry"/><br/>**Othniel Kpakpo Saka**</a> | [@jesu-henry](https://github.com/jesu-henry) | `1705408739` | **AppSec Engineer** | 5 Custom Semgrep Rules, CodeQL, AST Tests |
| <a href="https://github.com/Afrifar055-sketch"><img src="https://github.com/Afrifar055-sketch.png" width="44" height="44" style="border-radius:50%;" alt="Afrifar055-sketch"/><br/>**Fred Nkrumah**</a> | [@Afrifar055-sketch](https://github.com/Afrifar055-sketch) | `1703603625` | **Container & SCA** | Hardened Docker, Checkov, Trivy, Syft SBOMs |
| <a href="https://github.com/ben244294"><img src="https://github.com/ben244294.png" width="44" height="44" style="border-radius:50%;" alt="ben244294"/><br/>**Benjamin Essibo Ofori**</a> | [@ben244294](https://github.com/ben244294) | `1693417365` | **DAST & SecOps** | OWASP ZAP DAST, Ephemeral Staging, DefectDojo |

---

### Detailed Responsibilities:

- **Hannah Amoaba Larbi** ([@hannahamoaba](https://github.com/hannahamoaba)) — Index: `1700237691`
  - *Responsibilities*: CI/CD Pipeline Orchestration, Sigstore Cosign keyless signing, SLSA build provenance attestations, release verification gates, and architectural documentation.
- **Stephen Kwadwo Duah** ([@thetravelerkweku-ops](https://github.com/thetravelerkweku-ops)) — Index: `1696334280`
  - *Responsibilities*: Gitleaks pre-commit hooks, repository secret detection, CI secret scanning policies, secret rotation protocols, and developer onboarding automation.
- **Othniel Kpakpo Saka** ([@jesu-henry](https://github.com/jesu-henry)) — Index: `1705408739`
  - *Responsibilities*: Custom Semgrep rules (SQLi, RCE, eval, pickle, CORS), automated positive/negative rule test suites (`rule_tests.py`), and GitHub CodeQL integration.
- **Fred Nkrumah** ([@Afrifar055-sketch](https://github.com/Afrifar055-sketch)) — Index: `1703603625`
  - *Responsibilities*: Multi-stage Dockerfile hardening (non-root `appuser:10001`, read-only rootfs), Compose constraints, Checkov IaC scanning, OSV-Scanner, Trivy, and Anchore Syft CycloneDX SBOM generation.
- **Benjamin Essibo Ofori** ([@ben244294](https://github.com/ben244294)) — Index: `1693417365`
  - *Responsibilities*: Ephemeral staging container orchestration, OWASP ZAP dynamic baseline scanning, alert policy tuning (`.zap/rules.tsv`), DefectDojo ingestion client, and remediation/MTTF tracking.

See [`docs/contribution-records.md`](docs/contribution-records.md) for full responsibility matrices, review pairings, and task deliverables.
