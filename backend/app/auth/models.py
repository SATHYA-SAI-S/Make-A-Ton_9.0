import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import String, Boolean, DateTime, Uuid, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, TimestampMixin


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(50), default="customer", nullable=False)  # admin, staff, customer
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    reset_token_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    reset_token_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    customer: Mapped[Optional["Customer"]] = relationship("Customer", back_populates="user", uselist=False)

    __table_args__ = (
        Index("ix_users_email_lower", "email"),
    )
