"""FastAPI Book Catalogue API for CSSS 441 DevSecOps Pipeline.

This application serves as the target microservice to demonstrate security gates
in the continuous integration and release pipeline.
"""

import logging
from typing import Annotated, Final

from fastapi import FastAPI, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, Field

# Configure basic structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("csss441.api")

APP_NAME: Final[str] = "csss441-book-catalog"
APP_VERSION: Final[str] = "1.0.0"

app = FastAPI(
    title="CSSS 441 Secure Book Catalogue",
    description=(
        "Target application for DevSecOps automated security gates and provenance verification."
    ),
    version=APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
)


@app.middleware("http")
async def add_security_headers(request, call_next):
    """Inject defensive HTTP response headers required by security policy."""
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Cache-Control"] = "no-store"
    return response


# ---------------------------------------------------------------------------
# Pydantic Response Models
# ---------------------------------------------------------------------------
class HealthResponse(BaseModel):
    """Health check response payload."""

    model_config = ConfigDict(extra="forbid")

    status: str = Field(default="healthy", description="Current health status of the service")
    app: str = Field(default=APP_NAME, description="Application identifier")
    version: str = Field(default=APP_VERSION, description="Application semantic version")


class Book(BaseModel):
    """Book entity schema."""

    model_config = ConfigDict(extra="forbid")

    id: int = Field(gt=0, description="Unique book identifier")
    title: str = Field(min_length=1, max_length=120, description="Book title")
    author: str = Field(min_length=1, max_length=100, description="Author name")
    category: str = Field(min_length=1, max_length=50, description="Subject category")
    year: int = Field(ge=1970, le=2030, description="Publication year")


class BookListResponse(BaseModel):
    """List response wrapping book items and count."""

    model_config = ConfigDict(extra="forbid")

    total: int = Field(ge=0, description="Total matching books")
    items: list[Book] = Field(default_factory=list, description="Array of book records")


# ---------------------------------------------------------------------------
# Deterministic Sample Catalogue
# ---------------------------------------------------------------------------
SAMPLE_BOOKS: Final[list[dict]] = [
    {
        "id": 1,
        "title": "Security Engineering: A Guide to Building Dependable Distributed Systems",
        "author": "Ross Anderson",
        "category": "Security",
        "year": 2020,
    },
    {
        "id": 2,
        "title": "Threat Modeling: Designing for Security",
        "author": "Adam Shostack",
        "category": "Security",
        "year": 2014,
    },
    {
        "id": 3,
        "title": "Building Secure and Reliable Systems",
        "author": "Heather Adkins, Betsy Beyer, Paul Blankinship",
        "category": "Site Reliability & Security",
        "year": 2020,
    },
    {
        "id": 4,
        "title": "Designing Data-Intensive Applications",
        "author": "Martin Kleppmann",
        "category": "Architecture",
        "year": 2017,
    },
    {
        "id": 5,
        "title": "The Web Application Hacker's Handbook",
        "author": "Dafydd Stuttard, Marcus Pinto",
        "category": "Security",
        "year": 2011,
    },
    {
        "id": 6,
        "title": "Site Reliability Engineering: How Google Runs Production Systems",
        "author": "Betsy Beyer, Chris Jones, Jennifer Petoff, Niall Murphy",
        "category": "DevOps",
        "year": 2016,
    },
]

# Query parameter validation regex: alphanumeric, spaces, hyphens, and periods only
QUERY_PATTERN: Final[str] = r"^[a-zA-Z0-9\s\.\-_]+$"


# ---------------------------------------------------------------------------
# API Endpoints
# ---------------------------------------------------------------------------
@app.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Health check",
    description="Returns the health status of the application.",
    tags=["Monitoring"],
)
def get_health() -> HealthResponse:
    """Return application operational health."""
    logger.debug("Health check requested")
    return HealthResponse(
        status="healthy",
        app=APP_NAME,
        version=APP_VERSION,
    )


@app.get(
    "/books",
    response_model=BookListResponse,
    status_code=status.HTTP_200_OK,
    summary="List or search books",
    description="Returns deterministic list of books, optionally filtered by keyword query.",
    tags=["Catalogue"],
)
def get_books(
    q: Annotated[
        str | None,
        Query(
            min_length=1,
            max_length=50,
            pattern=QUERY_PATTERN,
            description="Optional search query keyword (1-50 alphanumeric characters)",
        ),
    ] = None,
) -> BookListResponse:
    """Retrieve all books or search books by keyword."""
    if q is None:
        return BookListResponse(
            total=len(SAMPLE_BOOKS),
            items=[Book(**b) for b in SAMPLE_BOOKS],
        )

    clean_query = q.strip().lower()
    if not clean_query:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Search query cannot be whitespace-only.",
        )

    matching = [
        Book(**b)
        for b in SAMPLE_BOOKS
        if clean_query in b["title"].lower()
        or clean_query in b["author"].lower()
        or clean_query in b["category"].lower()
    ]

    logger.info("Executed search query '%s', found %d items", clean_query, len(matching))
    return BookListResponse(total=len(matching), items=matching)
