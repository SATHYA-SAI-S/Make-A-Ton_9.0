from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from pydantic import BaseModel
from datetime import datetime

from backend.app.core.database import get_db
from backend.app.core.security import require_roles, UserContext
from backend.app.core.pagination import PaginatedResponse
from backend.app.notifications.models import Notification

router = APIRouter(prefix="/api/v1/notifications", tags=["Notifications"])

class NotificationItem(BaseModel):
    id: str
    template: str
    recipient: str
    customer_id: Optional[str]
    subject: str
    status: str
    attempts: int
    error: Optional[str]
    created_at: datetime
    sent_at: Optional[datetime]

    model_config = {'from_attributes': True}

@router.get("", response_model=PaginatedResponse[NotificationItem])
def list_notifications(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None),
    recipient: Optional[str] = Query(None),
    user: UserContext = Depends(require_roles("admin", "staff")),
    db: Session = Depends(get_db)
):
    query = db.query(Notification)
    if status:
        query = query.filter(Notification.status == status)
    if recipient:
        query = query.filter(Notification.recipient.ilike(f"%{recipient}%"))

    total = query.count()
    items = query.order_by(desc(Notification.created_at)).offset((page - 1) * page_size).limit(page_size).all()

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size
    )
