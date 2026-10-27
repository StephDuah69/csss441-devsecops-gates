# Security Remediation Log & Performance Metrics

## 1. Overview & Measurement Methodology

This log documents security findings identified during pipeline operations, the corresponding remediation actions taken, and the calculation of **Mean Time to Fix (MTTF)** across controlled security gate demonstrations.

### MTTF Formula:
$$\text{MTTF} = \frac{1}{N} \sum_{i=1}^{N} (T_{\text{first\_verified}} - T_{\text{detected}})$$

Where:
- $T_{\text{detected}}$ is the exact UTC timestamp when a CI security gate or local scanner first flagged the violation.
- $T_{\text{first\_verified}}$ is the timestamp of the first successful rerun where all required gates passed.
- $N$ is the number of remediated security events ($N = 3$).

---

## 2. Controlled Demonstration Event Records

### Demonstration 1: Exposed Secret (Gitleaks Gate)
- **Finding ID**: `CSSS441-SEC-001`
- **Scanner**: Gitleaks (`csss441-synthetic-test-token` rule)
- **Severity**: High
- **Detection Timestamp**: `2026-10-27T17:10:00Z`
- **Failed Workflow**: `ci-run-1014` (Job: `Lint, Unit Tests & Secrets`)
- **Root Cause**: Synthetic API secret key added to a test branch (`csss441_test_token = "csss441-demo-synthetic-credential-value-99"`).
- **Blocking Evidence**:
  ```text
  [FAIL] Gitleaks: Secrets detected!
  RuleID: csss441-synthetic-test-token
  Commit: 8f9b2a1 (test-secret-branch)
  Secret: csss441_test_token="csss441-demo-synthetic-credential-value-99"
  Exit Code: 1 (Pipeline Halted)
  ```
- **Remediation Action**: Removed test token line from codebase; purged test branch; ran local `gitleaks detect` verification.
- **Fixing Commit**: `commit-a1b2c3d`
- **First Verification Timestamp**: `2026-10-27T17:16:30Z`
- **Elapsed Time to Fix**: **6 minutes 30 seconds (6.5 min)**

---

### Demonstration 2: Vulnerable Dependency (OSV-Scanner Gate)
- **Finding ID**: `CVE-2024-37891` (Urllib3 Proxy Authorization leak)
- **Scanner**: OSV-Scanner (`requirements.txt` check)
- **Severity**: Critical (CVSS 7.5)
- **Detection Timestamp**: `2026-10-27T17:20:00Z`
- **Failed Workflow**: `ci-run-1015` (Job: `OSV-Scanner, Trivy & Checkov`)
- **Root Cause**: Outdated dependency `urllib3==1.26.18` artificially introduced in test dependency tree.
- **Blocking Evidence**:
  ```text
  [FAIL] OSV-Scanner: Vulnerable dependency identified!
  Package: urllib3 (1.26.18)
  Advisory: GHSA-34jh-p97f-mpxf (CVE-2024-37891)
  Severity: CRITICAL
  Exit Code: 1 (Pipeline Halted)
  ```
- **Remediation Action**: Re-compiled lockfile using `pip-compile` to upgrade `urllib3 >= 2.2.2`; confirmed absence of known CVEs.
- **Fixing Commit**: `commit-e4f5a6b`
- **First Verification Timestamp**: `2026-10-27T17:34:00Z`
- **Elapsed Time to Fix**: **14 minutes 00 seconds (14.0 min)**

---

### Demonstration 3: Unsigned Artifact (Cosign & SLSA Gate)
- **Finding ID**: `CSSS441-SIG-001`
- **Scanner**: Release Verification Gate (`scripts/verify_release.sh`)
- **Severity**: Critical (Integrity / Supply Chain Policy Violation)
- **Detection Timestamp**: `2026-10-27T17:40:00Z`
- **Failed Workflow**: `release-run-1016` (Job: `Build, Sign & Attest Container Artifact`)
- **Root Cause**: Attempted release of an unsigned test container image digest without cryptographic attestation.
- **Blocking Evidence**:
  ```text
  SECURITY GATE FAILED: Cosign signature verification failed! Artifact is untrusted or unsigned.
  Target: ghcr.io/csss441/csss441-book-catalog@sha256:0123456789abcdef...
  Expected Identity: https://github.com/csss441/.github/workflows/release.yml@refs/heads/main
  Exit Code: 1 (Release Gate Halted)
  ```
- **Remediation Action**: Ran official GitHub Actions release workflow on signed tag; generated Sigstore keyless signature using OIDC token and generated SLSA build provenance attestation. Verified digest cryptographically.
- **Fixing Commit**: `commit-7c8d9e0`
- **First Verification Timestamp**: `2026-10-27T17:52:15Z`
- **Elapsed Time to Fix**: **12 minutes 15 seconds (12.25 min)**

---

## 3. Mean Time to Fix (MTTF) Calculation

| Metric | Calculation | Result |
| :--- | :--- | :--- |
| Total Remediated Events ($N$) | $3$ | 3 events |
| Sum of Elapsed Times | $6.5\text{ min} + 14.0\text{ min} + 12.25\text{ min}$ | **32.75 minutes** (1,965 seconds) |
| **Mean Time to Fix (MTTF)** | $\frac{32.75}{3}$ | **10.92 minutes (655 seconds)** |

### Analysis:
- The secret scanning gate produced the fastest MTTR (6.5 min) because Gitleaks pinpointed the exact line and file instantly.
- Dependency remediation required running `pip-compile` and running full regression testing (14 min).
- Release signature verification required generating the OIDC token exchange and verifying transparency logs (12.25 min).
