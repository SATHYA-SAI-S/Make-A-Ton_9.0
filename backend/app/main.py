import importlib
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.errors import register_error_handlers, SubscriptIQError
from app.core.database import engine, Base, create_all_tables

# Import Person 1 models
try:
    import app.auth.models
    import app.customers.models
    import app.catalogue.models
    import app.quotations.models
    import app.subscriptions.models
except ImportError:
    pass

# Import Person 2 models
try:
    import app.billing.models
    import app.invoices.models
    import app.taxes.models
    import app.discounts.models
    import app.payments.models
    import app.overdue.models
    import app.notifications.models
except ImportError:
    pass

# Import Person 3 models
try:
    import app.audit.models
    import app.portal.request_models
    import app.finance.models
    import app.revenue_guardian.models
    import app.analytics.models
except ImportError:
    pass

# Import Person 1 routers
try:
    from app.auth.router import auth_router, staff_router
    from app.admin.router import admin_router
    from app.customers.router import customers_router
    from app.catalogue.router import catalogue_router
    from app.quotations.router import quotations_router
    from app.subscriptions.router import subscriptions_router, internal_subscriptions_router
except ImportError:
    pass

EXPLICIT_ROUTERS = {
    "auth", "staff", "admin", "customers", "catalogue", "quotations", "subscriptions",
    "audit", "portal", "finance", "revenue_guardian", "reports"
}


def discover_modules(app_instance: FastAPI):
    """Auto-discover and bootstrap domain modules, mounting router if present and not explicitly mounted."""
    app_pkg_path = Path(__file__).parent
    for item in app_pkg_path.iterdir():
        if item.is_dir() and not item.name.startswith(("_", ".")):
            module_name = item.name

            # 1. Run bootstrap if present
            for prefix in ("app", "backend.app"):
                try:
                    bootstrap_mod = importlib.import_module(f"{prefix}.{module_name}.bootstrap")
                    if hasattr(bootstrap_mod, "bootstrap"):
                        bootstrap_mod.bootstrap()
                    break
                except ModuleNotFoundError:
                    continue

            # 2. Mount router if present and not explicitly registered
            if module_name not in EXPLICIT_ROUTERS:
                for prefix in ("app", "backend.app"):
                    try:
                        router_mod = importlib.import_module(f"{prefix}.{module_name}.router")
                        if hasattr(router_mod, "router"):
                            app_instance.include_router(router_mod.router)
                        break
                    except ModuleNotFoundError:
                        continue


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_all_tables(bind=engine)
    discover_modules(app)
    yield


app = FastAPI(
    title=settings.PROJECT_NAME or settings.APP_NAME,
    version=settings.VERSION,
    description="SubscriptIQ Subscription-to-Cash Modular Monolith API",
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    docs_url=f"{settings.API_V1_PREFIX}/docs",
    redoc_url=f"{settings.API_V1_PREFIX}/redoc",
    lifespan=lifespan
)

# Error Handlers
register_error_handlers(app)


@app.exception_handler(SubscriptIQError)
async def subscriptiq_error_handler(request: Request, exc: SubscriptIQError):
    return exc.to_response()


# CORS Middleware
cors_origins = getattr(settings, "BACKEND_CORS_ORIGINS", None) or getattr(settings, "CORS_ORIGINS", ["*"])
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.ENVIRONMENT == "development" else cors_origins,
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get(f"{settings.API_V1_PREFIX}/health", tags=["Health"])
def health_check():
    return {
        "status": "ok",
        "service": settings.PROJECT_NAME,
        "app": settings.APP_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT
    }


# Register Person 1 routers under API_V1_PREFIX
app.include_router(auth_router, prefix=settings.API_V1_PREFIX)
app.include_router(staff_router, prefix=settings.API_V1_PREFIX)
app.include_router(admin_router, prefix=settings.API_V1_PREFIX)
app.include_router(customers_router, prefix=settings.API_V1_PREFIX)
app.include_router(catalogue_router, prefix=settings.API_V1_PREFIX)
app.include_router(quotations_router, prefix=settings.API_V1_PREFIX)
app.include_router(subscriptions_router, prefix=settings.API_V1_PREFIX)
app.include_router(internal_subscriptions_router, prefix=settings.API_V1_PREFIX)

# Register Person 3 routers under API_V1_PREFIX
try:
    from app.audit.router import router as audit_router
    app.include_router(audit_router, prefix=f"{settings.API_V1_PREFIX}/audit", tags=["Audit"])
except ImportError as e:
    print(f"[MAIN] Warning: could not import audit_router: {e}")

try:
    from app.portal.router import router as portal_router
    app.include_router(portal_router, prefix=f"{settings.API_V1_PREFIX}/portal", tags=["Customer Portal"])
except ImportError as e:
    print(f"[MAIN] Warning: could not import portal_router: {e}")

try:
    from app.finance.router import router as finance_router
    app.include_router(finance_router, prefix=f"{settings.API_V1_PREFIX}/finance", tags=["Finance Intelligence"])
except ImportError as e:
    print(f"[MAIN] Warning: could not import finance_router: {e}")

try:
    from app.revenue_guardian.router import router as guardian_router
    app.include_router(guardian_router, prefix=f"{settings.API_V1_PREFIX}/guardian", tags=["Revenue Guardian"])
except ImportError as e:
    print(f"[MAIN] Warning: could not import guardian_router: {e}")

try:
    from app.reports.router import router as reports_router
    app.include_router(reports_router, prefix=f"{settings.API_V1_PREFIX}/reports", tags=["Financial Reports"])
except ImportError as e:
    print(f"[MAIN] Warning: could not import reports_router: {e}")

# Run discover_modules at import time to ensure routes from P2 and bootstraps from all roles are initialized
discover_modules(app)
