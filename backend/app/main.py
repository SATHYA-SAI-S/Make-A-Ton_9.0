import importlib
import pkgutil
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.core.config import settings
from backend.app.core.errors import AppException, app_exception_handler
import backend.app

app = FastAPI(
    title=settings.APP_NAME,
    description="SubscriptIQ - Billing, Invoicing & Subscription Engine",
    version="1.0.0",
)

# Exception handlers
app.add_exception_handler(AppException, app_exception_handler)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/v1/health")
def health_check():
    return {"status": "ok", "app": settings.APP_NAME, "version": "1.0.0"}

# Auto-discover routers and bootstrap modules
def discover_modules():
    app_pkg_path = Path(__file__).parent
    for item in app_pkg_path.iterdir():
        if item.is_dir() and not item.name.startswith(("_", ".")):
            module_name = item.name
            
            # 1. Run bootstrap if present
            try:
                bootstrap_mod = importlib.import_module(f"backend.app.{module_name}.bootstrap")
                if hasattr(bootstrap_mod, "bootstrap"):
                    bootstrap_mod.bootstrap()
            except ModuleNotFoundError:
                pass

            # 2. Mount router if present
            try:
                router_mod = importlib.import_module(f"backend.app.{module_name}.router")
                if hasattr(router_mod, "router"):
                    app.include_router(router_mod.router)
            except ModuleNotFoundError:
                pass

discover_modules()
