# MPLAD GUARDIAN — Production Deployment Guide

**SIH 2026 | Problem Statement SIH26102**  
**Autonomous Public Expenditure Integrity & AI-Powered Anomaly Monitoring**

---

## 1. Prerequisites

### Local Development
- **Python**: 3.11+
- **Node.js**: 20+ (with npm 10+)
- **Git**: 2.30+

### Production Host / Cloud Instance
- **Docker Engine**: 24.0+
- **Docker Compose**: 2.20+
- **Hardware Minimum**: 2 vCPUs, 4 GB RAM, 20 GB SSD storage
- **Recommended Cloud Topology**: Managed PostgreSQL with PostGIS (e.g., AWS RDS / GCP Cloud SQL) + Managed Redis (e.g., AWS ElastiCache / GCP Memorystore).

---

## 2. Environment Configuration

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Generate a secure, cryptographically random JWT secret (minimum 32 bytes):
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(48))"
   ```

3. Update the `.env` file with production credentials:
   ```dotenv
   ENVIRONMENT=production
   DEBUG=false
   ENABLE_DOCS=false

   POSTGRES_DB=mplad_db
   POSTGRES_USER=app_user
   POSTGRES_PASSWORD=YOUR_STRONG_POSTGRES_PASSWORD
   DATABASE_URL=postgresql://app_user:YOUR_STRONG_POSTGRES_PASSWORD@postgres:5432/mplad_db

   REDIS_URL=redis://:YOUR_STRONG_REDIS_PASSWORD@redis:6379/0
   REDIS_PASSWORD=YOUR_STRONG_REDIS_PASSWORD

   JWT_SECRET=YOUR_GENERATED_JWT_SECRET_MIN_32_CHARS
   ALLOWED_ORIGINS=https://mpladguardian.gov.in,https://app.mpladguardian.gov.in
   AI_SERVICE_URL=http://ai-service:8001
   INTERNAL_SERVICE_TOKEN=YOUR_INTERNAL_SHARED_TOKEN
   ```

---

## 3. Deployment with Docker Compose (Recommended)

### 3.1 Build and Start All Services
```bash
docker compose up -d --build
```

### 3.2 Check Service Health & Status
```bash
docker compose ps
```
All containers should report `(healthy)`:
- `mplad-postgres` (Port 127.0.0.1:5432 -> 5432)
- `mplad-redis` (Internal Port 6379)
- `mplad-backend` (Port 127.0.0.1:8000 -> 8000)
- `mplad-worker` (Internal RQ daemon)
- `mplad-ai-service` (Internal Port 8001)
- `mplad-frontend` (Port 80 -> 80)

### 3.3 Migrate Real Data to PostgreSQL
Once the PostgreSQL container is healthy, run the migration engine from the host:
```bash
python scripts/migrate_sqlite_to_postgres.py --live \
  --dsn "postgresql://app_user:YOUR_STRONG_POSTGRES_PASSWORD@localhost:5432/mplad_db"
```

Verify target counts and financial aggregates:
```bash
python scripts/migrate_sqlite_to_postgres.py --verify \
  --dsn "postgresql://app_user:YOUR_STRONG_POSTGRES_PASSWORD@localhost:5432/mplad_db"
```

### 3.4 Run the Production Readiness Verifier
```bash
python scripts/verify_production_readiness.py
```

---

## 4. Local Development Startup (Without Docker)

### 4.1 Backend
```bash
cd C:\SIH_PROJECT
pip install -r ai-service/requirements.txt
pip install psycopg2-binary redis rq sqlalchemy uvicorn fastapi
uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```

### 4.2 AI Microservice
```bash
cd C:\SIH_PROJECT\ai-service
uvicorn main:app --host 127.0.0.1 --port 8001 --reload
```

### 4.3 Frontend
```bash
cd C:\SIH_PROJECT\frontend
npm install
npm run dev
```
Open [http://localhost:5173](http://localhost:5173) in your browser.

---

## 5. Cloud Production Architecture (AWS / GCP / Azure)

For enterprise high-availability and scale:

1. **Managed Database (RDS / Cloud SQL)**:
   - PostgreSQL 15+ engine with `postgis` extension enabled:
     ```sql
     CREATE EXTENSION IF NOT EXISTS postgis;
     ```
   - Connect via VPC peering / private subnet.
2. **Managed Redis (ElastiCache / Memorystore)**:
   - Redis 7.0+ with TLS and AUTH token.
3. **Application Containers (ECS Fargate / Cloud Run / Kubernetes)**:
   - Build backend, AI service, worker, and frontend images:
     ```bash
     docker build -f Dockerfile.backend -t myregistry.azurecr.io/mplad-backend:latest .
     docker build -f ai-service/Dockerfile -t myregistry.azurecr.io/mplad-ai:latest ./ai-service
     docker build -f Dockerfile.worker -t myregistry.azurecr.io/mplad-worker:latest .
     docker build -f frontend/Dockerfile.frontend -t myregistry.azurecr.io/mplad-frontend:latest ./frontend
     ```
4. **Ingress & TLS**:
   - Ingress controller / ALB terminating HTTPS (Let's Encrypt / AWS ACM certificate).
   - Route `/` to `mplad-frontend` service.
   - Route `/api/` to `mplad-backend` service.

---

## 6. Observability & Health Check Endpoints

| Service | Endpoint | Success Response | Usage |
|---|---|---|---|
| **Backend Live** | `GET /api/v1/health` | `{"status": "healthy"}` | Liveness probe |
| **Backend Ready**| `GET /api/v1/ready` | `{"status": "ready", "database": "healthy"}` | Readiness probe |
| **AI Service** | `GET /health` | `{"status": "healthy"}` | AI microservice probe |
| **Frontend** | `GET /` | HTTP 200 (HTML) | Web ingress probe |

---

## 7. Troubleshooting & Recovery Runbook

### Issue 1: Backend exits with "Production environment requires a valid PostgreSQL DATABASE_URL"
- **Cause**: `ENVIRONMENT=production` is set, but `DATABASE_URL` is empty or uses SQLite.
- **Remedy**: Set `DATABASE_URL=postgresql://app_user:password@postgres:5432/mplad_db` in `.env`.

### Issue 2: PostgreSQL migration fails with connection timeout
- **Cause**: Postgres container is initializing or port 5432 is blocked.
- **Remedy**: Check container logs: `docker compose logs postgres`. Ensure PostGIS extension is ready.

### Issue 3: Redis queue fallback message in logs
- **Cause**: Redis server is unreachable.
- **Remedy**: Backend automatically runs jobs with in-process threading fallback; verify Redis credentials in `REDIS_URL`.
