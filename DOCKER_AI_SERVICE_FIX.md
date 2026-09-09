# MPLAD GUARDIAN — Docker AI Service Fix Report

## 1. Root Cause
The `docker-compose.yml` service definition for `ai-service` referenced:
```yaml
ai-service:
  build:
    context: ./ai-service
    dockerfile: Dockerfile
```
However, `C:\SIH_PROJECT\ai-service\Dockerfile` was missing from the repository, causing `docker compose build ai-service` to fail.

---

## 2. Dockerfile Created
Created `/ai-service/Dockerfile` adhering to production-ready multi-stage / security-hardened standards:
- Base Image: `python:3.11-slim`
- Working Directory: `/app`
- Non-root user: `appuser:appgroup` (UID/GID 10001)
- Security: `no-new-privileges` compatible, unprivileged execution
- Python Path: `PYTHONPATH=/` to ensure package relative import compatibility (`from .risk_engine import ...`)
- Dependency caching: Layered `requirements.txt` installation before source code copy
- Healthcheck: Native container health probing against `/health`

```dockerfile
# Multi-stage / security-hardened Dockerfile for MPLAD GUARDIAN AI Service
FROM python:3.11-slim as runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    ENVIRONMENT=production \
    PYTHONPATH=/

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
COPY --chown=appuser:appgroup . /app

# Switch to non-privileged user for runtime execution
USER appuser:appgroup

EXPOSE 8001

# Health check probe using the existing /health endpoint
HEALTHCHECK --interval=20s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8001/health || exit 1

# Start the existing FastAPI application without reload
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
```

---

## 3. Startup Command
```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8001
```
- No reload flag is used (`--reload` omitted).
- Bound to host `0.0.0.0` and port `8001`.

---

## 4. Health Endpoint
- **URL**: `http://localhost:8001/health`
- **Method**: `GET`
- **Response**:
```json
{
  "status": "healthy",
  "service": "MPLAD GUARDIAN AI Microservice",
  "model_version": "guardian-risk-2.0.0-shadow",
  "algorithm_version": "2.1.0",
  "timestamp": "2026-08-28 18:37:41"
}
```

---

## 5. Dependencies
From `ai-service/requirements.txt`:
- `fastapi>=0.111.0`
- `uvicorn>=0.30.1`
- `pydantic>=2.7.1`
- `numpy>=1.26.0`
- `scikit-learn>=1.4.0`
- `scipy>=1.13.0`
- `requests>=2.31.0`
- `argon2-cffi>=23.1.0`

---

## 6. Build Results

### A. AI Service Targeted Build
```bash
docker compose build ai-service
```
- **Result**: `SUCCESS` (Exit Code 0)
- **Tagged**: `sih_project-ai-service:latest`

### B. Compose Configuration Validation
```bash
docker compose config
```
- **Result**: `VALID` (Parsed all services including `ai-service` correctly)

### C. Full Project Build
```bash
docker compose build
```
- **Result**: `SUCCESS` (Exit Code 0)
- Built Images:
  - `sih_project-worker:latest`
  - `sih_project-ai-service:latest`
  - `sih_project-backend:latest`
  - `sih_project-frontend:latest`

---

## 7. Test Results
1. **Container Startup**: `docker compose up -d ai-service` — Started container `mplad-ai-service`.
2. **Container Health Check Probe**: `docker inspect --format="{{json .State.Health}}" mplad-ai-service` — Evaluated `Status: healthy`, Exit Code `0`.
3. **Endpoint Validation (`GET /health`)**:
   - Status: `200 OK`
   - Payload: `{"status":"healthy","service":"MPLAD GUARDIAN AI Microservice","model_version":"guardian-risk-2.0.0-shadow","algorithm_version":"2.1.0", ...}`
4. **Model Registry Validation (`GET /models`)**:
   - Status: `200 OK`
   - Active models returned: `guardian-risk-engine` (Components: Hierarchical Cost Anomaly, Multi-Signal Duplicate Detection, Progress Gap Rule Engine, Geographic Concentration).
