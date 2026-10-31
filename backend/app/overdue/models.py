import uuid
from datetime import datetime, timezone, date
from sqlalchemy import Column, String, Integer, Date, DateTime, Text
from backend.app.core.database import Base

def get_utc_now():
    return datetime.now(timezone.utc)

class PaymentFollowup(Base):
    __tablename__ = "payment_followups"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    invoice_id = Column(String(36), nullable=False, index=True)
    customer_id = Column(String(36), nullable=False, index=True)
    tier = Column(Integer, nullable=True)  # 1, 2, 3, or None for manual
    channel = Column(String(30), default="EMAIL", nullable=False)  # EMAIL, PHONE, SMS
    notes = Column(Text, nullable=True)
    promised_payment_date = Column(Date, nullable=True)
    status = Column(String(30), default="PENDING", nullable=False)  # PENDING, PROMISED, DISPUTED, RESOLVED
    created_at = Column(DateTime(timezone=True), default=get_utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=get_utc_now, onupdate=get_utc_now, nullable=False)
