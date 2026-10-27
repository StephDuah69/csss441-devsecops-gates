#!/usr/bin/env python3
"""DefectDojo Vulnerability Management Ingestion Client.

Imports or re-imports automated security scanner reports into DefectDojo.
Supports:
- Gitleaks (Gitleaks Scan)
- Semgrep (Semgrep JSON Report)
- OSV-Scanner (OSV Scan / CycloneDX JSON)
- Trivy (Trivy Scan)
- Checkov (Checkov Scan)
- OWASP ZAP (ZAP Scan)
"""

import argparse
import os
import sys
from pathlib import Path
from typing import Final

import httpx

# Mapping of file naming patterns to standard DefectDojo scan types
SCAN_TYPE_MAP: Final[dict[str, str]] = {
    "gitleaks": "Gitleaks Scan",
    "semgrep": "Semgrep JSON Report",
    "osv": "OSV Scan",
    "trivy-fs": "Trivy Scan",
    "trivy-image": "Trivy Scan",
    "checkov": "Checkov Scan",
    "zap": "ZAP Scan",
}


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments for report ingestion."""
    parser = argparse.ArgumentParser(
        description="Ingest security scan reports into DefectDojo."
    )
    parser.add_argument(
        "--reports-dir",
        type=Path,
        default=Path("reports"),
        help="Directory containing scan output reports (default: reports/)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate report files without submitting to remote DefectDojo API",
    )
    return parser.parse_args()


def import_scan_report(
    client: httpx.Client,
    base_url: str,
    engagement_id: int,
    scan_type: str,
    file_path: Path,
) -> bool:
    """Upload a single scan report to DefectDojo /api/v2/import-scan/."""
    url = f"{base_url.rstrip('/')}/api/v2/import-scan/"

    print(f"--> Uploading {file_path.name} as '{scan_type}' to engagement #{engagement_id}...")

    try:
        with open(file_path, "rb") as f:
            files = {"file": (file_path.name, f, "application/octet-stream")}
            data = {
                "scan_type": scan_type,
                "engagement": str(engagement_id),
                "active": "true",
                "verified": "false",
                "close_old_findings": "false",
                "deduplication_on_engagement": "true",
            }
            response = client.post(url, data=data, files=files, timeout=30.0)

        if response.status_code in (200, 201):
            res_data = response.json()
            test_id = res_data.get("test_id", res_data.get("id", "N/A"))
            print(f"[SUCCESS] Ingested {file_path.name} (Test ID: {test_id})")
            return True
        else:
            print(
                f"[FAILED] Error importing {file_path.name}: "
                f"HTTP {response.status_code} - {response.text}",
                file=sys.stderr,
            )
            return False

    except httpx.RequestError as exc:
        print(f"[ERROR] Network error communicating with DefectDojo: {exc}", file=sys.stderr)
        return False


def main() -> int:
    """Main execution entrypoint."""
    args = parse_arguments()

    if not args.reports_dir.is_dir():
        print(f"ERROR: Reports directory '{args.reports_dir}' does not exist.", file=sys.stderr)
        return 1

    report_files = [
        p for p in args.reports_dir.iterdir()
        if p.is_file() and p.suffix.lower() in (".json", ".xml", ".sarif")
    ]

    if not report_files:
        print(f"No scan report files found in '{args.reports_dir}'. Nothing to ingest.")
        return 0

    print(f"Discovered {len(report_files)} report files to process:")
    for rf in report_files:
        print(f"  - {rf.name}")

    if args.dry_run:
        print("\nDry-run mode active. Validated report existence. Skipping remote upload.")
        return 0

    # Retrieve environment credentials
    dojo_url = os.getenv("DEFECTDOJO_URL")
    dojo_token = os.getenv("DEFECTDOJO_TOKEN")
    engagement_id_str = os.getenv("DEFECTDOJO_ENGAGEMENT_ID")

    if not dojo_url or not dojo_token or not engagement_id_str:
        print(
            "\n[WARNING] DefectDojo credentials missing in environment:\n"
            "  - DEFECTDOJO_URL\n"
            "  - DEFECTDOJO_TOKEN\n"
            "  - DEFECTDOJO_ENGAGEMENT_ID\n"
            "Reports are preserved locally in 'reports/' for subsequent import.\n"
            "To import manually, provide credentials or run with --dry-run.",
            file=sys.stderr,
        )
        return 0  # Do not break local pipelines when remote Dojo is offline

    try:
        engagement_id = int(engagement_id_str)
    except ValueError:
        print(f"ERROR: DEFECTDOJO_ENGAGEMENT_ID '{engagement_id_str}' must be an integer.", file=sys.stderr)
        return 1

    headers = {"Authorization": f"Token {dojo_token}"}
    success_count = 0
    fail_count = 0

    with httpx.Client(headers=headers, verify=True) as client:
        for rf in report_files:
            # Match scan type
            matched_scan_type = None
            for key, stype in SCAN_TYPE_MAP.items():
                if key in rf.name.lower():
                    matched_scan_type = stype
                    break

            if not matched_scan_type:
                print(f"[SKIP] Unknown scanner report format for file: {rf.name}")
                continue

            ok = import_scan_report(client, dojo_url, engagement_id, matched_scan_type, rf)
            if ok:
                success_count += 1
            else:
                fail_count += 1

    print(f"\nDefectDojo Ingestion Complete: {success_count} succeeded, {fail_count} failed.")
    return 1 if fail_count > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
