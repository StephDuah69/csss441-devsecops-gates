"""DevSecOps Security Scorecard and Report Service.

Reads actual security gate outcomes from evidence/security-scorecard.json
and calculates vulnerability statistics from generated scan reports in reports/.
Strict path allowlisting prevents directory traversal (CWE-22).
"""

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SCORECARD_PATH = PROJECT_ROOT / "evidence" / "security-scorecard.json"
REPORTS_DIR = PROJECT_ROOT / "reports"

ALLOWED_REPORTS = {
    "gitleaks-report.json",
    "semgrep-report.json",
    "osv-report.json",
    "trivy-fs-report.json",
    "trivy-image-report.json",
    "checkov-report.json",
    "pip-audit-report.json",
    "pytest-report.xml",
    "source-sbom.cdx.json",
    "image-sbom.cdx.json",
}


def get_latest_scorecard() -> dict[str, Any]:
    """Retrieve structured security scorecard produced by run_gates.py or CI."""
    if not SCORECARD_PATH.exists():
        return {
            "status": "UNKNOWN",
            "schema_version": "1.0.0",
            "generated_at": None,
            "commit_sha": None,
            "overall_status": "UNKNOWN",
            "summary": "No security scorecard available. Run 'python scripts/run_gates.py' to generate.",
            "gates": [],
            "vulnerabilities": {"critical": 0, "high": 0, "medium": 0, "low": 0},
        }

    try:
        with open(SCORECARD_PATH, encoding="utf-8") as f:
            data = json.load(f)

        # Check for staleness (e.g. > 7 days old)
        generated_at = data.get("finish_time") or data.get("start_time")
        is_stale = False
        if generated_at:
            try:
                gen_dt = datetime.fromisoformat(generated_at.replace("Z", "+00:00"))
                delta = datetime.now(UTC) - gen_dt
                if delta.days > 7:
                    is_stale = True
            except Exception:
                pass

        data["is_stale"] = is_stale
        return data
    except Exception as exc:
        return {
            "status": "ERROR",
            "schema_version": "1.0.0",
            "overall_status": "ERROR",
            "summary": f"Failed to parse security scorecard: {exc}",
            "gates": [],
            "vulnerabilities": {"critical": 0, "high": 0, "medium": 0, "low": 0},
        }


def get_safe_report_path(filename: str) -> Path | None:
    """Validate report filename against strict allowlist to prevent traversal."""
    if filename not in ALLOWED_REPORTS:
        return None

    report_path = (REPORTS_DIR / filename).resolve()
    if not report_path.is_file() or not str(report_path).startswith(str(REPORTS_DIR.resolve())):
        return None

    return report_path


def parse_vulnerability_statistics() -> dict[str, int]:
    """Calculate aggregate vulnerability severity counts from available reports."""
    stats = {"critical": 0, "high": 0, "medium": 0, "low": 0}

    # 1. Semgrep JSON
    semgrep_file = REPORTS_DIR / "semgrep-report.json"
    if semgrep_file.exists():
        try:
            with open(semgrep_file, encoding="utf-8") as f:
                data = json.load(f)
                for res in data.get("results", []):
                    sev = res.get("extra", {}).get("severity", "LOW").lower()
                    if sev in stats:
                        stats[sev] += 1
                    elif sev == "error":
                        stats["high"] += 1
                    elif sev == "warning":
                        stats["medium"] += 1
        except Exception:
            pass

    # 2. Trivy Filesystem JSON
    trivy_file = REPORTS_DIR / "trivy-fs-report.json"
    if trivy_file.exists():
        try:
            with open(trivy_file, encoding="utf-8") as f:
                data = json.load(f)
                for target in data.get("Results", []):
                    for vuln in target.get("Vulnerabilities", []):
                        sev = vuln.get("Severity", "LOW").lower()
                        if sev in stats:
                            stats[sev] += 1
        except Exception:
            pass

    # 3. Pip-Audit JSON
    pip_audit_file = REPORTS_DIR / "pip-audit-report.json"
    if pip_audit_file.exists():
        try:
            with open(pip_audit_file, encoding="utf-8") as f:
                data = json.load(f)
                for dep in data.get("dependencies", []):
                    for _vuln in dep.get("vulns", []):
                        # Pip-audit doesn't always provide severity, default to high
                        stats["high"] += 1
        except Exception:
            pass

    return stats
