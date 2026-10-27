# ============================================================================
# Stage 1: Build & Dependency Wheel Generation
# ============================================================================
FROM python:3.13-slim-bookworm AS builder

# Prevent interactive prompts during package install
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /build

# Copy runtime requirements only
COPY requirements.txt .

# Install dependencies into a separate prefix for clean copying
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --prefix=/install -r requirements.txt

# ============================================================================
# Stage 2: Hardened Runtime Container
# ============================================================================
FROM python:3.13-slim-bookworm AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000 \
    APP_HOME=/app

# Create dedicated unprivileged user and group with explicit IDs
RUN groupadd -g 10001 appgroup && \
    useradd -u 10001 -g appgroup -s /sbin/nologin -M appuser

WORKDIR ${APP_HOME}

# Copy installed packages from builder stage
COPY --from=builder /install /usr/local

# Copy application source code
COPY --chown=appuser:appgroup app/ ${APP_HOME}/app/

# Remove write permissions from application code to prevent runtime tampering
RUN chmod -R 555 ${APP_HOME}

# Switch to unprivileged runtime user
USER 10001:10001

# Expose internal service port
EXPOSE 8000

# Container healthcheck using built-in Python standard library (no curl required)
HEALTHCHECK --interval=15s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; sys_exit = 0 if urllib.request.urlopen('http://127.0.0.1:8000/health').getcode() == 200 else 1; exit(sys_exit)"

# Launch Uvicorn with single worker in production mode
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--no-access-log"]
