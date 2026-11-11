"""Security controls, headers, authentication, CSRF, and rate limiting."""

import os
import secrets
from typing import Final

from fastapi import Header, HTTPException, Request, Response, status
from slowapi import Limiter
from slowapi.util import get_remote_address

# Admin configuration
DEFAULT_ADMIN_KEY: Final[str] = "devsecops-admin-secret-2026"
ADMIN_API_KEY: Final[str] = os.getenv("ADMIN_API_KEY", DEFAULT_ADMIN_KEY)

# Rate limiter instance
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200/minute"],
    storage_uri="memory://",
)

# CSRF In-memory token store for session tracking
_ACTIVE_CSRF_TOKENS: set[str] = set()


def generate_csrf_token() -> str:
    """Generate and record a cryptographically secure CSRF token."""
    token = secrets.token_urlsafe(32)
    _ACTIVE_CSRF_TOKENS.add(token)
    # Prune set if it grows excessively
    if len(_ACTIVE_CSRF_TOKENS) > 5000:
        _ACTIVE_CSRF_TOKENS.clear()
        _ACTIVE_CSRF_TOKENS.add(token)
    return token


def validate_csrf_token(token: str | None) -> bool:
    """Verify that the submitted CSRF token is valid."""
    if not token:
        return False
    return token in _ACTIVE_CSRF_TOKENS


async def verify_admin(
    x_admin_key: str | None = Header(None, alias="X-Admin-Key"),
    request: Request = None,
) -> bool:
    """Verify administrator identity from header or secure cookie."""
    # Check header
    if x_admin_key and secrets.compare_digest(x_admin_key, ADMIN_API_KEY):
        return True

    # Check cookie
    if request:
        cookie_token = request.cookies.get("admin_session")
        if cookie_token and secrets.compare_digest(cookie_token, ADMIN_API_KEY):
            return True

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Unauthorized: Valid administrator credentials required.",
        headers={"WWW-Authenticate": "ApiKey"},
    )


async def security_headers_middleware(request: Request, call_next):
    """Enforce defensive HTTP response headers required by DevSecOps policy."""
    response: Response = await call_next(request)

    # Core defensive headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Cache-Control"] = "no-store"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"

    # Content Security Policy (allows Tailwind CDN, FontAwesome, Lucide, HTMX)
    csp_directives = [
        "default-src 'self'",
        (
            "script-src 'self' 'unsafe-inline' "
            "https://cdn.tailwindcss.com https://cdnjs.cloudflare.com https://unpkg.com"
        ),
        (
            "style-src 'self' 'unsafe-inline' "
            "https://cdnjs.cloudflare.com https://fonts.googleapis.com"
        ),
        "font-src 'self' https://cdnjs.cloudflare.com https://fonts.gstatic.com",
        "img-src 'self' data: https:",
        "connect-src 'self'",
        "frame-ancestors 'none'",
    ]
    response.headers["Content-Security-Policy"] = "; ".join(csp_directives)

    return response
