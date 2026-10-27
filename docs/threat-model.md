# STRIDE Threat Model & Security Risk Assessment

## 1. Methodology & Risk Matrix

This threat model applies the **STRIDE** methodology (**S**poofing, **T**ampering, **R**epudiation, **I**nformation Disclosure, **D**enial of Service, **E**levation of Privilege) across all architectural components of the CSSS 441 DevSecOps pipeline and target application.

### Qualitative Risk Matrix
Risk is evaluated as a function of **Likelihood** (Low, Medium, High) and **Impact** (Low, Medium, High):

| Likelihood \ Impact | Low | Medium | High |
| :--- | :--- | :--- | :--- |
| **High** | Medium Risk | High Risk | **Critical Risk** |
| **Medium** | Low Risk | Medium Risk | **High Risk** |
| **Low** | Low Risk | Low Risk | **Medium Risk** |

---

## 2. Comprehensive STRIDE Threat Register (14 Credible Threats)

| ID | Component / Asset | STRIDE Category | Threat Description | Likelihood | Impact | Initial Risk | Proposed Security Control | Verification Method | Residual Risk |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **THREAT-01** | Git Repository / Workstation | **Information Disclosure** | **Secret Leakage**: Developer accidentally commits API keys, tokens, or private signing keys into Git history. | High | High | **Critical** | Local Gitleaks pre-commit hook + Gitleaks CI scanning job with strict blocking gate. | Run Gitleaks detect on commit/PR; Demonstration 1 synthetic token test. | Low |
| **THREAT-02** | GitHub CI Runner | **Tampering / Elevation of Privilege** | **Malicious Pull Requests**: External PR author submits malicious code or tests designed to run arbitrary commands in CI. | Medium | High | **High** | Restricted PR permissions (`contents: read`), require approvals for first-time contributors, isolate secrets. | Verify fork PR workflow execution context cannot read production secrets. | Low |
| **THREAT-03** | GitHub Actions Workflow | **Elevation of Privilege** | **Excessive CI Permissions**: Workflows run with default broad write permissions allowing repository takeover. | Medium | High | **High** | Least-privilege top-level workflow permissions block (`contents: read`, only explicit token grants per job). | CodeQL analysis & Checkov scan of workflow files. | Low |
| **THREAT-04** | Python Application / Wheels | **Tampering** | **Vulnerable Dependencies**: Project imports third-party packages with known CVEs/RCE flaws. | High | High | **Critical** | Pinned `requirements.txt` via `pip-compile` + OSV-Scanner and Trivy SCA gates. | Demonstration 2: Injecting vulnerable package and asserting CI failure. | Low |
| **THREAT-05** | `.github/workflows/` | **Tampering** | **Malicious Workflow Changes**: Attacker modifies CI workflow definitions to bypass security gates. | Low | High | **Medium** | Protected branch rules on `main` requiring mandatory peer review and branch protection. | Pull request review requirement and CodeQL workflow scanning. | Low |
| **THREAT-06** | Docker Container | **Elevation of Privilege** | **Container Misconfiguration**: Container runs as root with writable rootfs and excessive Linux capabilities. | Medium | High | **High** | Hardened Dockerfile: unprivileged `appuser:10001`, `read_only: true`, `cap_drop: [ALL]`, `no-new-privileges:true`. | Checkov container scan + inspect container runtime user (`id -u`). | Low |
| **THREAT-07** | Ephemeral Staging | **Information Disclosure** | **Staging Exposure**: Test instance exposed to public internet during DAST scanning. | Medium | Medium | **Medium** | Localhost binding only (`127.0.0.1:8000`), ephemeral runtime, and guaranteed cleanup step (`docker compose down -v`). | Verify network interface binding and post-job teardown in CI logs. | Low |
| **THREAT-08** | CI Security Scanners | **Repudiation / Tampering** | **Scanner Failure / Silent Bypass**: Tool errors or crashes but returns exit code 0 (`continue-on-error: true`), masking vulnerabilities. | Medium | High | **High** | Fail-closed gate logic: explicit check of upstream job outcomes; no unreviewed `continue-on-error`. | Intentional synthetic violation tests; verify job failure propagates. | Low |
| **THREAT-09** | GHCR Registry | **Tampering** | **Artifact Tampering**: Attacker replaces image layers or tags in registry with a backdoored image. | Medium | High | **High** | Release verification gate verifies immutable SHA-256 digest + Sigstore Cosign signature before release. | Demonstration 3: Attempting to verify modified or unsigned image digest. | Low |
| **THREAT-10** | Sigstore / OIDC | **Spoofing** | **Signing-Identity Abuse**: Untrusted repository or unofficial workflow signs malicious container image. | Low | High | **Medium** | Cosign verification strictly matches certificate identity regex against official repository workflow and OIDC issuer. | Verification script asserts exact workflow identity pattern and issuer. | Low |
| **THREAT-11** | Build Pipeline | **Tampering** | **Missing Provenance**: Image pushed without verifiable build history, source commit, and builder identity. | Medium | High | **High** | SLSA build provenance attestation generated via GitHub official attestation action; verified by `gh attestation verify`. | Run release verification script without attestation to prove failure. | Low |
| **THREAT-12** | FastAPI Application | **Denial of Service** | **Resource Exhaustion**: Attacker floods search endpoint with gigantic query strings or excessive concurrent requests. | High | Medium | **High** | Input validation on `q` (max_length=50, regex pattern), container CPU/memory limits (`256MB`, `0.5 CPUs`). | Unit tests with 51+ char strings; load check within resource bounds. | Low |
| **THREAT-13** | Database / Query Layer | **Tampering / Information Disclosure** | **SQL Injection**: Code dynamically interpolates unsanitized parameters into database queries. | High | High | **Critical** | Custom Semgrep rule `csss441.python.sql-string-interpolation` blocking direct f-string/format SQL in CI. | Semgrep positive/negative rule tests; SAST scan block on violation. | Low |
| **THREAT-14** | Operating System Shell | **Elevation of Privilege** | **OS Command Injection**: Application invokes `subprocess` with `shell=True` on dynamic input. | High | High | **Critical** | Custom Semgrep rule `csss441.python.dangerous-subprocess-shell-true` blocking `shell=True` invocations. | Semgrep positive/negative rule tests; CI gate fails on violation. | Low |

---

## 3. Prioritized Security Controls Summary

1. **Shift-Left Static & Secret Prevention**:
   - Gitleaks pre-commit + CI gate (mitigates THREAT-01).
   - Custom Semgrep rules + CodeQL (mitigates THREAT-13, THREAT-14).
2. **Dependency & Configuration Hardening**:
   - OSV-Scanner + Trivy + Checkov (mitigates THREAT-04, THREAT-06).
   - Pinned actions and least-privilege token permissions (mitigates THREAT-03).
3. **Dynamic Sandbox Protection**:
   - Ephemeral container with dropped capabilities and ZAP DAST (mitigates THREAT-07, THREAT-12).
4. **Supply Chain & Release Integrity**:
   - Sigstore Cosign keyless signing + SLSA Provenance attestations (mitigates THREAT-09, THREAT-10, THREAT-11).
   - Immutable SHA-256 digest release gate (mitigates THREAT-08, THREAT-09).
