from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from sqlalchemy import func

from backend.app.core.database import SessionLocal
from backend.app.core.money import to_decimal, round_money
from backend.app.shared.dto import PaymentDTO
from backend.app.shared.ports import PaymentPort
from backend.app.shared.registry import register_port
from backend.app.payments.models import Payment
from backend.app.invoices.models import Invoice

class ProductionPaymentPort(PaymentPort):
    def list_for_customer(self, customer_id: str) -> List[PaymentDTO]:
        db = SessionLocal()
        try:
            payments = db.query(Payment).filter(
                Payment.customer_id == customer_id
            ).order_by(Payment.payment_date.desc()).all()

            return [
                PaymentDTO(
                    id=p.id,
                    customer_id=p.customer_id,
                    method=p.method,
                    amount=to_decimal(p.amount),
                    payment_date=p.payment_date,
                    reference=p.reference,
                    notes=p.notes,
                    status=p.status
                )
                for p in payments
            ]
        finally:
            db.close()

    def outstanding_for_customer(self, customer_id: str) -> Decimal:
        db = SessionLocal()
        try:
            # Total unpaid balances on open invoices
            invoices = db.query(Invoice).filter(
                Invoice.customer_id == customer_id,
                Invoice.status.in_(["CONFIRMED", "PARTIALLY_PAID"])
            ).all()
            total_balance = sum((to_decimal(inv.balance) for inv in invoices), Decimal("0.00"))

            # Unallocated credits from payments
            payments = db.query(Payment).filter(
                Payment.customer_id == customer_id,
                Payment.status == "RECORDED"
            ).all()
            total_unallocated = sum((to_decimal(p.unallocated_amount) for p in payments), Decimal("0.00"))

            net_outstanding = round_money(total_balance - total_unallocated)
            return max(Decimal("0.00"), net_outstanding)
        finally:
            db.close()

def bootstrap():
    service = ProductionPaymentPort()
    register_port("payment", service)
