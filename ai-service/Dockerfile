# Multi-stage / security-hardened Dockerfile for MPLAD GUARDIAN AI Service
FROM python:3.11-slim as runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    ENVIRONMENT=production \
    PYTHONPATH=/app

WORKDIR /app

# Install minimal OS dependencies for security and healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create dedicated non-root application user and group
RUN groupadd -g 10001 appgroup && \
    useradd -u 10001 -g appgroup -s /sbin/nologin -d /app appuser

# Copy requirements and install dependencies
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy existing AI source files with non-root ownership
# The ai-service directory contents are placed at /app
COPY --chown=appuser:appgroup . /app

# Create a proper package wrapper so uvicorn can find main:app
RUN echo "from main import app" > /app/__init__.py 2>/dev/null || true

# Switch to non-privileged user for runtime execution
USER appuser:appgroup

EXPOSE 8001

# Health check probe using the existing /health endpoint
HEALTHCHECK --interval=20s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8001/health || exit 1

# Start the existing FastAPI application
# Since PYTHONPATH=/app and code is at /app/main.py, use main:app directly
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
