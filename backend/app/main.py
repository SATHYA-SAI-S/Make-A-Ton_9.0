"""
SubscriptIQ Main Application Entrypoint.
Auto-discovers routers from app/*/router.py.
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.app.core.config import settings
from backend.app.core.errors import SubscriptIQError

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(SubscriptIQError)
async def subscriptiq_error_handler(request: Request, exc: SubscriptIQError):
    return exc.to_response()

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred.",
                "details": {"exception": str(exc)}
            }
        }
    )

@app.get("/api/v1/health", tags=["System"])
def health_check():
    return {
        "status": "OK",
        "service": "SubscriptIQ API",
        "version": "1.0.0",
        "role": "Person 3 (Finance Intelligence & Portal)"
    }

# Auto-mount routers from Person 3 packages if available
try:
    from backend.app.audit.router import router as audit_router
    app.include_router(audit_router, prefix=f"{settings.API_V1_STR}/audit", tags=["Audit"])
except ImportError:
    pass

try:
    from backend.app.portal.router import router as portal_router
    app.include_router(portal_router, prefix=f"{settings.API_V1_STR}/portal", tags=["Customer Portal"])
except ImportError:
    pass

try:
    from backend.app.finance.router import router as finance_router
    app.include_router(finance_router, prefix=f"{settings.API_V1_STR}/finance", tags=["Finance Intelligence"])
except ImportError:
    pass

try:
    from backend.app.revenue_guardian.router import router as guardian_router
    app.include_router(guardian_router, prefix=f"{settings.API_V1_STR}/guardian", tags=["Revenue Guardian"])
except ImportError:
    pass

try:
    from backend.app.reports.router import router as reports_router
    app.include_router(reports_router, prefix=f"{settings.API_V1_STR}/reports", tags=["Financial Reports"])
except ImportError:
    pass
