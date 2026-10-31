import uuid
from typing import Optional, List
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import select, desc

from app.core.database import get_db
from app.auth.models import User
from app.auth.deps import get_current_user, require_roles
from app.catalogue.models import Product, Plan, PlanVersion
from app.catalogue.schemas import (
    ProductCreate,
    ProductUpdate,
    ProductResponse,
    ProductVariantCreate,
    ProductVariantUpdate,
    ProductVariantResponse,
    PlanCreate,
    PlanUpdate,
    PlanResponse,
    PlanVersionResponse,
    PlanPriceChangeRequest
)
from app.catalogue import service

catalogue_router = APIRouter(tags=["Catalogue & Plans"])


# Products Endpoints

@catalogue_router.get("/products", response_model=List[ProductResponse])
def list_products(
    is_active: Optional[bool] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all products in catalogue."""
    return service.list_products(db, is_active=is_active)


@catalogue_router.post("/products", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
def create_product(
    request: ProductCreate,
    current_user: User = Depends(require_roles("admin")),
    db: Session = Depends(get_db)
):
    """Create a new product with optional variants (Admin only)."""
    return service.create_product(db, request, current_user)


@catalogue_router.get("/products/{product_id}", response_model=ProductResponse)
def get_product(
    product_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve product by ID."""
    return service.get_product(db, product_id)


@catalogue_router.patch("/products/{product_id}", response_model=ProductResponse)
def update_product(
    product_id: uuid.UUID,
    request: ProductUpdate,
    current_user: User = Depends(require_roles("admin")),
    db: Session = Depends(get_db)
):
    """Update product details (Admin only)."""
    return service.update_product(db, product_id, request, current_user)


@catalogue_router.post("/products/{product_id}/variants", response_model=ProductVariantResponse, status_code=status.HTTP_201_CREATED)
def add_product_variant(
    product_id: uuid.UUID,
    request: ProductVariantCreate,
    current_user: User = Depends(require_roles("admin")),
    db: Session = Depends(get_db)
):
    """Add a variant with price adjustment to a product (Admin only)."""
    return service.add_product_variant(db, product_id, request, current_user)


@catalogue_router.patch("/variants/{variant_id}", response_model=ProductVariantResponse)
def update_product_variant(
    variant_id: uuid.UUID,
    request: ProductVariantUpdate,
    current_user: User = Depends(require_roles("admin")),
    db: Session = Depends(get_db)
):
    """Update variant price adjustment or name (Admin only)."""
    return service.update_product_variant(db, variant_id, request, current_user)


# Plans & Pricing Endpoints

@catalogue_router.get("/plans", response_model=List[PlanResponse])
def list_plans(
    status: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List subscription plans with current versioned price."""
    return service.list_plans(db, status=status)


@catalogue_router.post("/plans", response_model=PlanResponse, status_code=status.HTTP_201_CREATED)
def create_plan(
    request: PlanCreate,
    current_user: User = Depends(require_roles("admin")),
    db: Session = Depends(get_db)
):
    """Create a subscription plan with initial price version (Admin only)."""
    return service.create_plan(db, request, current_user)


@catalogue_router.get("/plans/{plan_id}", response_model=PlanResponse)
def get_plan(
    plan_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve subscription plan by ID."""
    plan = service.get_plan(db, plan_id)
    return service.get_plan_response(db, plan)


@catalogue_router.patch("/plans/{plan_id}", response_model=PlanResponse)
def update_plan(
    plan_id: uuid.UUID,
    request: PlanUpdate,
    current_user: User = Depends(require_roles("admin")),
    db: Session = Depends(get_db)
):
    """Update plan rules, dates, or permission toggles (Admin only)."""
    return service.update_plan(db, plan_id, request, current_user)


@catalogue_router.post("/plans/{plan_id}/price", response_model=PlanVersionResponse, status_code=status.HTTP_201_CREATED)
def change_plan_price(
    plan_id: uuid.UUID,
    request: PlanPriceChangeRequest,
    current_user: User = Depends(require_roles("admin")),
    db: Session = Depends(get_db)
):
    """Create a new immutable price version for a plan (Admin only)."""
    return service.change_plan_price(db, plan_id, request, current_user)


@catalogue_router.get("/plans/{plan_id}/versions", response_model=List[PlanVersionResponse])
def get_plan_versions(
    plan_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve complete immutable price version history for a plan."""
    service.get_plan(db, plan_id)  # verify existence
    versions = list(db.scalars(
        select(PlanVersion)
        .where(PlanVersion.plan_id == plan_id)
        .order_by(desc(PlanVersion.version_no))
    ).all())
    return [PlanVersionResponse.model_validate(v) for v in versions]
