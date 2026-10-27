# Pipeline Security Gate Policy

## 1. Security Gate Philosophy & Core Principles

The security gates in this pipeline enforce a **fail-closed** policy:
1. **Mandatory Enforcement**: An artifact or pull request cannot proceed if any required gate fails, times out, or produces unhandled errors.
2. **No Silent Suppressions**: Global scanner suppression flags (such as `--ignore`, `continue-on-error: true`, or `|| true`) are strictly prohibited in the CI workflows.
3. **Defense in Depth**: Local developer checks provide fast feedback, but CI gates are the definitive source of truth and cannot be bypassed by skipping local pre-commit hooks.
4. **Separation of Roles**: The author of a change cannot unilaterally approve security gate exceptions or merge unverified code.

---

## 2. Gate Failure Matrix & Thresholds

| Security Gate | Scanner / Tool | Blocking Threshold | Permitted Actions on Violation |
| :--- | :--- | :--- | :--- |
| **Gate 1: Secrets** | Gitleaks | **Any detected secret** (High, Medium, or Low severity) | Immediate commit rejection. If pushed to remote, credential MUST be revoked/rotated immediately. |
| **Gate 2: Code Quality & Tests** | Pytest & Ruff | **Any failing unit test** or lint syntax violation | Block pull request merge until all tests pass and code is formatted. |
| **Gate 3: SAST** | Semgrep & CodeQL | **Any ERROR-level rule match** (e.g. SQL injection, shell=True, eval, pickle, wildcard CORS) | Refactor code to use secure parameterized alternative. |
| **Gate 4: SCA** | OSV-Scanner & Trivy | **Any vulnerability with severity HIGH or CRITICAL** | Upgrade package version to patched release or pin dependency. |
| **Gate 5: Container & IaC** | Checkov & Trivy Image | **Any HIGH or CRITICAL misconfiguration or CVE** | Enforce non-root user, read-only rootfs, and update base image. |
| **Gate 6: DAST** | OWASP ZAP Baseline | **Any rule mapped to FAIL in `.zap/rules.tsv`** (e.g. MIME sniffing, CSP wildcard, error leaks) | Remediate response headers or application endpoints. |
| **Gate 7: Supply Chain Integrity** | Sigstore Cosign & SLSA Provenance | **Missing signature, invalid digest, untrusted OIDC identity, or missing provenance attestation** | Immediate release abort. No deployment allowed. |

---

## 3. Policy Exception & Waiver Process

Under exceptional circumstances (e.g., third-party upstream CVE with no available vendor patch and documented compensating controls), a temporary exception may be requested.

### Mandatory Exception Fields
Every exception must be formally documented in `docs/remediation-log.md` with all of the following:

```yaml
exception_id: "EXC-2026-001"
finding_identifier: "CVE-2026-XXXXX / CHECKOV-DOCKER-01"
affected_component: "requirements.txt: some-package"
risk_assessment: "Low exploitability in our architecture because endpoint does not process user-supplied XML."
compensating_controls: "WAF input validation restricts payload sizes to < 1KB."
responsible_person: "Jane Doe (Security Lead)"
approved_by: "Dr. Security Lecturer / Project Advisor"
approval_date: "2026-10-27"
expiry_date: "2026-11-27" # Maximum duration: 30 days
remediation_plan: "Upgrade to v2.1.0 as soon as upstream maintainer merges fix."
```

### Prohibited Practices
- **No Blanket Allowlists**: Never add an entire directory, repository, or broad rule pattern to an allowlist.
- **No Permanent Exceptions**: Any waiver older than 30 days automatically expires and breaks the CI gate.
