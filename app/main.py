"""FastAPI Book Catalogue API and DevSecOps Security Dashboard.

Core application entrypoint integrating:
- Catalog Web Interface and RESTful API
- Database Persistence via SQLAlchemy
- DevSecOps Automated Security Scorecard
- Security Response Headers, CSRF Protection, and Rate Limiting
- Kubernetes Liveness/Readiness Probes and Prometheus Metrics
"""

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.database import Base, engine
from app.routers import books, catalog_pages, health, security_dashboard
from app.schemas import APP_VERSION
from app.security import limiter, security_headers_middleware
from app.services.seed_service import seed_database

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("csss441.api")


@asynccontextmanager
async def lifespan(_: FastAPI):
    """Application lifespan event: initialize DB tables and seed initial catalogue."""
    logger.info("Initializing database schema...")
    Base.metadata.create_all(bind=engine)
    seed_database()
    logger.info("Database initialized and verified.")
    yield
    logger.info("Shutting down application...")


app = FastAPI(
    title="CSSS 441 Secure Book Catalogue",
    description=(
        "Target application for DevSecOps automated security gates, "
        "observability, and provenance verification."
    ),
    version=APP_VERSION,
    docs_url=None,
    redoc_url="/redoc",
    lifespan=lifespan,
)

# 1. State and Rate Limiter setup
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# 2. Security Headers Middleware
app.middleware("http")(security_headers_middleware)

# 3. Strict CORS Configuration (Never combine wildcard origin with allow_credentials)
allowed_origins_env = os.getenv("CORS_ALLOWED_ORIGINS", "")
if allowed_origins_env.strip():
    allowed_origins = [o.strip() for o in allowed_origins_env.split(",") if o.strip()]
else:
    allowed_origins = ["http://127.0.0.1:8000", "http://localhost:8000"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# 4. Prometheus Metrics Instrumentation
instrumentator = Instrumentator(
    should_group_status_codes=True,
    should_ignore_untemplated=True,
    excluded_handlers=["/metrics", "/health", "/health/live", "/health/ready"],
)
instrumentator.instrument(app).expose(app, endpoint="/metrics")

# 5. Include Application Routers
app.include_router(health.router)
app.include_router(books.router)
app.include_router(catalog_pages.router)
app.include_router(security_dashboard.router)
