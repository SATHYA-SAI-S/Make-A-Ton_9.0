import sys
import os

# Ensure backend root is on path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import select, func
from app.core.config import settings
from app.core.database import SessionLocal, Base, engine
from app.core.security import hash_password

# Import all models so relationships resolve properly
import app.auth.models
import app.customers.models
import app.catalogue.models
import app.quotations.models
import app.subscriptions.models
from app.auth.models import User


def seed_admin():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        admin_email = settings.SEED_ADMIN_EMAIL.lower().strip()
        existing = db.scalar(select(User).where(func.lower(User.email) == admin_email))
        if existing:
            print(f"[Seed] Admin user already exists: {admin_email}")
            return existing

        admin = User(
            email=admin_email,
            password_hash=hash_password(settings.SEED_ADMIN_PASSWORD),
            role="admin",
            is_active=True
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)
        print(f"[Seed] Successfully created default Admin user: {admin_email}")
        return admin
    finally:
        db.close()


if __name__ == "__main__":
    seed_admin()
