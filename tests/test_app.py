"""Automated test suite for the FastAPI Book Catalogue Application.

Covers:
- GET /health endpoint checks
- GET /books default listing
- GET /books query filtering with valid search terms
- GET /books empty result handling
- GET /books input validation (min/max length, regex, whitespace)
"""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_endpoint():
    """Verify health endpoint returns 200 and expected metadata."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["app"] == "csss441-book-catalog"
    assert "version" in data


def test_security_headers_present():
    """Verify defensive HTTP security headers are injected into responses."""
    response = client.get("/health")
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["Referrer-Policy"] == "no-referrer"
    assert response.headers["Cache-Control"] == "no-store"


def test_get_all_books():
    """Verify default catalogue retrieval returns all deterministic records."""
    response = client.get("/books")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] > 0
    assert len(data["items"]) == data["total"]
    # Verify structure of first item
    first_book = data["items"][0]
    assert "id" in first_book
    assert "title" in first_book
    assert "author" in first_book
    assert "category" in first_book
    assert "year" in first_book


def test_search_books_with_valid_query():
    """Verify case-insensitive search filtering."""
    response = client.get("/books?q=security")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 2
    for item in data["items"]:
        haystack = f"{item['title']} {item['author']} {item['category']}".lower()
        assert "security" in haystack


def test_search_books_by_author():
    """Verify filtering works on author name."""
    response = client.get("/books?q=Kleppmann")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert "Designing Data-Intensive Applications" in data["items"][0]["title"]


def test_search_books_no_matches():
    """Verify search returning no matches yields an empty list with total=0."""
    response = client.get("/books?q=nonexistenttopic")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert data["items"] == []


def test_search_books_validation_min_length():
    """Verify empty query string triggers 422 Unprocessable Entity."""
    response = client.get("/books?q=")
    assert response.status_code == 422
    error_detail = response.json()
    assert "detail" in error_detail


def test_search_books_validation_max_length():
    """Verify query string exceeding 50 characters triggers 422."""
    too_long = "a" * 51
    response = client.get(f"/books?q={too_long}")
    assert response.status_code == 422


def test_search_books_validation_invalid_characters():
    """Verify queries containing disallowed characters (e.g. angle brackets, quotes)
    are rejected."""
    # Attempt script tag injection
    response = client.get("/books?q=<script>")
    assert response.status_code == 422

    # Attempt SQL wildcard characters
    response = client.get("/books?q=test' OR 1=1--")
    assert response.status_code == 422


def test_search_books_whitespace_only():
    """Verify whitespace-only query is handled and rejected."""
    response = client.get("/books?q=%20%20%20")
    # %20 is accepted by regex, but stripped to empty in logic, returning 400
    assert response.status_code == 400
    assert "Search query cannot be whitespace-only" in response.json()["detail"]
