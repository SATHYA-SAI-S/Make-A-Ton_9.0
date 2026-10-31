from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from pydantic import BaseModel

from app.core.database import get_db
from app.auth.models import User
from app.auth.deps import require_roles
from app.customers.models import Customer
from app.catalogue.models import Product, Plan
from app.quotations.models import Quotation
from app.subscriptions.models import Subscription


class AdminStatsResponse(BaseModel):
    total_customers: int
    total_staff: int
    total_products: int
    total_plans: int
    total_quotations: int
    total_subscriptions: int
    active_subscriptions: int
    paused_subscriptions: int
    closed_subscriptions: int


admin_router = APIRouter(prefix="/admin", tags=["Admin Overview"])


@admin_router.get("/stats", response_model=AdminStatsResponse)
def get_admin_stats(
    current_user: User = Depends(require_roles("admin")),
    db: Session = Depends(get_db)
):
    """Retrieve system-wide KPIs and entity counts (Admin only)."""
    total_customers = db.scalar(select(func.count()).select_from(Customer)) or 0
    total_staff = db.scalar(select(func.count()).select_from(User).where(User.role == "staff")) or 0
    total_products = db.scalar(select(func.count()).select_from(Product)) or 0
    total_plans = db.scalar(select(func.count()).select_from(Plan)) or 0
    total_quotations = db.scalar(select(func.count()).select_from(Quotation)) or 0
    total_subscriptions = db.scalar(select(func.count()).select_from(Subscription)) or 0
    active_subscriptions = db.scalar(select(func.count()).select_from(Subscription).where(Subscription.status == "ACTIVE")) or 0
    paused_subscriptions = db.scalar(select(func.count()).select_from(Subscription).where(Subscription.status == "PAUSED")) or 0
    closed_subscriptions = db.scalar(select(func.count()).select_from(Subscription).where(Subscription.status == "CLOSED")) or 0

    return AdminStatsResponse(
        total_customers=total_customers,
        total_staff=total_staff,
        total_products=total_products,
        total_plans=total_plans,
        total_quotations=total_quotations,
        total_subscriptions=total_subscriptions,
        active_subscriptions=active_subscriptions,
        paused_subscriptions=paused_subscriptions,
        closed_subscriptions=closed_subscriptions
    )
