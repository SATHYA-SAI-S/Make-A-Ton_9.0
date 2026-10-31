from datetime import date, timedelta
from decimal import Decimal
import pytest
from fastapi.testclient import TestClient

from app.core.database import Base, engine, SessionLocal
from app.shared.dto import CustomerDTO, TaxLineInputDTO
from app.taxes.models import TaxRule, BillingSettings, tax_rule_products
from app.taxes.service import compute_tax
from app.main import app

@pytest.fixture(autouse=True)
def setup_db():
    db = SessionLocal()
    # 18% standard GST rule
    gst_rule = TaxRule(
        name="GST 18%",
        rate=Decimal("18.00"),
        type="GST",
        effective_from=date.today() - timedelta(days=30),
        effective_to=None,
        active=True
    )
    db.add(gst_rule)
    db.commit()
    yield
    db.close()

def test_intra_state_split_cgst_sgst():
    # Customer located in same state (KA)
    cust_intra = CustomerDTO(id="c1", name="Local Client", email="loc@test.com", state_code="KA")
    lines = [
        TaxLineInputDTO(product_id="p1", quantity=2, unit_price=Decimal("1000.00"), discount_amount=Decimal("0.00"))
    ]
    # Total base = 2000.00
    # CGST 9% = 180.00, SGST 9% = 180.00
    breakdowns = compute_tax(lines, cust_intra, as_of=date.today())
    assert len(breakdowns) == 2
    types = {b.tax_type: b.tax_amount for b in breakdowns}
    assert types["CGST"] == Decimal("180.00")
    assert types["SGST"] == Decimal("180.00")

def test_inter_state_igst():
    # Customer located in different state (Maharashtra - MH)
    cust_inter = CustomerDTO(id="c2", name="Interstate Client", email="inter@test.com", state_code="MH")
    lines = [
        TaxLineInputDTO(product_id="p1", quantity=1, unit_price=Decimal("1000.00"), discount_amount=Decimal("100.00"))
    ]
    # Base after discount = 900.00
    # IGST 18% = 162.00
    breakdowns = compute_tax(lines, cust_inter, as_of=date.today())
    assert len(breakdowns) == 1
    assert breakdowns[0].tax_type == "IGST"
    assert breakdowns[0].tax_amount == Decimal("162.00")
    assert breakdowns[0].base_amount == Decimal("900.00")

def test_rule_effective_dates():
    db = SessionLocal()
    # Expired rule
    expired_rule = TaxRule(
        name="Old VAT",
        rate=Decimal("5.00"),
        type="VAT",
        effective_from=date(2020, 1, 1),
        effective_to=date(2021, 1, 1),
        active=True
    )
    db.add(expired_rule)
    db.commit()
    db.close()

    cust = CustomerDTO(id="c1", name="Client", email="c@test.com", state_code="KA")
    lines = [TaxLineInputDTO(product_id="p1", quantity=1, unit_price=Decimal("500.00"))]
    breakdowns = compute_tax(lines, cust, as_of=date.today())
    # Should not include Old VAT
    rule_names = [b.rule_name for b in breakdowns]
    assert not any("Old VAT" in name for name in rule_names)

def test_product_specific_applicability():
    db = SessionLocal()
    luxury_rule = TaxRule(
        name="Luxury Cess 12%",
        rate=Decimal("12.00"),
        type="OTHER",
        effective_from=date.today() - timedelta(days=10),
        active=True
    )
    db.add(luxury_rule)
    db.commit()
    db.refresh(luxury_rule)
    
    # Associate luxury rule only with product 'prod-luxury'
    db.execute(tax_rule_products.insert().values(rule_id=luxury_rule.id, product_id="prod-luxury"))
    db.commit()
    db.close()

    cust = CustomerDTO(id="c1", name="Client", email="c@test.com", state_code="MH")
    # Line 1: prod-standard (should NOT get luxury cess)
    # Line 2: prod-luxury (SHOULD get luxury cess)
    lines = [
        TaxLineInputDTO(product_id="prod-standard", quantity=1, unit_price=Decimal("1000.00")),
        TaxLineInputDTO(product_id="prod-luxury", quantity=1, unit_price=Decimal("2000.00"))
    ]
    breakdowns = compute_tax(lines, cust, as_of=date.today())
    luxury_items = [b for b in breakdowns if "Luxury Cess" in b.rule_name]
    assert len(luxury_items) == 1
    assert luxury_items[0].base_amount == Decimal("2000.00")
    assert luxury_items[0].tax_amount == Decimal("240.00")

def test_tax_preview_api():
    client = TestClient(app)
    payload = {
        "customer": {"id": "c1", "name": "API Client", "email": "api@test.com", "state_code": "MH"},
        "lines": [{"product_id": "p1", "quantity": 1, "unit_price": "500.00", "discount_amount": "0.00"}],
        "as_of": str(date.today())
    }
    response = client.post("/api/v1/taxes/preview", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert data[0]["tax_type"] == "IGST"
    assert data[0]["tax_amount"] == "90.00"
