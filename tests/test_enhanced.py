"""Automated test suite for Enhanced CSSS 441 Book Catalog & Security Gates.

Covers:
- UI HTML rendering for Catalog (/) and Security Dashboard (/security)
- Kubernetes Probes (/health/live, /health/ready) and Prometheus (/metrics)
- Book CRUD operations with Administrative Authentication
- Input validation (ISBN, non-negative price, availability allowlist)
- Duplicate ISBN conflict handling (409)
- Directory traversal prevention on security reports
- Security headers verification (CSP, X-Frame-Options, etc.)
"""

import sys
from pathlib import Path

from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.main import app  # noqa: E402
from app.security import ADMIN_API_KEY  # noqa: E402

client = TestClient(app)
ADMIN_HEADERS = {"X-Admin-Key": ADMIN_API_KEY}


# ---------------------------------------------------------------------------
# 1. UI & HTML Rendering Tests
# ---------------------------------------------------------------------------
def test_ui_catalog_dashboard_renders():
    """Verify GET / renders the HTML catalog dashboard with CSRF token."""
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["Content-Type"]
    assert "Book Catalog" in response.text
    assert 'name="csrf_token"' in response.text


def test_ui_security_dashboard_renders():
    """Verify GET /security renders the interactive DevSecOps dashboard."""
    response = client.get("/security")
    assert response.status_code == 200
    assert "text/html" in response.headers["Content-Type"]
    assert "DevSecOps Security Pipeline" in response.text
    assert "Vulnerability Posture" in response.text


# ---------------------------------------------------------------------------
# 2. Kubernetes Probes & Prometheus Metrics Tests
# ---------------------------------------------------------------------------
def test_liveness_probe():
    """Verify GET /health/live returns process status."""
    response = client.get("/health/live")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "alive"
    assert "timestamp" in data


def test_readiness_probe():
    """Verify GET /health/ready executes database query and confirms readiness."""
    response = client.get("/health/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
    assert data["database"] == "connected"


def test_prometheus_metrics_endpoint():
    """Verify GET /metrics exposes Prometheus formatted metrics."""
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "http_requests_total" in response.text or "http_request_duration" in response.text


# ---------------------------------------------------------------------------
# 3. Security Headers & CSRF Verification
# ---------------------------------------------------------------------------
def test_extended_security_headers():
    """Verify CSP and permissions policy headers are present on all responses."""
    response = client.get("/")
    assert "Content-Security-Policy" in response.headers
    assert "Permissions-Policy" in response.headers
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["X-Content-Type-Options"] == "nosniff"


# ---------------------------------------------------------------------------
# 4. Book CRUD & Admin Authorization Tests
# ---------------------------------------------------------------------------
def test_create_book_requires_admin():
    """Verify unauthenticated book creation is blocked with HTTP 401."""
    payload = {
        "title": "Unauthorized Book",
        "author": "Attacker",
        "isbn": "9780123456789",
        "category": "Security",
        "year": 2024,
        "price": 19.99,
        "availability": "IN_STOCK",
    }
    response = client.post("/api/books", json=payload)
    assert response.status_code == 401


def test_create_book_admin_success():
    """Verify book creation succeeds with valid admin key and input."""
    payload = {
        "title": "The Art of Software Security Assessment",
        "author": "Mark Dowd, John McDonald, Justin Schuh",
        "isbn": "9780321444424",
        "category": "Security",
        "year": 2006,
        "price": 55.00,
        "availability": "IN_STOCK",
        "rating": 4.9,
    }
    response = client.post("/api/books", json=payload, headers=ADMIN_HEADERS)
    assert response.status_code in (201, 409)  # 201 created or 409 if exists from rerun
    if response.status_code == 201:
        data = response.json()
        assert data["title"] == payload["title"]
        assert data["isbn"] == payload["isbn"]


def test_create_book_duplicate_isbn_conflict():
    """Verify inserting duplicate ISBN triggers HTTP 409 Conflict."""
    payload = {
        "title": "Duplicate ISBN Test",
        "author": "Test Author",
        "isbn": "9781119642787",  # Existing Ross Anderson book ISBN
        "category": "Security",
        "year": 2024,
        "price": 25.00,
        "availability": "IN_STOCK",
    }
    response = client.post("/api/books", json=payload, headers=ADMIN_HEADERS)
    assert response.status_code == 409
    assert "already exists" in response.json()["detail"]


def test_create_book_validation_negative_price():
    """Verify negative price is rejected with HTTP 422."""
    payload = {
        "title": "Invalid Price Book",
        "author": "Test Author",
        "isbn": "9780987654321",
        "category": "Security",
        "year": 2024,
        "price": -10.00,
        "availability": "IN_STOCK",
    }
    response = client.post("/api/books", json=payload, headers=ADMIN_HEADERS)
    assert response.status_code == 422


def test_create_book_validation_invalid_availability():
    """Verify non-allowlisted availability status is rejected with HTTP 422."""
    payload = {
        "title": "Invalid Status Book",
        "author": "Test Author",
        "isbn": "9780987654322",
        "category": "Security",
        "year": 2024,
        "price": 10.00,
        "availability": "INVALID_STATE",
    }
    response = client.post("/api/books", json=payload, headers=ADMIN_HEADERS)
    assert response.status_code == 422


def test_delete_book_requires_admin():
    """Verify book deletion is protected with 401."""
    response = client.delete("/api/books/1")
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# 5. Security Scorecard & Traversal Prevention Tests
# ---------------------------------------------------------------------------
def test_scorecard_api():
    """Verify GET /api/security/scorecard returns valid scorecard schema."""
    response = client.get("/api/security/scorecard")
    assert response.status_code == 200
    data = response.json()
    assert "schema_version" in data
    assert "overall_status" in data


def test_report_download_requires_admin():
    """Verify report downloading without admin key is blocked with 401."""
    response = client.get("/api/security/reports/semgrep-report.json?admin_key=wrong-key")
    assert response.status_code == 401


def test_report_path_traversal_prevention():
    """Verify directory traversal attempts on reports endpoint fail with 404."""
    response = client.get(
        "/api/security/reports/../../app/main.py",
        params={"admin_key": ADMIN_API_KEY},
    )
    assert response.status_code in (404, 422)


def test_custom_openapi_docs_page_renders():
    """Verify GET /docs renders the Aegis CI themed OpenAPI specification page."""
    response = client.get("/docs")
    assert response.status_code == 200
    assert "text/html" in response.headers["Content-Type"]
    assert "OpenAPI 3.1 Interactive Specs" in response.text
    assert "swagger-ui" in response.text
    assert "devsecops-admin-secret-2026" in response.text

