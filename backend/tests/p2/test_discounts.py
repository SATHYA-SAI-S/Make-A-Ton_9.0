from datetime import date, timedelta
from decimal import Decimal
import pytest
from fastapi.testclient import TestClient

from app.core.database import Base, engine, SessionLocal
from app.shared.dto import TaxLineInputDTO
from app.discounts.models import DiscountRule
from app.discounts.service import eligible_discounts, record_redemption, mark_expired_rules
from app.main import app

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

def test_expired_discount_rejected():
    db = SessionLocal()
    rule = DiscountRule(
        name="Summer Deal",
        type="PERCENT",
        value=Decimal("20.00"),
        start_date=date.today() - timedelta(days=60),
        end_date=date.today() - timedelta(days=1),  # Expired yesterday
        scope="SUBSCRIPTION",
        status="ACTIVE"
    )
    db.add(rule)
    db.commit()

    lines = [TaxLineInputDTO(product_id="p1", quantity=1, unit_price=Decimal("1000.00"))]
    eligible = eligible_discounts(lines, as_of=date.today(), db=db)
    assert len(eligible) == 0

    # Auto-expiry helper updates status
    count = mark_expired_rules(db)
    assert count == 1
    db.refresh(rule)
    assert rule.status == "EXPIRED"
    db.close()

def test_minimum_purchase_and_quantity():
    db = SessionLocal()
    rule = DiscountRule(
        name="Bulk Order Tier",
        type="FIXED",
        value=Decimal("200.00"),
        min_purchase=Decimal("1500.00"),
        min_quantity=3,
        start_date=date.today() - timedelta(days=5),
        scope="SUBSCRIPTION",
        status="ACTIVE"
    )
    db.add(rule)
    db.commit()

    # Case A: Below min purchase and min quantity
    lines_small = [TaxLineInputDTO(product_id="p1", quantity=2, unit_price=Decimal("500.00"))] # total 1000, qty 2
    assert len(eligible_discounts(lines_small, as_of=date.today(), db=db)) == 0

    # Case B: Meets both conditions (qty 3, total 1500)
    lines_qualify = [TaxLineInputDTO(product_id="p1", quantity=3, unit_price=Decimal("500.00"))]
    eligible = eligible_discounts(lines_qualify, as_of=date.today(), db=db)
    assert len(eligible) == 1
    assert eligible[0].amount == Decimal("200.00")
    db.close()

def test_max_usage_limit():
    db = SessionLocal()
    rule = DiscountRule(
        name="First 2 Customers",
        type="FIXED",
        value=Decimal("50.00"),
        max_usage=2,
        used_count=0,
        start_date=date.today(),
        scope="SUBSCRIPTION",
        status="ACTIVE"
    )
    db.add(rule)
    db.commit()

    lines = [TaxLineInputDTO(product_id="p1", quantity=1, unit_price=Decimal("500.00"))]

    # Usage 1
    record_redemption(rule.id, Decimal("50.00"), db=db)
    assert len(eligible_discounts(lines, as_of=date.today(), db=db)) == 1

    # Usage 2
    record_redemption(rule.id, Decimal("50.00"), db=db)
    # Reached limit (used_count = 2, max_usage = 2)
    assert len(eligible_discounts(lines, as_of=date.today(), db=db)) == 0
    db.close()

def test_discount_performance_api():
    db = SessionLocal()
    rule = DiscountRule(
        name="Launch Promo",
        type="FIXED",
        value=Decimal("100.00"),
        start_date=date.today(),
        status="ACTIVE"
    )
    db.add(rule)
    db.commit()
    record_redemption(rule.id, Decimal("100.00"), db=db)
    db.close()

    client = TestClient(app)
    response = client.get("/api/v1/discounts/performance", headers={"x-user-role": "admin"})
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    item = [d for d in data if d["rule_name"] == "Launch Promo"][0]
    assert item["redemptions_count"] == 1
    assert item["total_discount_amount"] == "100.00"
