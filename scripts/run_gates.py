#!/usr/bin/env python3
"""CSSS 441 DevSecOps Unified Security Gate Runner.

Executes all verification gates:
- Gitleaks (Secrets)
- Ruff (Code Quality & Style)
- Pytest (Unit & Integration Tests)
- Semgrep Application Code Scan (SAST)
- pip-audit (Python Dependency CVE Audit)
- OSV-Scanner (Open Source Vulnerability Scanner)
- Trivy (Filesystem Scan)
- Checkov (IaC & Dockerfile Hardening)

Outputs:
- Consolidated terminal scorecard
- Atomically written JSON scorecard at evidence/security-scorecard.json
"""

import json
import shutil
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent
REPORTS_DIR = PROJECT_ROOT / "reports"
EVIDENCE_DIR = PROJECT_ROOT / "evidence"
SCORECARD_FILE = EVIDENCE_DIR / "security-scorecard.json"

VENV_SCRIPTS = PROJECT_ROOT / ".venv" / "Scripts"
VENV_BIN = PROJECT_ROOT / ".venv" / "bin"

# Automatically resolve the virtual environment Python interpreter
VENV_PYTHON = VENV_SCRIPTS / "python.exe"
if not VENV_PYTHON.is_file():
    VENV_PYTHON = VENV_BIN / "python"

PYTHON_BIN = str(VENV_PYTHON) if VENV_PYTHON.is_file() else sys.executable


def find_tool(name: str) -> str | None:
    """Find binary executable in PATH or virtual environment."""
    for bin_dir in (VENV_SCRIPTS, VENV_BIN):
        for ext in (".exe", ""):
            candidate = bin_dir / f"{name}{ext}"
            if candidate.is_file():
                return str(candidate)

    return shutil.which(name)


def get_git_commit_sha() -> str:
    """Retrieve current Git commit SHA if in a repository."""
    try:
        res = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
            timeout=5,
        )
        if res.returncode == 0:
            return res.stdout.strip()
    except Exception:
        pass
    return "unknown"


def run_gate(
    name: str,
    category: str,
    cmd_args: list[str],
    report_file: str | None = None,
    timeout_sec: int = 120,
    mandatory: bool = True,
) -> dict[str, Any]:
    """Execute a single security check subprocess safely without shell=True."""
    tool_binary = cmd_args[0]

    # Special handling for Python module commands (e.g. checkov)
    if tool_binary == "checkov":
        cmd = [PYTHON_BIN, "-m", "checkov.main"] + cmd_args[1:]
    else:
        resolved_bin = find_tool(tool_binary)
        if not resolved_bin and not Path(tool_binary).is_file():
            status = "SKIPPED"
            print(f"[{status:<7}] {name:<35} (Binary '{tool_binary}' not found on PATH)")
            return {
                "name": name,
                "category": category,
                "status": status,
                "duration": 0.0,
                "exit_code": -1,
                "mandatory": mandatory,
                "report_file": report_file,
                "summary": "Tool binary not found in local environment.",
            }
        cmd = [resolved_bin if resolved_bin else tool_binary] + cmd_args[1:]

    start_time = time.time()

    try:
        res = subprocess.run(
            cmd,
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout_sec,
            check=False,
        )
        duration = round(time.time() - start_time, 2)
        passed = res.returncode == 0
        status = "PASS" if passed else "FAIL"

        print(f"[{status:<7}] {name:<35} ({duration}s)")
        return {
            "name": name,
            "category": category,
            "status": status,
            "duration": duration,
            "exit_code": res.returncode,
            "mandatory": mandatory,
            "report_file": report_file,
            "summary": res.stderr.strip()[:200] if not passed else "Clean verification",
        }
    except subprocess.TimeoutExpired:
        duration = round(time.time() - start_time, 2)
        print(f"[TIMEOUT] {name:<35} (Exceeded {timeout_sec}s)")
        return {
            "name": name,
            "category": category,
            "status": "TIMEOUT",
            "duration": duration,
            "exit_code": -2,
            "mandatory": mandatory,
            "report_file": report_file,
            "summary": f"Process exceeded timeout limit of {timeout_sec}s",
        }


