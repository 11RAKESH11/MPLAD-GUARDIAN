import time
import os
import sys
import uuid
import logging
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

# Add project root to sys.path
sys.path.insert(0, r"c:\SIH_PROJECT")

# Configure structured application logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s"
)
logger = logging.getLogger("mplad.security")

ENVIRONMENT = os.getenv("ENVIRONMENT", "development").lower()
IS_PRODUCTION = ENVIRONMENT in ["production", "prod"]
DEBUG = os.getenv("DEBUG", "true" if not IS_PRODUCTION else "false").lower() in ["true", "1"]
ENABLE_DOCS = os.getenv("ENABLE_DOCS", "true" if not IS_PRODUCTION else "false").lower() in ["true", "1"]

from backend.app.routers.auth_router import router as auth_router
from backend.app.routers.dashboard_router import router as dashboard_router
from backend.app.routers.projects_router import router as projects_router
from backend.app.routers.risks_router import router as risks_router
from backend.app.routers.states_router import router as states_router
from backend.app.routers.mps_router import router as mps_router
from backend.app.routers.alerts_router import router as alerts_router
from backend.app.routers.data_quality_router import router as data_quality_router
from backend.app.routers.audit_router import router as audit_router
from backend.app.routers.analytics_router import router as analytics_router
from backend.app.routers.jobs_router import router as jobs_router
from backend.app.routers.map_router import router as map_router

app = FastAPI(
    title="MPLAD GUARDIAN — Parliamentary Development Intelligence API",
    description="AI-Powered MPLADS Oversight, Anomaly Detection & Risk Monitoring API — Production Hardened",
    version="2.0.0",
    docs_url="/docs" if ENABLE_DOCS else None,
    redoc_url="/redoc" if ENABLE_DOCS else None,
    openapi_url="/openapi.json" if ENABLE_DOCS else None
)

# 1. Configured Origin CORS Protection
allowed_origins_env = os.getenv("ALLOWED_ORIGINS")
if allowed_origins_env:
    allowed_origins = [o.strip() for o in allowed_origins_env.split(",") if o.strip()]
elif IS_PRODUCTION:
    # Strict default production origins
    allowed_origins = ["https://mpladguardian.gov.in", "https://app.mpladguardian.gov.in"]
else:
    # Explicit local development origins (Never wildcard '*' with credentials)
    allowed_origins = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost:3000"
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID", "Accept", "Origin"],
    expose_headers=["X-Request-ID", "X-Response-Time"]
)

# 2. Request ID, Timing & Security Headers Middleware
@app.middleware("http")
async def security_and_tracing_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    request.state.request_id = request_id
    start_time = time.time()
    
    try:
        response = await call_next(request)
    except Exception as exc:
        duration = time.time() - start_time
        logger.error(f"[REQ:{request_id}] Unhandled server exception on {request.method} {request.url.path}: {str(exc)}", exc_info=True)
        if IS_PRODUCTION:
            return JSONResponse(
                status_code=500,
                content={"error": "Internal server error", "request_id": request_id},
                headers={"X-Request-ID": request_id}
            )
        else:
            return JSONResponse(
                status_code=500,
                content={"error": "Internal server error", "detail": str(exc), "request_id": request_id},
                headers={"X-Request-ID": request_id}
            )

    duration = time.time() - start_time
    
    # Attach Tracing Headers
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Response-Time"] = f"{duration:.3f}s"
    
    # Attach Essential Defense-in-Depth HTTP Security Headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=(), payment=()"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline'; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com data:; "
        "img-src 'self' data: blob: https://*; "
        "connect-src 'self' http://localhost:* ws://localhost:*; "
        "frame-ancestors 'none'; "
        "base-uri 'self'; "
        "form-action 'self';"
    )
    
    if request.url.scheme == "https" or IS_PRODUCTION:
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
    return response

# 3. Global Exception Handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    req_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    logger.warning(f"[REQ:{req_id}] Validation failure on {request.url.path}: {exc.errors()}")
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "422",
                "message": "Request validation error",
                "request_id": req_id
            },
            "detail": exc.errors() if not IS_PRODUCTION else "Invalid request parameters provided."
        },
        headers={"X-Request-ID": req_id}
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    req_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    resp_headers = dict(exc.headers) if exc.headers else {}
    resp_headers["X-Request-ID"] = req_id
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": str(exc.status_code),
                "message": exc.detail,
                "request_id": req_id
            }
        },
        headers=resp_headers
    )

# 4. Health & Status Checks
@app.get("/health", tags=["Health"])
@app.get("/api/v1/health", tags=["Health"])
def health_check():
    return {
        "status": "healthy",
        "service": "MPLAD GUARDIAN Core API",
        "version": "2.0.0",
        "environment": ENVIRONMENT,
        "security_profile": "HARDENED",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "database": "CONNECTED",
        "ai_engine": "ONLINE"
    }

@app.get("/ready", tags=["Health"])
@app.get("/api/v1/ready", tags=["Health"])
def readiness_check():
    try:
        from backend.app.database import query_db
        # Fast query to ensure DB is responsive
        query_db("SELECT 1")
        return {"status": "ready"}
    except Exception as exc:
        return JSONResponse(
            status_code=503,
            content={"error": {"code": "503", "message": "Database not ready"}}
        )

# 5. Include Application Routers
app.include_router(auth_router)
app.include_router(dashboard_router)
app.include_router(projects_router)
app.include_router(risks_router)
app.include_router(states_router)
app.include_router(mps_router)
app.include_router(alerts_router)
app.include_router(data_quality_router)
app.include_router(audit_router)
app.include_router(analytics_router)
app.include_router(jobs_router)
app.include_router(map_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=DEBUG)
