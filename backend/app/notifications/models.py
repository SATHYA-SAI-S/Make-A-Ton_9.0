from datetime import datetime, timezone
import uuid
from sqlalchemy import Column, String, Integer, Text, DateTime
from app.core.database import Base

def get_utc_now():
    return datetime.now(timezone.utc)

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    template = Column(String(100), nullable=False)
    recipient = Column(String(255), nullable=False)
    customer_id = Column(String(36), nullable=True)
    subject = Column(String(255), nullable=False)
    status = Column(String(20), default="QUEUED", nullable=False)  # QUEUED, SENT, FAILED
    attempts = Column(Integer, default=0, nullable=False)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=get_utc_now, nullable=False)
    sent_at = Column(DateTime(timezone=True), nullable=True)
