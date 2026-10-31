import os
import pytest
from backend.app.core.database import Base, engine, SessionLocal
from backend.app.taxes.models import BillingSettings
from backend.app.shared.registry import get_port

# Import all models to ensure Base.metadata is completely populated
import backend.app.notifications.models
import backend.app.taxes.models
import backend.app.discounts.models
import backend.app.billing.models
import backend.app.invoices.models
import backend.app.payments.models
import backend.app.overdue.models

@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    os.environ["TESTING"] = "1"
    os.environ["ENVIRONMENT"] = "testing"

@pytest.fixture(autouse=True)
def auto_db_setup():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    if not db.query(BillingSettings).filter_by(id="default").first():
        db.add(BillingSettings(id="default", company_state_code="KA", company_name="Brightloop Software"))
        db.commit()
    db.close()

    sub_port = get_port("subscription")
    if hasattr(sub_port, "subscriptions"):
        sub_port.subscriptions.clear()

    yield

    Base.metadata.drop_all(bind=engine)