def main() -> int:
    """Run all gates, write scorecard, and report summary."""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 65)
    print("       CSSS 441 DEVSECOPS SECURITY GATES RUNNER       ")
    print("=" * 65)
    start_timestamp = datetime.now(UTC).isoformat()
    commit_sha = get_git_commit_sha()

    gates_definitions = [
        {
            "name": "Gitleaks Secret Scan",
            "category": "Secrets Detection",
            "cmd": [
                "gitleaks",
                "detect",
                "--no-git",
                "--source",
                ".",
                "--config",
                ".gitleaks.toml",
                "--report-format",
                "json",
                "--report-path",
                "reports/gitleaks-report.json",
            ],
            "report": "gitleaks-report.json",
            "mandatory": False,
        },
        {
            "name": "Ruff Linter",
            "category": "Code Quality",
            "cmd": ["ruff", "check", "."],
            "report": None,
            "mandatory": True,
        },
        {
            "name": "Ruff Code Formatter",
            "category": "Code Style",
            "cmd": ["ruff", "format", "--check", "."],
            "report": None,
            "mandatory": True,
        },
        {
            "name": "Pytest Test Suite",
            "category": "Unit & Integration Tests",
            "cmd": ["pytest", "-v", "--junitxml=reports/pytest-report.xml"],
            "report": "pytest-report.xml",
            "mandatory": True,
        },
        {
            "name": "Semgrep Application Scan",
            "category": "SAST Application Scan",
            "cmd": [
                "semgrep",
                "scan",
                "--config",
                ".semgrep/custom_rules.yml",
                "--error",
                "--json",
                "--output",
                "reports/semgrep-report.json",
                "app/",
            ],
            "report": "semgrep-report.json",
            "mandatory": True,
        },
        {
            "name": "pip-audit Dependency Audit",
            "category": "Python SCA",
            "cmd": [
                "pip-audit",
                "-r",
                "requirements.txt",
                "--format",
                "json",
                "-o",
                "reports/pip-audit-report.json",
            ],
            "report": "pip-audit-report.json",
            "mandatory": True,
        },
        {
            "name": "OSV-Scanner Analysis",
            "category": "Open Source SCA",
            "cmd": [
                "osv-scanner",
                "--lockfile=requirements.txt",
                "--json",
                "--output",
                "reports/osv-report.json",
            ],
            "report": "osv-report.json",
            "mandatory": False,
        },
        {
            "name": "Trivy Filesystem Scan",
            "category": "Filesystem Vulnerabilities",
            "cmd": [
                "trivy",
                "fs",
                "--severity",
                "HIGH,CRITICAL",
                "--format",
                "json",
                "--output",
                "reports/trivy-fs-report.json",
                ".",
            ],
            "report": "trivy-fs-report.json",
            "mandatory": False,
        },
        {
            "name": "Checkov Container & IaC",
            "category": "IaC Hardening",
            "cmd": [
                "checkov",
                "-f",
                "Dockerfile",
                "--framework",
                "dockerfile",
                "--compact",
                "--output",
                "json",
                "--output-file-path",
                "reports/",
            ],
            "report": "checkov-report.json",
            "mandatory": False,
        },
    ]

    gate_results = []
    overall_passed = True

    for g in gates_definitions:
        res = run_gate(
            name=g["name"],
            category=g["category"],
            cmd_args=g["cmd"],
            report_file=g["report"],
            mandatory=g["mandatory"],
        )
        gate_results.append(res)
        if g["mandatory"] and res["status"] in ("FAIL", "TIMEOUT"):
            overall_passed = False

    finish_timestamp = datetime.now(UTC).isoformat()
    overall_status = "PASS" if overall_passed else "FAIL"

    # Terminal Consolidated Summary Table
    print("\n" + "=" * 65)
    print("                     GATE SUMMARY                     ")
    print("=" * 65)
    print(f"{'Check':<35} {'Status':<12} {'Duration'}")
    print("-" * 65)
    for gr in gate_results:
        dur_str = f"{gr['duration']}s" if gr["duration"] > 0 else "N/A"
        print(f"{gr['name']:<35} {gr['status']:<12} {dur_str}")
    print("-" * 65)
    print(f"Overall Result: {overall_status}")
    print(f"Scorecard Saved: {SCORECARD_FILE}")
    print("=" * 65)

    # Atomic Write of JSON Scorecard
    scorecard_data = {
        "schema_version": "1.0.0",
        "run_id": f"run-{int(time.time())}",
        "commit_sha": commit_sha,
        "start_time": start_timestamp,
        "finish_time": finish_timestamp,
        "overall_status": overall_status,
        "gates": gate_results,
    }

    temp_scorecard = SCORECARD_FILE.with_suffix(".tmp")
    with open(temp_scorecard, "w", encoding="utf-8") as f:
        json.dump(scorecard_data, f, indent=2)
    temp_scorecard.replace(SCORECARD_FILE)

    return 0 if overall_passed else 1


if __name__ == "__main__":
    sys.exit(main())
