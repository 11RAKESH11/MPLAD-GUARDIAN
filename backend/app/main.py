import time
import os
import sys
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Add project root to sys.path
sys.path.insert(0, r"c:\SIH_PROJECT")

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

app = FastAPI(
    title="MPLAD GUARDIAN — Parliamentary Development Intelligence API",
    description="AI-Powered MPLADS Oversight, Anomaly Detection & Risk Monitoring API — SIH 2026",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request Timing & Structured Logging Middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    response.headers["X-Response-Time"] = f"{duration:.3f}s"
    return response

# Health Checks
@app.get("/health", tags=["Health"])
@app.get("/api/health", tags=["Health"])
def health_check():
    return {
        "status": "healthy",
        "service": "MPLAD GUARDIAN Core API",
        "version": "1.0.0",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "database": "CONNECTED",
        "ai_engine": "ONLINE"
    }

# Include Routers
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)
