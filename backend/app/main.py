import importlib
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

try:
    from app.core.config import settings
    from app.core.errors import register_error_handlers
    from app.core.database import engine, Base
except ImportError:
    from app.core.config import settings
    from app.core.errors import register_error_handlers
    from app.core.database import engine, Base

# Import Person 1 models
try:
    import app.auth.models
    import app.customers.models
    import app.catalogue.models
    import app.quotations.models
    import app.subscriptions.models
except ImportError:
    import app.auth.models
    import app.customers.models
    import app.catalogue.models
    import app.quotations.models
    import app.subscriptions.models

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

# Import Person 1 routers
try:
    from app.auth.router import auth_router, staff_router
    from app.admin.router import admin_router
    from app.customers.router import customers_router
    from app.catalogue.router import catalogue_router
    from app.quotations.router import quotations_router
    from app.subscriptions.router import subscriptions_router, internal_subscriptions_router
except ImportError:
    from app.auth.router import auth_router, staff_router
    from app.admin.router import admin_router
    from app.customers.router import customers_router
    from app.catalogue.router import catalogue_router
    from app.quotations.router import quotations_router
    from app.subscriptions.router import subscriptions_router, internal_subscriptions_router


def discover_modules(app_instance: FastAPI):
    """Auto-discover and bootstrap domain modules, mounting router if present."""
    app_pkg_path = Path(__file__).parent
    for item in app_pkg_path.iterdir():
        if item.is_dir() and not item.name.startswith(("_", ".")):
            module_name = item.name

            # 1. Run bootstrap if present
            for prefix in ("backend.app", "app"):
                try:
                    bootstrap_mod = importlib.import_module(f"{prefix}.{module_name}.bootstrap")
                    if hasattr(bootstrap_mod, "bootstrap"):
                        bootstrap_mod.bootstrap()
                    break
                except ModuleNotFoundError:
                    continue

            # 2. Mount router if present
            for prefix in ("backend.app", "app"):
                try:
                    router_mod = importlib.import_module(f"{prefix}.{module_name}.router")
                    if hasattr(router_mod, "router"):
                        app_instance.include_router(router_mod.router)
                    break
                except ModuleNotFoundError:
                    continue


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    discover_modules(app)
    yield


app = FastAPI(
    title=settings.PROJECT_NAME or settings.APP_NAME,
    version=settings.VERSION,
    description="SubscriptIQ Subscription-to-Cash Modular Monolith API",
    lifespan=lifespan
)

# Error Handlers
register_error_handlers(app)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.ENVIRONMENT == "development" else settings.CORS_ORIGINS,
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

# Also run discover_modules immediately at import time so routes are available before lifespan
discover_modules(app)

