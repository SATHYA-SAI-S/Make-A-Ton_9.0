import sys
import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Add backend to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.database import Base, get_db
from app.core.security import hash_password, create_access_token
from app.auth.models import User
from app.customers.models import Customer
from app.main import app

# In-memory SQLite database for fast, isolated test runs
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db():
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


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
