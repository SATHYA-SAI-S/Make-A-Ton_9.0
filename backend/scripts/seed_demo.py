import sys
import os
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

# Ensure backend root is on path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import select, func
from app.core.database import SessionLocal, Base, engine
from app.core.security import hash_password
import app.auth.models
import app.customers.models
import app.catalogue.models
import app.quotations.models
import app.subscriptions.models

from app.auth.models import User
from app.customers.models import Customer
from app.catalogue.models import Product, ProductVariant, Plan, PlanVersion
from app.quotations.models import QuotationTemplate, QuotationTemplateLine, Quotation, QuotationLine
from app.subscriptions.models import Subscription, SubscriptionLine, SubscriptionEvent


def seed_demo_data():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        print("[Seed] Seeding SubscriptIQ demo dataset...")
        today = date.today()

        # 1. Admin User
        admin = db.scalar(select(User).where(func.lower(User.email) == "admin@example.com"))
        if not admin:
            admin = User(
                email="admin@example.com",
                password_hash=hash_password("Admin@Secure123!"),
                role="admin",
                is_active=True
            )
            db.add(admin)
            db.flush()
            print("  Created Admin: admin@example.com")

        # 2. Staff User
        staff = db.scalar(select(User).where(func.lower(User.email) == "staff@example.com"))
        if not staff:
            staff = User(
                email="staff@example.com",
                password_hash=hash_password("Staff@Secure123!"),
                role="staff",
                is_active=True
            )
            db.add(staff)
            db.flush()
            print("  Created Staff: staff@example.com")

        # 3. Customer 1: Acme Enterprise Corp (with Portal Login)
        cust1_user = db.scalar(select(User).where(func.lower(User.email) == "acme@example.com"))
        if not cust1_user:
            cust1_user = User(
                email="acme@example.com",
                password_hash=hash_password("Customer@Secure123!"),
                role="customer",
                is_active=True
            )
            db.add(cust1_user)
            db.flush()

        cust1 = db.scalar(select(Customer).where(func.lower(Customer.email) == "acme@example.com"))
        if not cust1:
            cust1 = Customer(
                user_id=cust1_user.id,
                name="Acme Enterprise Corp",
                email="acme@example.com",
                phone="+919876543210",
                billing_contact="John Acme",
                address_line1="100 Tech Park Avenue",
                city="Bengaluru",
                state="Karnataka",
                postal_code="560100",
                country="India",
                timezone="Asia/Kolkata",
                tax_id="29ABCDE1234F1Z5",
                status="active"
            )
            db.add(cust1)
            db.flush()
            print("  Created Customer 1: Acme Enterprise Corp (acme@example.com)")

        # 4. Customer 2: Beta Innovations Ltd (with Portal Login)
        cust2_user = db.scalar(select(User).where(func.lower(User.email) == "beta@example.com"))
        if not cust2_user:
            cust2_user = User(
                email="beta@example.com",
                password_hash=hash_password("Customer@Secure123!"),
                role="customer",
                is_active=True
            )
            db.add(cust2_user)
            db.flush()

        cust2 = db.scalar(select(Customer).where(func.lower(Customer.email) == "beta@example.com"))
        if not cust2:
            cust2 = Customer(
                user_id=cust2_user.id,
                name="Beta Innovations Ltd",
                email="beta@example.com",
                phone="+919876543211",
                billing_contact="Sarah Beta",
                address_line1="45 Silicon Boulevard",
                city="Hyderabad",
                state="Telangana",
                postal_code="500081",
                country="India",
                timezone="Asia/Kolkata",
                tax_id="36AABCB1234F1Z2",
                status="active"
            )
            db.add(cust2)
            db.flush()
            print("  Created Customer 2: Beta Innovations Ltd (beta@example.com)")

        # 5. Products & Variants
        prod_erp = db.scalar(select(Product).where(Product.name == "Cloud ERP Suite"))
        if not prod_erp:
            prod_erp = Product(
                name="Cloud ERP Suite",
                type="service",
                sales_price=Decimal("2000.00"),
                cost_price=Decimal("750.00"),
                notes="Integrated ERP for procurement, catalogue, and finance",
                is_active=True,
                currency="INR"
            )
            db.add(prod_erp)
            db.flush()

            v1 = ProductVariant(product_id=prod_erp.id, name="Standard Edition", price_adjustment=Decimal("0.00"))
            v2 = ProductVariant(product_id=prod_erp.id, name="Odoo Pro Edition", price_adjustment=Decimal("560.00"))
            db.add_all([v1, v2])
            db.flush()
            print("  Created Product: Cloud ERP Suite (Variants: Standard, Odoo Pro)")

        prod_support = db.scalar(select(Product).where(Product.name == "Dedicated Support SLA"))
        if not prod_support:
            prod_support = Product(
                name="Dedicated Support SLA",
                type="service",
                sales_price=Decimal("1500.00"),
                cost_price=Decimal("400.00"),
                notes="Priority 24/7 technical hotline",
                is_active=True,
                currency="INR"
            )
            db.add(prod_support)
            db.flush()

            v3 = ProductVariant(product_id=prod_support.id, name="Standard SLA (8x5)", price_adjustment=Decimal("0.00"))
            v4 = ProductVariant(product_id=prod_support.id, name="24/7 Dedicated Concierge", price_adjustment=Decimal("800.00"))
            db.add_all([v3, v4])
            db.flush()
            print("  Created Product: Dedicated Support SLA")

        # 6. Plans & Versions
        plan_monthly = db.scalar(select(Plan).where(Plan.name == "Growth Monthly"))
        if not plan_monthly:
            plan_monthly = Plan(
                name="Growth Monthly",
                billing_frequency="monthly",
                min_quantity=2,
                available_from=today - timedelta(days=60),
                available_to=today + timedelta(days=365),
                allow_pause=True,
                allow_early_close=True,
                allow_renewal=True,
                status="active"
            )
            db.add(plan_monthly)
            db.flush()

            pv1 = PlanVersion(plan_id=plan_monthly.id, version_no=1, price=Decimal("4999.00"))
            db.add(pv1)
            db.flush()
            print("  Created Plan: Growth Monthly (Version 1: 4999.00)")

        plan_annual = db.scalar(select(Plan).where(Plan.name == "Enterprise Annual"))
        if not plan_annual:
            plan_annual = Plan(
                name="Enterprise Annual",
                billing_frequency="yearly",
                min_quantity=1,
                available_from=today - timedelta(days=60),
                available_to=today + timedelta(days=365),
                allow_pause=True,
                allow_early_close=True,
                allow_renewal=True,
                status="active"
            )
            db.add(plan_annual)
            db.flush()

            pv2 = PlanVersion(plan_id=plan_annual.id, version_no=1, price=Decimal("49999.00"))
            db.add(pv2)
            db.flush()
            print("  Created Plan: Enterprise Annual (Version 1: 49999.00)")

        # 7. Quotation Template
        tpl = db.scalar(select(QuotationTemplate).where(QuotationTemplate.name == "Standard ERP Onboarding"))
        if not tpl:
            tpl = QuotationTemplate(
                name="Standard ERP Onboarding",
                default_plan_id=plan_monthly.id,
                validity_days=30,
                payment_terms="Net 30",
                is_active=True
            )
            db.add(tpl)
            db.flush()
            tl = QuotationTemplateLine(
                template_id=tpl.id,
                product_id=prod_erp.id,
                quantity=2
            )
            db.add(tl)
            db.flush()
            print("  Created Template: Standard ERP Onboarding")

        # 8. Subscription 1: Due Today for Acme Corp (Ready for Person 2 Billing Worker)
        sub_due = db.scalar(select(Subscription).where(Subscription.subscription_number == "SUB-2026-DEMO01"))
        if not sub_due:
            # Create confirmed quote first
            q1 = Quotation(
                number="QTN-2026-DEMO01",
                customer_id=cust1.id,
                plan_id=plan_monthly.id,
                plan_version_id=plan_monthly.versions[0].id,
                status="confirmed",
                valid_until=today + timedelta(days=30),
                payment_terms="Net 30",
                subtotal=Decimal("5120.00"),
                tax_amount=Decimal("0.00"),
                total=Decimal("5120.00"),
                currency="INR",
                created_by=admin.id
            )
            db.add(q1)
            db.flush()

            # Active Subscription with next_billing_at = today
            sub_due = Subscription(
                subscription_number="SUB-2026-DEMO01",
                customer_id=cust1.id,
                plan_id=plan_monthly.id,
                plan_version_id=plan_monthly.versions[0].id,
                quotation_id=q1.id,
                status="active",
                start_date=today - timedelta(days=30),
                end_date=today + timedelta(days=335),
                payment_terms="Net 30",
                next_billing_at=today,  # Due today!
                billing_anchor_day=(today - timedelta(days=30)).day,
                currency="INR",
                total_amount=Decimal("5120.00"),
                created_by=admin.id
            )
            db.add(sub_due)
            db.flush()

            # Add lines
            sline = SubscriptionLine(
                subscription_id=sub_due.id,
                product_id=prod_erp.id,
                variant_id=prod_erp.variants[1].id,  # Odoo Pro: 2000 + 560 = 2560
                description="Cloud ERP Suite - Odoo Pro Edition",
                quantity=2,
                unit_price=Decimal("2560.00"),
                line_total=Decimal("5120.00")
            )
            db.add(sline)

            # Events
            ev1 = SubscriptionEvent(
                subscription_id=sub_due.id,
                actor_id=admin.id,
                from_state="quotation",
                to_state="confirmed",
                reason="Confirmed demo quotation QTN-2026-DEMO01"
            )
            ev2 = SubscriptionEvent(
                subscription_id=sub_due.id,
                actor_id=admin.id,
                from_state="confirmed",
                to_state="active",
                reason="Activated for scheduled billing demo"
            )
            db.add_all([ev1, ev2])
            print("  Created Active Due Subscription: SUB-2026-DEMO01 (Due today for Acme Corp)")

        # 9. Expired Quotation (for testing admin validity extension)
        q_exp = db.scalar(select(Quotation).where(Quotation.number == "QTN-2026-EXPIRED"))
        if not q_exp:
            q_exp = Quotation(
                number="QTN-2026-EXPIRED",
                customer_id=cust2.id,
                plan_id=plan_monthly.id,
                plan_version_id=plan_monthly.versions[0].id,
                status="expired",
                valid_until=today - timedelta(days=5),
                payment_terms="Net 15",
                subtotal=Decimal("4000.00"),
                tax_amount=Decimal("0.00"),
                total=Decimal("4000.00"),
                currency="INR",
                created_by=staff.id
            )
            db.add(q_exp)
            db.flush()
            print("  Created Expired Quotation: QTN-2026-EXPIRED (for testing validity extension)")

        db.commit()
        print("[Seed] SubscriptIQ demo dataset successfully seeded!")

    finally:
        db.close()


if __name__ == "__main__":
    seed_demo_data()
