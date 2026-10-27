#!/usr/bin/env bash
# ============================================================================
# CSSS 441 DevSecOps Pipeline - Local Security Gate Execution Script
# ============================================================================
set -uo pipefail

REPORTS_DIR="reports"
mkdir -p "$REPORTS_DIR"

TOTAL_FAILED=0

echo "========================================================================"
echo "CSSS 441 - AUTOMATED SECURITY GATE VERIFICATION SUITE"
echo "========================================================================"

# ----------------------------------------------------------------------------
# 1. Gitleaks Secret Scanning
# ----------------------------------------------------------------------------
echo ""
echo "[GATE 1/6] Running Gitleaks Secret Detection..."
if command -v gitleaks &>/dev/null; then
    if gitleaks detect --no-git --source . --config .gitleaks.toml --report-format json --report-path "$REPORTS_DIR/gitleaks-report.json" --verbose; then
        echo "[PASS] Gitleaks: No exposed secrets detected."
    else
        echo "[FAIL] Gitleaks: Secrets detected! Review $REPORTS_DIR/gitleaks-report.json" >&2
        TOTAL_FAILED=$((TOTAL_FAILED + 1))
    fi
else
    echo "[WARN] Gitleaks binary not found on local PATH. Skipping local run (enforced in CI)."
fi

# ----------------------------------------------------------------------------
# 2. Semgrep Custom Rule Tests & Application Scan
# ----------------------------------------------------------------------------
echo ""
echo "[GATE 2/6] Running Semgrep Custom Rule Verification & Scan..."
if command -v semgrep &>/dev/null || [ -f ".venv/Scripts/semgrep.exe" ] || [ -f ".venv/bin/semgrep" ]; then
    SEMGREP_BIN="semgrep"
    [ -f ".venv/Scripts/semgrep.exe" ] && SEMGREP_BIN=".venv/Scripts/semgrep.exe"
    [ -f ".venv/bin/semgrep" ] && SEMGREP_BIN=".venv/bin/semgrep"

    echo "--> Running Semgrep custom rule unit tests (positive & negative assertions)..."
    if $SEMGREP_BIN --test --config .semgrep/custom_rules.yml tests/semgrep/; then
        echo "[PASS] Semgrep: All custom rule tests passed successfully."
    else
        echo "[FAIL] Semgrep: Custom rule test failure!" >&2
        TOTAL_FAILED=$((TOTAL_FAILED + 1))
    fi

    echo "--> Scanning application source code (app/)..."
    if $SEMGREP_BIN scan --config .semgrep/custom_rules.yml --error --json --output "$REPORTS_DIR/semgrep-report.json" app/; then
        echo "[PASS] Semgrep: Application code clean."
    else
        echo "[FAIL] Semgrep: Security policy violation detected in app/!" >&2
        TOTAL_FAILED=$((TOTAL_FAILED + 1))
    fi
else
    echo "[WARN] Semgrep not installed in current environment. Enforced in CI."
fi

# ----------------------------------------------------------------------------
# 3. OSV-Scanner Dependency Vulnerabilities
# ----------------------------------------------------------------------------
echo ""
echo "[GATE 3/6] Running OSV-Scanner Dependency Analysis..."
if command -v osv-scanner &>/dev/null; then
    if osv-scanner --lockfile=requirements.txt --json --output "$REPORTS_DIR/osv-report.json"; then
        echo "[PASS] OSV-Scanner: No known vulnerable dependencies."
    else
        echo "[FAIL] OSV-Scanner: Vulnerable dependency identified!" >&2
        TOTAL_FAILED=$((TOTAL_FAILED + 1))
    fi
else
    echo "[WARN] OSV-Scanner not found locally. Enforced in CI workflow."
fi

# ----------------------------------------------------------------------------
# 4. Trivy Source & Filesystem Scan
# ----------------------------------------------------------------------------
echo ""
echo "[GATE 4/6] Running Trivy Filesystem Scan..."
if command -v trivy &>/dev/null; then
    if trivy fs --severity HIGH,CRITICAL --format json --output "$REPORTS_DIR/trivy-fs-report.json" --exit-code 1 .; then
        echo "[PASS] Trivy: No HIGH or CRITICAL issues found in filesystem."
    else
        echo "[FAIL] Trivy: Policy violation in filesystem!" >&2
        TOTAL_FAILED=$((TOTAL_FAILED + 1))
    fi
else
    echo "[WARN] Trivy not found locally. Enforced in CI workflow."
fi

# ----------------------------------------------------------------------------
# 5. Checkov Infrastructure-as-Code & Dockerfile Scan
# ----------------------------------------------------------------------------
echo ""
echo "[GATE 5/6] Running Checkov Container & IaC Security Scan..."
if command -v checkov &>/dev/null || [ -f ".venv/Scripts/checkov.exe" ] || [ -f ".venv/bin/checkov" ]; then
    CHECKOV_BIN="checkov"
    [ -f ".venv/Scripts/checkov.exe" ] && CHECKOV_BIN=".venv/Scripts/checkov.exe"
    [ -f ".venv/bin/checkov" ] && CHECKOV_BIN=".venv/bin/checkov"

    if $CHECKOV_BIN -f Dockerfile -f compose.yaml --framework dockerfile,compose --compact --output json --output-file-path "$REPORTS_DIR/"; then
        echo "[PASS] Checkov: Container configurations comply with security baseline."
    else
        echo "[FAIL] Checkov: Insecure container configuration detected!" >&2
        TOTAL_FAILED=$((TOTAL_FAILED + 1))
    fi
else
    echo "[WARN] Checkov not found locally. Enforced in CI workflow."
fi

# ----------------------------------------------------------------------------
# Summary
# ----------------------------------------------------------------------------
echo ""
echo "========================================================================"
if [ "$TOTAL_FAILED" -eq 0 ]; then
    echo "==> ALL ACTIVE SECURITY GATES PASSED! READY FOR PUSH / RELEASE."
    exit 0
else
    echo "==> SECURITY POLICY VIOLATION: $TOTAL_FAILED gate(s) failed." >&2
    exit 1
fi
