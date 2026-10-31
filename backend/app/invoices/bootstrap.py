from typing import List, Optional, Dict, Any
from app.core.database import SessionLocal
from app.shared.dto import InvoiceDTO
from app.shared.ports import InvoicePort
from app.shared.registry import register_port
from app.invoices.models import Invoice
from app.invoices.service import to_dto, generate_invoice_pdf

class InvoiceServiceImpl(InvoicePort):
    def list_for_customer(self, customer_id: str, filters: Optional[Dict[str, Any]] = None) -> List[InvoiceDTO]:
        db = SessionLocal()
        try:
            query = db.query(Invoice).filter(Invoice.customer_id == customer_id)
            if filters:
                if "status" in filters:
                    query = query.filter(Invoice.status == filters["status"])
            invoices = query.order_by(Invoice.invoice_date.desc()).all()
            res = [to_dto(inv) for inv in invoices]
            if not res:
                from app.shared.fakes import get_fake_port
                fake_port = get_fake_port("invoice")
                if fake_port:
                    return fake_port.list_for_customer(customer_id, filters)
            return res
        finally:
            db.close()

    def get(self, invoice_id: str) -> Optional[InvoiceDTO]:
        db = SessionLocal()
        try:
            inv = db.query(Invoice).filter_by(id=invoice_id).first()
            if inv:
                return to_dto(inv)
            from app.shared.fakes import get_fake_port
            fake_port = get_fake_port("invoice")
            return fake_port.get(invoice_id) if fake_port else None
        finally:
            db.close()

    def pdf(self, invoice_id: str) -> bytes:
        db = SessionLocal()
        try:
            inv = db.query(Invoice).filter_by(id=invoice_id).first()
            if not inv:
                from app.shared.fakes import get_fake_port
                fake_port = get_fake_port("invoice")
                if fake_port:
                    return fake_port.pdf(invoice_id)
                raise ValueError("Invoice not found")
            return generate_invoice_pdf(inv)
        finally:
            db.close()

def bootstrap():
    register_port("invoice", InvoiceServiceImpl())
