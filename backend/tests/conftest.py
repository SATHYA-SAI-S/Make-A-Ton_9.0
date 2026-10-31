import sys
import os
import pytest
from fastapi.testclient import TestClient

# Ensure both repo root and backend directory are in sys.path
repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

os.environ["TESTING"] = "1"
os.environ["ENVIRONMENT"] = "testing"

# Import all models to ensure Base.metadata is completely populated across P1 & P2
import app.auth.models
import app.customers.models
import app.catalogue.models
import app.quotations.models
import app.subscriptions.models

import app.notifications.models
import app.taxes.models
import app.discounts.models
import app.billing.models
import app.invoices.models
import app.payments.models
import app.overdue.models
from app.taxes.models import BillingSettings
from app.shared.registry import get_port

from app.core.database import Base, engine, SessionLocal, get_db, create_all_tables
from app.core.security import hash_password, create_access_token
from app.auth.models import User
from app.customers.models import Customer
from app.main import app


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    os.environ["TESTING"] = "1"
    os.environ["ENVIRONMENT"] = "testing"


@pytest.fixture(autouse=True)
def auto_db_setup():
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)
    create_all_tables(bind=engine)
    db = SessionLocal()
    if BillingSettings is not None:
        if not db.query(BillingSettings).filter_by(id="default").first():
            db.add(BillingSettings(id="default", company_state_code="KA", company_name="Brightloop Software"))
            db.commit()
    db.close()

    if get_port is not None:
        try:
            sub_port = get_port("subscription")
            if hasattr(sub_port, "reset"):
                sub_port.reset()
            inv_port = get_port("invoice")
            if hasattr(inv_port, "reset"):
                inv_port.reset()
            cust_port = get_port("customer")
            if hasattr(cust_port, "reset"):
                cust_port.reset()
        except Exception:
            pass

    yield

    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db):
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def admin_user(db):
    user = User(
        email="admin_test@example.com",
        password_hash=hash_password("Admin@Pass1234"),
        role="admin",
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def admin_token(admin_user):
    return create_access_token(subject=str(admin_user.id), role="admin")


@pytest.fixture
def admin_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture
def staff_user(db):
    user = User(
        email="staff_test@example.com",
        password_hash=hash_password("Staff@Pass1234"),
        role="staff",
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def staff_token(staff_user):
    return create_access_token(subject=str(staff_user.id), role="staff")


@pytest.fixture
def staff_headers(staff_token):
    return {"Authorization": f"Bearer {staff_token}"}


@pytest.fixture
def customer_user(db):
    user = User(
        email="customer_test@example.com",
        password_hash=hash_password("Cust@Pass1234"),
        role="customer",
        is_active=True
    )
    db.add(user)
    db.flush()

    customer = Customer(
        user_id=user.id,
        name="Acme Corp Test",
        email=user.email,
        phone="+919876543210",
        country="India",
        timezone="Asia/Kolkata",
        status="active"
    )
    db.add(customer)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def customer_token(customer_user):
    return create_access_token(subject=str(customer_user.id), role="customer")


@pytest.fixture
def customer_headers(customer_token):
    return {"Authorization": f"Bearer {customer_token}"}

