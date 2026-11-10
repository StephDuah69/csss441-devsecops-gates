"""DevSecOps Security Dashboard router and authorized report downloads."""

from fastapi import APIRouter, HTTPException, Query, Request, status
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.templating import Jinja2Templates

from app.security import ADMIN_API_KEY
from app.services import scorecard_service

templates = Jinja2Templates(directory="app/templates")
router = APIRouter(tags=["Security Dashboard"])

DEFAULT_GATES = [
    {
        "name": "Gitleaks",
        "category": "Secrets Detection",
        "status": "PASS",
        "report_file": "gitleaks-report.json",
        "icon": "fa-key",
    },
    {
        "name": "Semgrep",
        "category": "SAST Analysis",
        "status": "PASS",
        "report_file": "semgrep-report.json",
        "icon": "fa-shield-halved",
    },
    {
        "name": "Ruff",
        "category": "Code Quality & Linting",
        "status": "PASS",
        "report_file": None,
        "icon": "fa-check-double",
    },
    {
        "name": "Pytest",
        "category": "Application Unit Tests",
        "status": "PASS",
        "report_file": "pytest-report.xml",
        "icon": "fa-vial",
    },
    {
        "name": "OSV-Scanner",
        "category": "Dependency SCA",
        "status": "PASS",
        "report_file": "osv-report.json",
        "icon": "fa-box-open",
    },
    {
        "name": "pip-audit",
        "category": "Python Vulnerability Audit",
        "status": "PASS",
        "report_file": "pip-audit-report.json",
        "icon": "fa-magnifying-glass",
    },
    {
        "name": "Trivy Filesystem",
        "category": "Filesystem Vulnerabilities",
        "status": "PASS",
        "report_file": "trivy-fs-report.json",
        "icon": "fa-folder-tree",
    },
    {
        "name": "Checkov",
        "category": "IaC & Container Hardening",
        "status": "PASS",
        "report_file": "checkov-report.json",
        "icon": "fa-cubes",
    },
    {
        "name": "OWASP ZAP",
        "category": "DAST Dynamic Baseline",
        "status": "PASS",
        "report_file": None,
        "icon": "fa-bolt",
    },
]


@router.get("/security", response_class=HTMLResponse, include_in_schema=False)
def serve_security_dashboard(request: Request):
    """Render interactive DevSecOps dashboard with actual scorecard and vulnerability stats."""
    scorecard = scorecard_service.get_latest_scorecard()
    vulnerabilities = scorecard_service.parse_vulnerability_statistics()

    # Map scorecard gates or fallback to registered defaults
    active_gates = scorecard.get("gates")
    if not active_gates:
        active_gates = DEFAULT_GATES

    return templates.TemplateResponse(
        request=request,
        name="security/dashboard.html",
        context={
            "active_page": "security",
            "scorecard": scorecard,
            "vulnerabilities": vulnerabilities,
            "gates": active_gates,
        },
    )


@router.get("/api/security/scorecard", summary="Get latest security scorecard JSON")
def get_scorecard_json():
    """Retrieve structured security scorecard."""
    return scorecard_service.get_latest_scorecard()


@router.get("/api/security/reports/{filename}", summary="Download authorized scan report")
def download_report(
    filename: str,
    admin_key: str = Query(
        ..., description="Administrator access key required to view scan reports"
    ),
):
    """Serve a specific scan report file with strict allowlisting and directory traversal prevention."""
    if admin_key != ADMIN_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized: Valid admin key required to inspect scan reports.",
        )

    safe_path = scorecard_service.get_safe_report_path(filename)
    if not safe_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report '{filename}' not found or not in allowed reports directory.",
        )

    return FileResponse(
        path=safe_path,
        media_type="application/json" if safe_path.suffix == ".json" else "text/plain",
        filename=filename,
    )
