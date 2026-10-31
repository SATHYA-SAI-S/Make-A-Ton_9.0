from app.shared.registry import register_port
from app.taxes.service import TaxPreviewService

def bootstrap():
    service = TaxPreviewService()
    register_port("tax_preview", service)
