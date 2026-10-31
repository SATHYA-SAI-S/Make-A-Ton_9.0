import uuid
from datetime import datetime, timezone
from typing import Generator, Optional

from sqlalchemy import create_engine, Column, DateTime, String, Uuid
from sqlalchemy.orm import declarative_base, sessionmaker, Session, DeclarativeBase, Mapped, mapped_column

try:
    from app.core.config import settings
except ImportError:
    from app.core.config import settings

# Engine setup
connect_args = {"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_utc_now():
    return datetime.now(timezone.utc)


from sqlalchemy import func


class TimestampMixin:
    created_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=True
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=True
    )


class BaseModel(Base):
    __abstract__ = True

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    created_at = Column(DateTime(timezone=True), default=get_utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=get_utc_now, onupdate=get_utc_now, nullable=False)


class TimeStampedModel(Base):
    __abstract__ = True

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    created_at = Column(DateTime(timezone=True), default=get_utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=get_utc_now, onupdate=get_utc_now, nullable=False)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


_orig_create_all = Base.metadata.create_all
_orig_drop_all = Base.metadata.drop_all

def patched_create_all(*args, **kwargs):
    bind = kwargs.get("bind") or (args[0] if len(args) > 0 else None)
    _orig_create_all(*args, **kwargs)
    try:
        from app.finance.models import FinanceBase
        FinanceBase.metadata.create_all(bind=bind, checkfirst=True)
    except Exception as e:
        pass

def patched_drop_all(*args, **kwargs):
    bind = kwargs.get("bind") or (args[0] if len(args) > 0 else None)
    try:
        from app.finance.models import FinanceBase
        FinanceBase.metadata.drop_all(bind=bind, checkfirst=True)
    except Exception:
        pass
    _orig_drop_all(*args, **kwargs)

Base.metadata.create_all = patched_create_all
Base.metadata.drop_all = patched_drop_all

def create_all_tables(bind=None):
    Base.metadata.create_all(bind=bind or engine)


